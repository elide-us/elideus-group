"""Authentication module handling login and token workflows."""

import base64, logging, uuid
from collections.abc import Mapping
from datetime import datetime, timedelta, timezone
from fastapi import FastAPI, HTTPException, status
from jose import jwt, JWTError, ExpiredSignatureError
from typing import Any, Dict

from server.modules import BaseModule
from server.modules.env_module import EnvModule
from server.modules.db_module import DbModule
from server.modules.role_module import RoleModule
from server.modules.providers import AuthProviderBase
from server.modules.providers.auth.microsoft_provider import MicrosoftAuthProvider
from server.modules.providers.auth.google_provider import GoogleAuthProvider
from server.modules.providers.auth.discord_provider import DiscordAuthProvider
from server.modules.discord_bot_module import DiscordBotModule
from queryregistry.handler import dispatch_query_request
from queryregistry.identity.users import account_exists_request
from queryregistry.identity.sessions import get_rotkey_request
from queryregistry.identity.sessions.models import RotkeyLookupParams
from queryregistry.system.config import get_config_request
from queryregistry.system.config.models import ConfigKeyParams

DEFAULT_SESSION_TOKEN_EXPIRY = 15 # minutes
DEFAULT_ROTATION_TOKEN_EXPIRY = 90 # days


class AuthModule(BaseModule):
  def __init__(self, app: FastAPI):
    super().__init__(app)
    self.providers: dict[str, AuthProviderBase] = {}
    self.jwt_secret: str | None = None
    self.jwt_algo_int: str = "HS256"
    self.jwks_cache_minutes: int = 60
    self.role: RoleModule | None = None
    self.domain_role_map: dict[str, int] = {}
    self.discord: DiscordBotModule | None = None

  @property
  def roles(self) -> dict[str, int]:
    assert self.role
    return self.role.roles

  @property
  def role_names(self) -> list[str]:
    assert self.role
    return self.role.role_names

  @property
  def role_registered(self) -> int:
    assert self.role
    return self.role.role_registered


  async def _read_config_value(self, key: str) -> str | None:
    """Read a single system_config value by key."""
    res = await self.db.run(get_config_request(ConfigKeyParams(key=key)))
    return res.rows[0]["element_value"] if res.rows else None

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
    self.role = self.app.state.role
    await self.role.on_ready()
    self.domain_role_map = self.role.domain_role_map
    self.jwt_secret = self.env.get("JWT_SECRET")
    cache_raw = await self._read_config_value("JwksCacheTime")
    if cache_raw is None:
      raise ValueError("Missing config value for key: JwksCacheTime")
    self.jwks_cache_minutes = int(cache_raw)

    providers_raw = await self._read_config_value("AuthProviders")
    if providers_raw is None:
      raise ValueError("Missing config value for key: AuthProviders")
    providers_cfg = [provider.strip() for provider in providers_raw.split(",") if provider.strip()]
    logging.debug(f"[AuthModule] Provider configuration: {providers_cfg}")
    try:
      if "microsoft" in providers_cfg:
        logging.debug("[AuthModule] Loading Microsoft provider")
        ms_api_id = await self._read_config_value("MsApiId")
        if not ms_api_id:
          raise ValueError("Missing config value for key: MsApiId")
        logging.debug("[AuthModule] MsApiId=%s", ms_api_id)
        provider = await MicrosoftAuthProvider.create(api_id=ms_api_id, jwks_expiry=timedelta(minutes=self.jwks_cache_minutes))
        await provider.startup()
        self.providers["microsoft"] = provider
        logging.debug("[AuthModule] Microsoft provider ready")
      if "google" in providers_cfg:
        logging.debug("[AuthModule] Loading Google provider")
        google_client_id = await self._read_config_value("GoogleClientId")
        if not google_client_id:
          raise ValueError("Missing config value for key: GoogleClientId")
        google_secret = self.env.get("GOOGLE_AUTH_SECRET")
        if not google_secret:
          raise ValueError("Missing env value for key: GOOGLE_AUTH_SECRET")
        logging.debug("[AuthModule] GoogleAuthSecret loaded: %s", bool(google_secret))
        logging.debug("[AuthModule] GoogleClientId=%s", google_client_id)
        provider = await GoogleAuthProvider.create(api_id=google_client_id, jwks_expiry=timedelta(minutes=self.jwks_cache_minutes))
        await provider.startup()
        self.providers["google"] = provider
        logging.debug("[AuthModule] Google provider ready")
      if "discord" in providers_cfg:
        logging.debug("[AuthModule] Loading Discord provider")
        discord_client_id = await self._read_config_value("DiscordClientId")
        if not discord_client_id:
          raise ValueError("Missing config value for key: DiscordClientId")
        logging.debug("[AuthModule] DiscordClientId=%s", discord_client_id)
        provider = DiscordAuthProvider()
        provider.audience = discord_client_id
        await provider.startup()
        self.providers["discord"] = provider
        logging.debug("[AuthModule] Discord provider ready")
      logging.debug("Auth module loaded")
      self.mark_ready()
    except Exception as e:
      logging.exception("[AuthModule] Failed to load providers: %s", e)

  async def shutdown(self):
    for provider in self.providers.values():
      await provider.shutdown()
    if self.discord and getattr(self.discord, "auth_module", None) is self:
      self.discord.auth_module = None
    logging.info("Auth module shutdown")

  async def user_exists(self, user_guid: str) -> bool:
    request = account_exists_request({"user_guid": user_guid})
    provider_name = self.db.provider or "mssql"
    try:
      res = await dispatch_query_request(request, provider=provider_name)
    except KeyError:
      logging.getLogger("server" + ".registry").warning(
        "Query registry handler missing for user lookup",
        extra={"db_op": request.op, "db_provider": provider_name},
      )
      return await self._fallback_user_exists(user_guid=user_guid)
    payload = res.payload if isinstance(res.payload, dict) else {}
    return bool(payload.get("exists_flag"))

  async def _fallback_user_exists(self, *, user_guid: str) -> bool:
    provider_name = self.db.provider or "mssql"
    if provider_name != "mssql":
      logging.getLogger("server" + ".registry").error(
        "No registry handler for %s and no fallback available", provider_name
      )
      return False
    try:
      from queryregistry.identity.users.mssql import account_exists
    except ModuleNotFoundError:
      logging.getLogger("server" + ".registry").error(
        "MSSQL account exists handler unavailable"
      )
      return False
    response = await account_exists({"user_guid": user_guid})
    payload = response.payload if isinstance(response.payload, dict) else {}
    return bool(payload.get("exists_flag"))

  @staticmethod
  def _normalize_query_payload(payload: Any | None) -> list[dict[str, Any]]:
    if payload is None:
      return []
    if isinstance(payload, list):
      return [dict(item) for item in payload]
    if isinstance(payload, Mapping):
      return [dict(payload)]
    return [dict(payload)]


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

    res = await dispatch_query_request(
      get_rotkey_request(RotkeyLookupParams(guid=guid, device_guid=device_guid)),
      provider=self.db.provider or "mssql",
    )
    rows = self._normalize_query_payload(res.payload)
    rotkey = rows[0].get("device_rotkey") if rows else None
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
      return {"guid": guid, "issued_at": token_time}
    except Exception:
      logging.error("[AuthModule] Failed to decode rotation token")
      raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid rotation token")


  async def refresh_role_cache(self):
    assert self.role
    await self.role.refresh_role_cache()

  async def check_domain_access(self, domain: str, user_guid: str) -> None:
    """Check if a user has the required role for an RPC domain."""
    domain_role_map = self.role.domain_role_map if self.role else self.domain_role_map
    required_mask = domain_role_map.get(domain)
    if required_mask is None:
      raise HTTPException(status_code=403, detail="Domain access not configured")
    if not await self.user_has_role(user_guid, required_mask):
      raise HTTPException(status_code=403, detail="Forbidden")

  async def upsert_role(self, name: str, mask: int, display: str | None):
    assert self.role
    await self.role.upsert_role(name, mask, display)

  async def delete_role(self, name: str):
    assert self.role
    await self.role.delete_role(name)

  def mask_to_names(self, mask: int) -> list[str]:
    assert self.role
    return self.role.mask_to_names(mask)

  def names_to_mask(self, names: list[str]) -> int:
    assert self.role
    return self.role.names_to_mask(names)

  def get_role_names(self, exclude_registered: bool = False) -> list[str]:
    assert self.role
    return self.role.get_role_names(exclude_registered)

  async def get_discord_user_security(self, discord_id: str) -> tuple[str, list[str], int]:
    from queryregistry.identity.users import read_by_discord_request

    res = await self.db.run(read_by_discord_request(discord_id))
    rows = res.rows
    if not rows:
      return "", [], 0
    row = rows[0]
    guid = row.get("user_guid")
    if not guid:
      return "", [], 0
    mask = int(row.get("user_roles", 0) or 0)
    assert self.role
    names = self.role.mask_to_names(mask)
    return guid, names, mask

  async def get_user_roles(self, guid: str, refresh: bool = False) -> tuple[list[str], int]:
    assert self.role
    return await self.role.get_user_roles(guid, refresh)

  async def user_has_role(self, guid: str, required_mask: int) -> bool:
    assert self.role
    return await self.role.user_has_role(guid, required_mask)

  async def refresh_user_roles(self, guid: str):
    assert self.role
    await self.role.refresh_user_roles(guid)
