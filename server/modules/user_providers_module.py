from __future__ import annotations

import uuid

from fastapi import FastAPI, HTTPException

from server.modules import BaseModule
from server.modules.auth_module import AuthModule
from server.modules.db_module import DbModule
from server.modules.env_module import EnvModule
from server.modules.oauth_module import OauthModule
from server.registry.system.config import get_config_request
from server.registry.users.content.profile import (
  get_profile_request,
  update_if_unedited_request,
)
from server.registry.users.security.identities import (
  create_from_provider_request,
  get_by_provider_identifier_request,
  get_user_by_email_request,
  link_provider_request,
  set_provider_request,
  unlink_last_provider_request,
  unlink_provider_request,
)
from server.registry.users.security.sessions import revoke_provider_tokens_request


_CLIENT_ID_ERRORS = {
  "google": "Google OAuth client_id not configured",
  "discord": "Discord OAuth client_id not configured",
  "microsoft": "Microsoft OAuth client_id not configured",
}

_CLIENT_SECRET_ENV = {
  "google": ("GOOGLE_AUTH_SECRET", "Google OAuth client_secret not configured"),
  "discord": ("DISCORD_AUTH_SECRET", "Discord OAuth client_secret not configured"),
  "microsoft": ("MICROSOFT_AUTH_SECRET", "Microsoft OAuth client_secret not configured"),
}

_REDIRECT_ERRORS = {
  "google": "Google OAuth redirect URI not configured",
  "discord": "Discord OAuth redirect URI not configured",
  "microsoft": "Microsoft OAuth redirect URI not configured",
}


