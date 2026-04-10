"""MCP OAuth gateway module."""

from __future__ import annotations

import base64
import hashlib
import logging
import secrets
import time
from collections import deque
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from fastapi import FastAPI, HTTPException
from jose import jwt

from queryregistry.identity.mcp_agents import (
  consume_auth_code_request,
  create_agent_token_request,
  create_auth_code_request,
  get_agent_by_client_id_request,
  get_agent_token_request,
  link_agent_user_request,
  list_user_agents_request,
  register_agent_request,
  revoke_agent_request,
  revoke_agent_token_request,
)
from queryregistry.identity.mcp_agents.models import (
  ClientIdParams,
  CreateAgentTokenParams,
  CreateAuthCodeParams,
  ConsumeAuthCodeParams,
  LinkAgentUserParams,
  RefreshTokenParams,
  RegisterAgentParams,
  RevokeTokenParams,
  UserGuidParams,
)
from queryregistry.models import DBRequest
from queryregistry.system.config import get_config_request, upsert_config_request
from queryregistry.system.config.models import ConfigKeyParams, UpsertConfigParams

from . import BaseModule
from .auth_module import AuthModule
from .db_module import DbModule
from .discord_bot_module import DiscordBotModule
from .oauth_module import OauthModule


def _coerce_datetime(value) -> datetime | None:
  if value is None:
    return None
  if isinstance(value, datetime):
    dt = value
  else:
    text = str(value).replace("Z", "+00:00")
    dt = datetime.fromisoformat(text)
  if dt.tzinfo is None:
    return dt.replace(tzinfo=timezone.utc)
  return dt


class SlidingWindowRateLimiter:
  def __init__(self, window_seconds: float):
    self._window = window_seconds
    self._counters: dict[str, deque[float]] = {}
    self._global: deque[float] = deque()

  def check(self, key: str, per_key_limit: int, global_limit: int) -> bool:
    """Return True if request is allowed, False if rate limited."""
    now = time.monotonic()
    cutoff = now - self._window
    while self._global and self._global[0] < cutoff:
      self._global.popleft()
    if len(self._global) >= global_limit:
      return False
    counter = self._counters.get(key)
    if counter is None:
      counter = deque()
      self._counters[key] = counter
    while counter and counter[0] < cutoff:
      counter.popleft()
    if len(counter) >= per_key_limit:
      return False
    counter.append(now)
    self._global.append(now)
    return True

  @property
  def global_count(self) -> int:
    return len(self._global)


