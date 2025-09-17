"""Authentication module handling login and token workflows."""

import base64, logging, uuid
from datetime import datetime, timedelta, timezone
from fastapi import FastAPI, HTTPException, status
from jose import jwt, JWTError, ExpiredSignatureError
from typing import Dict

from server.modules import BaseModule
from server.modules.env_module import EnvModule
from server.modules.db_module import DbModule
from server.modules.providers import AuthProviderBase
from server.modules.providers.auth.microsoft_provider import MicrosoftAuthProvider
from server.modules.providers.auth.google_provider import GoogleAuthProvider
from server.modules.providers.auth.discord_provider import DiscordAuthProvider
from server.modules.discord_bot_module import DiscordBotModule

DEFAULT_SESSION_TOKEN_EXPIRY = 15 # minutes
DEFAULT_ROTATION_TOKEN_EXPIRY = 90 # days


class RoleCache:
  def __init__(self, db: DbModule | None = None):
    self.db = db
    self.roles: dict[str, int] = {}
    self.role_names: list[str] = []
    self.role_registered: int = 0
    self._user_roles: dict[str, tuple[list[str], int]] = {}

  async def load_roles(self):
    logging.debug("[RoleCache] Loading roles from database")
    try:
      result = await self.db.run("db:system:roles:list:1", {})
    except Exception as e:
      logging.error("[RoleCache] Failed to load roles: %s", e)
      return
    rows = result.rows
    if not rows:
      logging.debug("[RoleCache] No roles returned")
      return
    self.roles.clear()
    for r in rows:
      self.roles[r["name"]] = int(r["mask"])
    self.role_registered = self.roles.get("ROLE_REGISTERED", 0)
    self.role_names = [n for n in self.roles.keys() if n != "ROLE_REGISTERED"]
    self._user_roles.clear()
    logging.debug("[RoleCache] Loaded roles: %s", self.roles)

  async def refresh_role_cache(self):
    logging.debug("[RoleCache] Refreshing role cache")
    await self.load_roles()

  async def upsert_role(self, name: str, mask: int, display: str | None):
    await self.db.run(
      "db:security:roles:upsert_role:1",
      {"name": name, "mask": mask, "display": display},
    )
    await self.refresh_role_cache()

  async def delete_role(self, name: str):
    await self.db.run(
      "db:security:roles:delete_role:1",
      {"name": name},
    )
    await self.refresh_role_cache()

  def mask_to_names(self, mask: int) -> list[str]:
    return [name for name, bit in self.roles.items() if mask & bit]

  def names_to_mask(self, names: list[str]) -> int:
    mask = 0
    for name in names:
      mask |= self.roles.get(name, 0)
    return mask

  def get_role_names(self, exclude_registered: bool = False) -> list[str]:
    if exclude_registered:
      return [n for n in self.role_names]
    return list(self.roles.keys())

  async def get_user_roles(self, guid: str, refresh: bool = False) -> tuple[list[str], int]:
    if not refresh and guid in self._user_roles:
      logging.debug("[RoleCache] Returning cached roles for %s", guid)
      return self._user_roles[guid]
    logging.debug("[RoleCache] Fetching roles for %s", guid)
    res = await self.db.run("db:users:profile:get_roles:1", {"guid": guid})
    mask = int(res.rows[0].get("element_roles", 0)) if res.rows else 0
    names = self.mask_to_names(mask)
    self._user_roles[guid] = (names, mask)
    logging.debug("[RoleCache] Roles for %s: %s (mask=%#018x)", guid, names, mask)
    return names, mask

  async def user_has_role(self, guid: str, required_mask: int) -> bool:
    if not required_mask:
      return True
    if not guid:
      return False
    _, mask = await self.get_user_roles(guid)
    return bool(mask & required_mask)

  async def refresh_user_roles(self, guid: str):
    logging.debug("[RoleCache] Refreshing user roles for %s", guid)
    await self.get_user_roles(guid, refresh=True)


