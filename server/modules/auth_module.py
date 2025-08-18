import base64, logging, uuid
from datetime import datetime, timedelta, timezone
from fastapi import FastAPI, HTTPException, status
from jose import jwt, JWTError
from typing import Dict

from server.modules import BaseModule
from server.modules.env_module import EnvModule
from server.modules.db_module import DbModule
from server.modules.providers import AuthProvider
from server.modules.providers.microsoft import MicrosoftAuthProvider

DEFAULT_SESSION_TOKEN_EXPIRY = 15 # minutes
DEFAULT_ROTATION_TOKEN_EXPIRY = 90 # days

class AuthModule(BaseModule):
  def __init__(self, app: FastAPI):
    super().__init__(app)
    self.providers: dict[str, AuthProvider] = {}
    self.jwt_secret: str | None = None
    self.jwt_algo_int: str = "HS256"
    self.jwks_cache_minutes: int = 60

  async def startup(self):
    self.env: EnvModule = self.app.state.env
    await self.env.on_ready()
    self.db: DbModule = self.app.state.db
    await self.db.on_ready()
    self.jwt_secret = self.env.get("JWT_SECRET")
    self.jwks_cache_minutes = int(self.env.get("JWKS_CACHE_MINUTES"))

    providers_cfg = [p.strip() for p in self.env.get("AUTH_PROVIDERS").split(",") if p.strip()]
    try:
      if "microsoft" in providers_cfg:
        res = await self.db.run("db:system:config:get_config:1", {"key": "MsApiId"})
        if not res.rows:
          raise ValueError("Missing config value for key: MsApiId")
        ms_api_id = res.rows[0]["value"]
        provider = await MicrosoftAuthProvider.create(api_id=ms_api_id, jwks_expiry=timedelta(minutes=self.jwks_cache_minutes))
        await provider._get_jwks()
        self.providers["microsoft"] = provider
      logging.info("Auth module loaded")
      self.mark_ready()
    except Exception as e:
      logging.error(f"[AuthModule] Failed to load providers: {e}")

  async def shutdown(self):
    logging.info("Auth module shutdown")


  async def handle_auth_login(self, provider: str, id_token: str, access_token: str):
    strategy = self.providers.get(provider)
    if not strategy:
      raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported auth provider")
    payload = await strategy.verify_id_token(id_token)
    guid = strategy.extract_guid(payload)
    if not guid:
      raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload.")
    profile = await strategy.fetch_user_profile(access_token)
    logging.info(f"Processing login for: {profile['username']}, {profile['email']}")
    return guid, profile, payload

  def make_session_token(self, guid: str, rotation_token: str, roles: list[str], provider: str) -> tuple[str, datetime]:
    now = datetime.now(timezone.utc)
    exp = now + timedelta(minutes=DEFAULT_SESSION_TOKEN_EXPIRY)
    token_data = {
      "sub": guid,
      "roles": roles,
      "iat": int(now.timestamp()),
      "exp": int(exp.timestamp()),
      "jti": uuid.uuid4().hex,
      "session": rotation_token,
      "provider": provider,
    }
    derived_secret = f"{self.jwt_secret}:{rotation_token}"
    token = jwt.encode(token_data, derived_secret, algorithm=self.jwt_algo_int)
    return token, exp

  def make_rotation_token(self, guid: str) -> tuple[str, datetime]:
    exp = datetime.now(timezone.utc) + timedelta(days=DEFAULT_ROTATION_TOKEN_EXPIRY)
    parts = [uuid.uuid4().hex for _ in range(4)]
    now = datetime.now(timezone.utc)
    raw = f"{guid}:{now}:{':'.join(parts)}"
    encoded = base64.urlsafe_b64encode(raw.encode("utf-8")).decode("utf-8").rstrip("=")
    return encoded, exp

  async def decode_session_token(self, token: str) -> Dict:
    try:
      claims = jwt.get_unverified_claims(token)
    except JWTError:
      raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token", headers={"WWW-Authenticate": "Bearer"})

    guid = claims.get("sub")
    if not guid:
      raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Subject not found", headers={"WWW-Authenticate": "Bearer"})

    res = await self.db.run("db:users:session:get_rotkey:1", {"guid": guid})
    rotkey = res.rows[0].get("rotkey") if res.rows else None
    if not rotkey:
      raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid rotation token", headers={"WWW-Authenticate": "Bearer"})

    derived_secret = f"{self.jwt_secret}:{rotkey}"
    try:
      payload = jwt.decode(token, derived_secret, algorithms=[self.jwt_algo_int])
    except JWTError:
      raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token", headers={"WWW-Authenticate": "Bearer"})

    exp = payload.get("exp")
    if not exp or datetime.fromtimestamp(exp, tz=timezone.utc) < datetime.now(timezone.utc):
      raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired", headers={"WWW-Authenticate": "Bearer"})

    return payload

  def decode_rotation_token(self, token: str) -> Dict:
    try:
      padded_token = token + '=' * (-len(token) % 4)  # restore stripped padding
      raw = base64.urlsafe_b64decode(padded_token.encode("utf-8")).decode("utf-8")
      parts = raw.split(":")
      if len(parts) < 6:
        raise ValueError("Malformed token")
      guid, timestamp = parts[0], parts[1]
      token_time = datetime.fromisoformat(timestamp)
      if token_time + timedelta(days=DEFAULT_ROTATION_TOKEN_EXPIRY) < datetime.now(timezone.utc):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Rotation token expired")
      return {"guid": guid}
    except Exception:
      raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid rotation token")