class McpGatewayModule(BaseModule):
  ROLE_MCP_ACCESS_MASK = 32

  def __init__(self, app: FastAPI):
    super().__init__(app)
    self.dcr_enabled: bool = False
    self.hostname: str = ""
    self.register_ip_limit: int = 5
    self.register_global_limit: int = 50
    self.token_ip_limit: int = 60
    self.token_global_limit: int = 500
    self.register_rate_limiter = SlidingWindowRateLimiter(window_seconds=60.0)
    self.token_rate_limiter = SlidingWindowRateLimiter(window_seconds=60.0)

  async def startup(self):
    self.db: DbModule = self.app.state.db
    await self.db.on_ready()
    self.auth: AuthModule = self.app.state.auth
    await self.auth.on_ready()
    self.oauth: OauthModule = self.app.state.oauth
    await self.oauth.on_ready()
    self.discord: DiscordBotModule | None = getattr(self.app.state, "discord_bot", None)
    if self.discord:
      await self.discord.on_ready()
    await self.refresh_runtime_config()
    self.mark_ready()

  async def shutdown(self):
    pass

  async def _audit(self, level: str, message: str):
    log_line = f"[McpGatewayModule] [{level}] {message}"
    getattr(logging, level.lower(), logging.info)(log_line)
    if self.discord:
      try:
        await self.discord.send_sys_message(log_line)
      except Exception:
        logging.exception("[McpGatewayModule] Failed to send Discord audit event")

  async def refresh_runtime_config(self):
    self.dcr_enabled = await self.is_dcr_enabled(refresh=True)
    self.hostname = await self._get_config_value("Hostname", fallback="")
    self.register_ip_limit = await self._get_config_int("MCP_RATE_LIMIT_REGISTER_IP", fallback=5)
    self.register_global_limit = await self._get_config_int(
      "MCP_RATE_LIMIT_REGISTER_GLOBAL", fallback=50
    )
    self.token_ip_limit = await self._get_config_int("MCP_RATE_LIMIT_TOKEN_IP", fallback=60)
    self.token_global_limit = await self._get_config_int("MCP_RATE_LIMIT_TOKEN_GLOBAL", fallback=500)

  async def _get_config_value(self, key: str, *, fallback: str = "") -> str:
    res = await self.db.run(get_config_request(ConfigKeyParams(key=key)))
    if not res.rows:
      return fallback
    value = res.rows[0].get("element_value")
    return str(value) if value is not None else fallback

  async def _get_config_int(self, key: str, *, fallback: int) -> int:
    value = await self._get_config_value(key, fallback=str(fallback))
    try:
      return int(value)
    except (TypeError, ValueError):
      logging.warning("[McpGatewayModule] Invalid integer config %s=%s", key, value)
      return fallback

  async def is_dcr_enabled(self, refresh: bool = False) -> bool:
    if not refresh:
      return self.dcr_enabled
    value = await self._get_config_value("MCP_DCR_ENABLED", fallback="false")
    self.dcr_enabled = value.lower() in ("1", "true", "yes", "on")
    return self.dcr_enabled

  async def _set_dcr_enabled(self, enabled: bool):
    value = "true" if enabled else "false"
    await self.db.run(upsert_config_request(UpsertConfigParams(key="MCP_DCR_ENABLED", value=value)))
    self.dcr_enabled = enabled

  async def check_register_rate(self, ip: str) -> bool:
    allowed = self.register_rate_limiter.check(ip, self.register_ip_limit, self.register_global_limit)
    if not allowed:
      await self._audit("warning", f"Registration rate limit hit for ip={ip}")
      if self.register_rate_limiter.global_count >= self.register_global_limit:
        await self._set_dcr_enabled(False)
        await self._audit("critical", "Registration global limit reached. MCP_DCR_ENABLED set to false")
      return False
    if self.register_rate_limiter.global_count >= int(self.register_global_limit * 0.8):
      await self._audit(
        "warning",
        f"Registration global counter nearing limit {self.register_rate_limiter.global_count}/{self.register_global_limit}",
      )
    return True

  async def check_token_rate(self, ip: str) -> bool:
    allowed = self.token_rate_limiter.check(ip, self.token_ip_limit, self.token_global_limit)
    if not allowed:
      await self._audit("warning", f"Token rate limit hit for ip={ip}")
      return False
    return True

  async def register_client(
    self,
    client_name,
    redirect_uris,
    grant_types,
    response_types,
    scopes,
    ip_address,
    user_agent,
  ) -> dict:
    if not await self.is_dcr_enabled(refresh=False):
      await self._audit("warning", "DCR registration blocked by kill switch")
      raise HTTPException(status_code=503, detail="MCP DCR is disabled")
    if not await self.check_register_rate(ip_address or "unknown"):
      raise HTTPException(status_code=429, detail="Rate limit exceeded")
    params = RegisterAgentParams(
      client_name=client_name,
      redirect_uris=redirect_uris,
      grant_types=grant_types,
      response_types=response_types,
      scopes=scopes,
      ip_address=ip_address,
      user_agent=user_agent,
    )
    response = await self.db.run(register_agent_request(params))
    row = response.rows[0] if response.rows else None
    if not row:
      await self._audit("error", f"Registration failed for client_name={client_name}")
      raise HTTPException(status_code=500, detail="Client registration failed")
    await self._audit("info", f"Registered MCP client client_id={row.get('element_client_id')}")
    return row

  async def get_client(self, client_id: str) -> dict | None:
    response = await self.db.run(get_agent_by_client_id_request(ClientIdParams(client_id=client_id)))
    return response.rows[0] if response.rows else None

  async def link_client_to_user(self, client_id: str, users_guid: str) -> None:
    await self.db.run(
      link_agent_user_request(
        LinkAgentUserParams(client_id=client_id, users_guid=users_guid),
      ),
    )

  async def create_authorization_code(
    self,
    agents_recid,
    users_guid: str,
    code_challenge,
    code_method,
    redirect_uri,
    scopes,
  ) -> str:
    code = secrets.token_urlsafe(32)
    expires_on = datetime.now(timezone.utc) + timedelta(seconds=60)
    await self.db.run(
      create_auth_code_request(
        CreateAuthCodeParams(
          agents_recid=agents_recid,
          users_guid=users_guid,
          code=code,
          code_challenge=code_challenge,
          code_method=code_method,
          redirect_uri=redirect_uri,
          scopes=scopes,
          expires_on=expires_on,
        ),
      ),
    )
    await self._audit("info", f"Authorization code issued for agents_recid={agents_recid}")
    return code

  async def exchange_authorization_code(self, code, code_verifier, client_id) -> dict:
    consumed = await self.db.run(consume_auth_code_request(ConsumeAuthCodeParams(code=code)))
    code_row = consumed.rows[0] if consumed.rows else None
    if not code_row:
      raise HTTPException(status_code=400, detail="Invalid or expired authorization code")
    if (code_row.get("element_code_method") or "S256") != "S256":
      raise HTTPException(status_code=400, detail="Unsupported code challenge method")
    expected = code_row.get("element_code_challenge")
    digest = hashlib.sha256(str(code_verifier).encode("utf-8")).digest()
    verifier_challenge = base64.urlsafe_b64encode(digest).decode("utf-8").rstrip("=")
    if verifier_challenge != expected:
      raise HTTPException(status_code=400, detail="PKCE verification failed")

    client = await self.get_client(client_id)
    if not client or int(client.get("recid") or 0) != int(code_row.get("agents_recid") or 0):
      raise HTTPException(status_code=400, detail="Client does not match authorization code")
    if not client.get("element_is_active"):
      raise HTTPException(status_code=401, detail="Client revoked")

    users_guid = code_row.get("users_guid")
    if users_guid is None:
      raise HTTPException(status_code=400, detail="Authorization code is not linked to a user")

    await self.db.run(
      revoke_agent_token_request(RevokeTokenParams(agents_recid=int(code_row["agents_recid"]))),
    )

    user_guid, _ = await self.resolve_agent_credits(int(code_row["agents_recid"]))
    now = datetime.now(timezone.utc)
    access_exp = now + timedelta(minutes=5)
    refresh_exp = now + timedelta(days=7)
    claims = {
      "sub": user_guid,
      "client_id": str(client.get("element_client_id")),
      "scopes": str(code_row.get("element_scopes") or ""),
      "iss": self.hostname,
      "iat": int(now.timestamp()),
      "exp": int(access_exp.timestamp()),
      "jti": uuid4().hex,
      "type": "mcp_access",
    }
    if not self.auth.jwt_secret:
      raise HTTPException(status_code=500, detail="JWT secret is not configured")
    access_token = jwt.encode(
      claims,
      self.auth.jwt_secret,
      algorithm=getattr(self.auth, "jwt_algo_int", "HS256"),
    )
    refresh_token = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode("utf-8").rstrip("=")

    await self.db.run(
      create_agent_token_request(
        CreateAgentTokenParams(
          agents_recid=int(code_row["agents_recid"]),
          access_token=access_token,
          refresh_token=refresh_token,
          access_exp=access_exp,
          refresh_exp=refresh_exp,
          scopes=str(code_row.get("element_scopes") or ""),
        ),
      ),
    )
    await self._audit("info", f"Access token issued for agents_recid={code_row['agents_recid']}")
    return {
      "access_token": access_token,
      "refresh_token": refresh_token,
      "token_type": "Bearer",
      "expires_in": 300,
      "scope": str(code_row.get("element_scopes") or ""),
    }

  async def refresh_access_token(self, refresh_token: str) -> dict:
    token_response = await self.db.run(
      get_agent_token_request(RefreshTokenParams(refresh_token=refresh_token)),
    )
    row = token_response.rows[0] if token_response.rows else None
    if not row:
      raise HTTPException(status_code=401, detail="Invalid refresh token")
    if row.get("element_revoked_at"):
      raise HTTPException(status_code=401, detail="Refresh token revoked")
    refresh_exp = _coerce_datetime(row.get("element_refresh_exp"))
    if refresh_exp is not None and refresh_exp < datetime.now(timezone.utc):
      raise HTTPException(status_code=401, detail="Refresh token expired")
    if not row.get("element_is_active"):
      raise HTTPException(status_code=401, detail="Client revoked")

    user_guid = row.get("user_guid")
    if not user_guid:
      raise HTTPException(status_code=401, detail="Refresh token is not linked to a user")

    now = datetime.now(timezone.utc)
    access_exp = now + timedelta(minutes=5)
    claims = {
      "sub": str(user_guid),
      "client_id": str(row.get("element_client_id")),
      "scopes": str(row.get("element_scopes") or ""),
      "iss": self.hostname,
      "iat": int(now.timestamp()),
      "exp": int(access_exp.timestamp()),
      "jti": uuid4().hex,
      "type": "mcp_access",
    }
    if not self.auth.jwt_secret:
      raise HTTPException(status_code=500, detail="JWT secret is not configured")
    new_access_token = jwt.encode(
      claims,
      self.auth.jwt_secret,
      algorithm=getattr(self.auth, "jwt_algo_int", "HS256"),
    )
    await self.db.run(
      create_agent_token_request(
        CreateAgentTokenParams(
          agents_recid=int(row["agents_recid"]),
          access_token=new_access_token,
          refresh_token=refresh_token,
          access_exp=access_exp,
          refresh_exp=refresh_exp,
          scopes=str(row.get("element_scopes") or ""),
        ),
      ),
    )
    await self._audit("info", f"Refreshed access token for agents_recid={row['agents_recid']}")
    return {
      "access_token": new_access_token,
      "refresh_token": refresh_token,
      "token_type": "Bearer",
      "expires_in": 300,
      "scope": str(row.get("element_scopes") or ""),
    }

  async def validate_access_token(self, token: str) -> dict:
    try:
      claims = jwt.decode(
        token,
        self.auth.jwt_secret,
        algorithms=[getattr(self.auth, "jwt_algo_int", "HS256")],
      )
    except Exception as exc:
      raise HTTPException(status_code=401, detail="Invalid access token") from exc
    if claims.get("type") != "mcp_access":
      raise HTTPException(status_code=401, detail="Invalid token type")
    exp = claims.get("exp")
    if exp and datetime.fromtimestamp(int(exp), tz=timezone.utc) < datetime.now(timezone.utc):
      raise HTTPException(status_code=401, detail="Token expired")
    return claims

  async def resolve_agent_credits(self, agents_recid: int) -> tuple[str, int]:
    res = await self.db.run(
      DBRequest(op="db:identity:mcp_agents:get_by_recid:1", payload={"agents_recid": agents_recid}),
    )
    agent = res.rows[0] if res.rows else None
    if not agent or not agent.get("user_guid"):
      raise HTTPException(status_code=404, detail="Agent is not linked to a user")
    user_guid = str(agent["user_guid"])
    return user_guid, 0

  async def check_user_mcp_role(self, user_guid: str) -> bool:
    return await self.auth.user_has_role(user_guid, self.ROLE_MCP_ACCESS_MASK)

  async def list_user_clients(self, users_guid: str) -> list[dict]:
    response = await self.db.run(list_user_agents_request(UserGuidParams(users_guid=users_guid)))
    return response.rows

  async def revoke_client(self, client_id: str):
    await self.db.run(revoke_agent_request(ClientIdParams(client_id=client_id)))