class AuthModule(BaseModule):
  def __init__(self, app: FastAPI):
    super().__init__(app)
    self.providers: dict[str, AuthProviderBase] = {}
    self.jwt_secret: str | None = None
    self.jwt_algo_int: str = "HS256"
    self.jwks_cache_minutes: int = 60
    self.role_cache = RoleCache()
    self.discord: DiscordBotModule | None = None

  @property
  def roles(self) -> dict[str, int]:
    return self.role_cache.roles

  @property
  def role_names(self) -> list[str]:
    return self.role_cache.role_names

  @property
  def role_registered(self) -> int:
    return self.role_cache.role_registered

  @property
  def _user_roles(self) -> dict[str, tuple[list[str], int]]:
    return self.role_cache._user_roles

  async def startup(self):
    self.env: EnvModule = self.app.state.env
    await self.env.on_ready()
    self.db: DbModule = self.app.state.db
    await self.db.on_ready()
    self.discord = getattr(self.app.state, "discord_bot", None) or getattr(self.app.state, "discord", None)
    self.discord = getattr(self.app.state, "discord_bot", None)
    if self.discord:
      await self.discord.on_ready()
      register = getattr(self.discord, "register_auth_module", None)
      if register:
        register(self)
    self.role_cache.db = self.db
    self.jwt_secret = self.env.get("JWT_SECRET")
    self.jwks_cache_minutes = await self.db.get_jwks_cache_time()

    providers_cfg = await self.db.get_auth_providers()
    logging.debug(f"[AuthModule] Provider configuration: {providers_cfg}")
    try:
      if "microsoft" in providers_cfg:
        logging.debug("[AuthModule] Loading Microsoft provider")
        ms_api_id = await self.db.get_ms_api_id()
        logging.debug("[AuthModule] MsApiId=%s", ms_api_id)
        provider = await MicrosoftAuthProvider.create(api_id=ms_api_id, jwks_expiry=timedelta(minutes=self.jwks_cache_minutes))
        await provider.startup()
        self.providers["microsoft"] = provider
        logging.debug("[AuthModule] Microsoft provider ready")
      if "google" in providers_cfg:
        logging.debug("[AuthModule] Loading Google provider")
        google_client_id = await self.db.get_google_client_id()
        logging.debug("[AuthModule] GoogleClientId=%s", google_client_id)
        provider = await GoogleAuthProvider.create(api_id=google_client_id, jwks_expiry=timedelta(minutes=self.jwks_cache_minutes))
        await provider.startup()
        self.providers["google"] = provider
        logging.debug("[AuthModule] Google provider ready")
      if "discord" in providers_cfg:
        logging.debug("[AuthModule] Loading Discord provider")
        discord_client_id = await self.db.get_discord_client_id()
        logging.debug("[AuthModule] DiscordClientId=%s", discord_client_id)
        provider = DiscordAuthProvider()
        provider.audience = discord_client_id
        await provider.startup()
        self.providers["discord"] = provider
        logging.debug("[AuthModule] Discord provider ready")
      await self.role_cache.load_roles()
      logging.info("Auth module loaded")
      self.mark_ready()
    except Exception as e:
      logging.exception("[AuthModule] Failed to load providers: %s", e)

  async def shutdown(self):
    for provider in self.providers.values():
      await provider.shutdown()
    if self.discord and getattr(self.discord, "auth_module", None) is self:
      self.discord.auth_module = None
    logging.info("Auth module shutdown")


  async def handle_auth_login(self, provider: str, id_token: str | None, access_token: str | None):
    logging.debug("[AuthModule] handle_auth_login provider=%s", provider)
    strategy = self.providers.get(provider)
    if not strategy:
      logging.error("[AuthModule] Unsupported auth provider %s", provider)
      raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported auth provider")
    if not access_token or (strategy.requires_id_token and not id_token):
      logging.error("[AuthModule] Missing credentials for provider %s", provider)
      raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing credentials")
    payload = await strategy.verify_id_token(id_token, access_token)
    guid = strategy.extract_guid(payload)
    if not guid:
      logging.error("[AuthModule] Missing guid in token for provider %s", provider)
      raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload.")
    profile = await strategy.fetch_user_profile(access_token)
    logging.info(f"Processing login for: {profile['username']}, {profile['email']}")
    logging.debug("[AuthModule] Login payload guid=%s provider=%s", guid, provider)
    return guid, profile, payload

  def make_session_token(
    self,
    guid: str,
    rotation_token: str,
    session_guid: str,
    device_guid: str,
    roles: list[str],
    exp: datetime | None = None,
  ) -> tuple[str, datetime]:
    now = datetime.now(timezone.utc)
    exp = exp or now + timedelta(minutes=DEFAULT_SESSION_TOKEN_EXPIRY)
    token_data = {
      "sub": guid,
      "roles": roles,
      "iat": int(now.timestamp()),
      "exp": int(exp.timestamp()),
      "jti": uuid.uuid4().hex,
      "sid": session_guid,
      "did": device_guid,
    }
    logging.debug("[AuthModule] Creating session token for %s roles=%s", guid, roles)
    derived_secret = f"{self.jwt_secret}:{rotation_token}:{guid}:{session_guid}:{device_guid}"
    token = jwt.encode(token_data, derived_secret, algorithm=self.jwt_algo_int)
    return token, exp

  def make_rotation_token(self, guid: str) -> tuple[str, datetime]:
    exp = datetime.now(timezone.utc) + timedelta(days=DEFAULT_ROTATION_TOKEN_EXPIRY)
    parts = [uuid.uuid4().hex for _ in range(4)]
    now = datetime.now(timezone.utc)
    raw = f"{guid}:{now}:{':'.join(parts)}"
    encoded = base64.urlsafe_b64encode(raw.encode("utf-8")).decode("utf-8").rstrip("=")
    logging.debug("[AuthModule] Generated rotation token for %s", guid)
    return encoded, exp

  async def decode_session_token(self, token: str) -> Dict:
    logging.debug("[AuthModule] Decoding session token")
    try:
      claims = jwt.get_unverified_claims(token)
    except JWTError:
      logging.error("[AuthModule] Failed to decode session token")
      raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token", headers={"WWW-Authenticate": "Bearer"})

    guid = claims.get("sub")
    session_guid = claims.get("sid")
    device_guid = claims.get("did")
    if not guid or not session_guid or not device_guid:
      raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Subject not found", headers={"WWW-Authenticate": "Bearer"})

    res = await self.db.run("db:users:session:get_rotkey:1", {"guid": guid})
    rotkey = res.rows[0].get("rotkey") if res.rows else None
    derived_secret = f"{self.jwt_secret}:{rotkey}:{guid}:{session_guid}:{device_guid}" if rotkey else None
    try:
      if not derived_secret:
        raise JWTError("missing session key")
      payload = jwt.decode(token, derived_secret, algorithms=[self.jwt_algo_int])
    except ExpiredSignatureError:
      logging.warning("[AuthModule] Session token expired for %s", guid)
      raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired", headers={"WWW-Authenticate": "Bearer"})
    except jwt.JWTClaimsError:
      logging.error("[AuthModule] JWT claims error for guid %s", guid)
      raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token claims", headers={"WWW-Authenticate": "Bearer"})
    except JWTError as e:
      if str(e) == "missing session key":
        logging.error("[AuthModule] Session key missing for guid %s", guid)
        detail = "Invalid session key"
      else:
        logging.error("[AuthModule] JWT decode failed for guid %s", guid)
        detail = "Invalid token"
      raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=detail, headers={"WWW-Authenticate": "Bearer"})

    if not rotkey:
      logging.error("[AuthModule] Rotation key missing for %s", guid)
      raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid rotation token", headers={"WWW-Authenticate": "Bearer"})

    return payload

  def decode_rotation_token(self, token: str) -> Dict:
    logging.debug("[AuthModule] Decoding rotation token")
    try:
      padded_token = token + '=' * (-len(token) % 4)  # restore stripped padding
      raw = base64.urlsafe_b64decode(padded_token.encode("utf-8")).decode("utf-8")
      parts = raw.split(":")
      if len(parts) < 6:
        raise ValueError("Malformed token")
      guid = parts[0]
      timestamp = ":".join(parts[1:-4])
      token_time = datetime.fromisoformat(timestamp)
      if token_time.tzinfo is None:
        token_time = token_time.replace(tzinfo=timezone.utc)
      if token_time + timedelta(days=DEFAULT_ROTATION_TOKEN_EXPIRY) < datetime.now(timezone.utc):
        logging.error("[AuthModule] Rotation token expired for %s", guid)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Rotation token expired")
      return {"guid": guid}
    except Exception:
      logging.error("[AuthModule] Failed to decode rotation token")
      raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid rotation token")

  async def load_roles(self):
    await self.role_cache.load_roles()

  async def refresh_role_cache(self):
    await self.role_cache.refresh_role_cache()

  async def upsert_role(self, name: str, mask: int, display: str | None):
    await self.role_cache.upsert_role(name, mask, display)

  async def delete_role(self, name: str):
    await self.role_cache.delete_role(name)

  def mask_to_names(self, mask: int) -> list[str]:
    return self.role_cache.mask_to_names(mask)

  def names_to_mask(self, names: list[str]) -> int:
    return self.role_cache.names_to_mask(names)

  def get_role_names(self, exclude_registered: bool = False) -> list[str]:
    return self.role_cache.get_role_names(exclude_registered)

  async def get_discord_user_security(self, discord_id: str) -> tuple[str, list[str], int]:
    res = await self.db.run("db:auth:discord:get_security:1", {"discord_id": discord_id})
    if not res.rows:
      return "", [], 0
    row = res.rows[0]
    guid = row.get("user_guid")
    mask = int(row.get("user_roles", 0) or 0)
    names = self.role_cache.mask_to_names(mask)
    return guid, names, mask

  async def get_user_roles(self, guid: str, refresh: bool = False) -> tuple[list[str], int]:
    return await self.role_cache.get_user_roles(guid, refresh)

  async def user_has_role(self, guid: str, required_mask: int) -> bool:
    return await self.role_cache.user_has_role(guid, required_mask)

  async def refresh_user_roles(self, guid: str):
    await self.role_cache.refresh_user_roles(guid)