class UserProvidersModule(BaseModule):
  def __init__(self, app: FastAPI):
    super().__init__(app)
    self.db: DbModule | None = None
    self.auth: AuthModule | None = None
    self.oauth: OauthModule | None = None
    self.env: EnvModule | None = None

  async def startup(self):
    self.db = self.app.state.db
    await self.db.on_ready()
    self.auth = self.app.state.auth
    await self.auth.on_ready()
    self.oauth = self.app.state.oauth
    await self.oauth.on_ready()
    self.env = self.app.state.env
    await self.env.on_ready()
    self.mark_ready()

  async def shutdown(self):
    self.db = None
    self.auth = None
    self.oauth = None
    self.env = None

  async def set_provider(
    self,
    guid: str,
    provider: str,
    *,
    code: str | None = None,
    id_token: str | None = None,
    access_token: str | None = None,
  ) -> None:
    id_token, access_token, profile = await self._authenticate_provider(
      provider,
      code=code,
      id_token=id_token,
      access_token=access_token,
    )
    assert self.db, "database module not initialised"
    request = set_provider_request(guid=guid, provider=provider)
    await self.db.run(request)
    if profile:
      await self._update_profile_from_login(guid, profile)

  async def link_provider(
    self,
    guid: str,
    provider: str,
    *,
    code: str | None = None,
    id_token: str | None = None,
    access_token: str | None = None,
  ) -> None:
    provider_uid, _, _ = await self._authenticate_provider(
      provider,
      code=code,
      id_token=id_token,
      access_token=access_token,
      require_login=True,
    )
    provider_uid = self._normalize_provider_identifier(provider_uid)
    assert self.db, "database module not initialised"
    lookup_request = get_by_provider_identifier_request(
      provider=provider,
      provider_identifier=provider_uid,
    )
    res = await self.db.run(lookup_request)
    if res.rows and str(res.rows[0].get("guid")) != str(guid):
      raise HTTPException(status_code=409, detail="Provider already linked")
    link_request = link_provider_request(
      guid=guid,
      provider=provider,
      provider_identifier=provider_uid,
    )
    await self.db.run(link_request)

  async def unlink_provider(
    self,
    guid: str,
    provider: str,
    *,
    new_default: str | None = None,
  ) -> None:
    assert self.db, "database module not initialised"
    profile_request = get_profile_request(guid=guid)
    res_profile = await self.db.run(profile_request)
    default_provider = res_profile.rows[0].get("default_provider") if res_profile.rows else None
    unlink_request = unlink_provider_request(guid=guid, provider=provider)
    res = await self.db.run(unlink_request)
    remaining = res.rows[0].get("providers_remaining") if res.rows else 0
    if remaining == 0:
      await self.unlink_last_provider(guid=guid, provider=provider)
      return
    if provider == default_provider:
      if not new_default:
        raise HTTPException(status_code=400, detail="new_default required")
      set_request = set_provider_request(guid=guid, provider=new_default)
      await self.db.run(set_request)
      revoke_request = revoke_provider_tokens_request(guid=guid, provider=provider)
      await self.db.run(revoke_request)

  async def unlink_last_provider(self, guid: str, provider: str) -> None:
    assert self.db, "database module not initialised"
    request = unlink_last_provider_request(guid=guid, provider=provider)
    await self.db.run(request)

  async def get_by_provider_identifier(self, provider: str, provider_identifier: str):
    assert self.db, "database module not initialised"
    request = get_by_provider_identifier_request(
      provider=provider,
      provider_identifier=provider_identifier,
    )
    res = await self.db.run(request)
    return res.rows[0] if res.rows else None

  async def create_from_provider(
    self,
    provider: str,
    provider_identifier: str,
    provider_email: str,
    provider_displayname: str | None,
    provider_profile_image: str | None,
  ):
    assert self.db, "database module not initialised"
    email_request = get_user_by_email_request(email=provider_email)
    res = await self.db.run(email_request)
    if res.rows:
      raise HTTPException(status_code=409, detail="Email already registered")
    create_request = create_from_provider_request(
      provider=provider,
      provider_identifier=provider_identifier,
      provider_email=provider_email,
      provider_displayname=provider_displayname,
      provider_profile_image=provider_profile_image,
    )
    res = await self.db.run(create_request)
    return res.rows[0] if res.rows else None

  async def _authenticate_provider(
    self,
    provider: str,
    *,
    code: str | None,
    id_token: str | None,
    access_token: str | None,
    require_login: bool = False,
  ):
    if provider not in ("google", "discord", "microsoft"):
      raise HTTPException(status_code=400, detail="Unsupported auth provider")
    auth = self._require_auth()
    oauth = self._require_oauth()
    strategy = getattr(auth, "providers", {}).get(provider)
    if not strategy or not getattr(strategy, "audience", None):
      raise HTTPException(status_code=500, detail=_CLIENT_ID_ERRORS[provider])
    if code:
      client_id = getattr(strategy, "audience")
      client_secret = self._get_client_secret(provider)
      redirect_uri = await self._get_redirect_uri(provider)
      id_token, access_token = await oauth.exchange_code_for_tokens(
        code,
        client_id,
        client_secret,
        redirect_uri,
        provider,
      )
      if provider in ("google", "microsoft") and not id_token:
        raise HTTPException(status_code=400, detail="Missing id_token")
      if provider == "discord" and not access_token:
        raise HTTPException(status_code=400, detail="access_token required")
    else:
      if provider == "discord" and not access_token:
        raise HTTPException(status_code=400, detail="access_token required")
      if provider == "microsoft" and (not id_token or not access_token):
        raise HTTPException(status_code=400, detail="id_token and access_token required")
    if require_login:
      guid, profile, payload = await auth.handle_auth_login(provider, id_token, access_token)
      return guid, profile, payload
    profile = None
    if access_token or id_token:
      _, profile, _ = await auth.handle_auth_login(provider, id_token, access_token)
    return id_token, access_token, profile

  def _require_auth(self) -> AuthModule:
    assert self.auth, "auth module not initialised"
    return self.auth

  def _require_oauth(self) -> OauthModule:
    assert self.oauth, "oauth module not initialised"
    return self.oauth

  def _require_env(self) -> EnvModule:
    assert self.env, "env module not initialised"
    return self.env

  def _require_db(self) -> DbModule:
    assert self.db, "database module not initialised"
    return self.db

  def _get_client_secret(self, provider: str) -> str:
    env_module = self._require_env()
    env_key, error_message = _CLIENT_SECRET_ENV[provider]
    try:
      secret = env_module.get(env_key)
    except RuntimeError:
      secret = None
    if not secret:
      raise HTTPException(status_code=500, detail=error_message)
    return secret

  async def _get_redirect_uri(self, provider: str) -> str:
    db = self._require_db()
    res = await db.run(get_config_request("Hostname"))
    if not res.rows:
      raise HTTPException(status_code=500, detail=_REDIRECT_ERRORS[provider])
    return res.rows[0]["value"]

  async def _update_profile_from_login(self, guid: str, profile: dict) -> None:
    raw_email = (profile.get("email") or "").strip()
    raw_name = (profile.get("username") or "").strip()
    display_name = raw_name or (raw_email.split("@")[0] if raw_email else "User")
    db = self._require_db()
    request = update_if_unedited_request(
      guid=guid,
      email=raw_email,
      display_name=display_name,
    )
    await db.run(request)

  def _normalize_provider_identifier(self, pid: str) -> str:
    try:
      return str(uuid.UUID(pid))
    except ValueError:
      return str(uuid.uuid5(uuid.NAMESPACE_URL, pid))

