from __future__ import annotations

import base64, logging, uuid
from collections.abc import Mapping
import aiohttp
from datetime import datetime, timezone, timedelta

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from queryregistry.identity.profiles import (
  get_profile_request,
  update_if_unedited_request,
  update_profile_request,
)
from queryregistry.identity.profiles.models import (
  GuidParams,
  UpdateIfUneditedParams,
  UpdateProfileParams,
)
from queryregistry.identity.sessions.models import (
  CreateSessionParams,
  RevokeProviderTokensParams,
  UpdateDeviceTokenParams,
)
from queryregistry.system.config.models import ConfigKeyParams
from . import BaseModule

from server.modules.auth_module import AuthModule
try:
  from server.modules.auth_module import DEFAULT_SESSION_TOKEN_EXPIRY
except Exception:
  DEFAULT_SESSION_TOKEN_EXPIRY = 15
from server.modules.db_module import DbModule
from server.modules.discord_bot_module import DiscordBotModule
from queryregistry.identity.auth import (
  create_from_provider_request,
  get_any_by_provider_identifier_request,
  get_by_provider_identifier_request,
  get_user_by_email_request,
  link_provider_request,
  relink_provider_request,
  set_provider_request,
  unlink_last_provider_request,
  unlink_provider_request,
)
from queryregistry.identity.sessions import (
  create_session_request,
  revoke_provider_tokens_request,
  update_device_token_request,
)
from queryregistry.finance.credits import set_credits_request
from queryregistry.finance.credits.models import SetCreditsParams
from queryregistry.system.config import get_config_request

class UsersProvidersSetProviderResult1(BaseModel):
  provider: str
  code: str | None = None
  id_token: str | None = None
  access_token: str | None = None


class UsersProvidersLinkProviderResult1(BaseModel):
  provider: str


class UsersProvidersUnlinkProviderResult1(BaseModel):
  provider: str


class UsersProvidersGetByProviderIdentifierResult1(BaseModel):
  guid: str | None = None
  provider: str | None = None
  provider_identifier: str | None = None


class UsersProvidersCreateFromProviderResult1(BaseModel):
  guid: str | None = None


class OauthModule(BaseModule):
  TOKEN_ENDPOINTS = {
    "google": "https://oauth2.googleapis.com/token",
    "microsoft": "https://login.microsoftonline.com/consumers/oauth2/v2.0/token",
    "discord": "https://discord.com/api/oauth2/token",
  }

  def __init__(self, app: FastAPI):
    super().__init__(app)
    self.discord: DiscordBotModule | None = None
    self.env = None
    self._redirect_uri: str | None = None

  async def startup(self):
    self.auth: AuthModule = self.app.state.auth
    await self.auth.on_ready()
    self.db: DbModule = self.app.state.db
    await self.db.on_ready()
    self.env = getattr(self.app.state, "env", None)
    if self.env:
      await self.env.on_ready()
    self.discord = getattr(self.app.state, "discord_bot", None)
    if self.discord:
      await self.discord.on_ready()
    self.mark_ready()

  async def shutdown(self):
    pass

  def _normalize_query_payload(self, payload: object | None) -> list[dict]:
    if payload is None:
      return []
    if isinstance(payload, list):
      return [dict(item) for item in payload]
    if isinstance(payload, Mapping):
      return [dict(payload)]
    return [dict(payload)]


  def _provider_title(self, provider: str) -> str:
    return {"google": "Google", "microsoft": "Microsoft", "discord": "Discord"}.get(
      provider, provider.title()
    )

  def _get_secret_var(self, provider: str) -> str | None:
    return {
      "google": "GOOGLE_AUTH_SECRET",
      "microsoft": "MICROSOFT_AUTH_SECRET",
      "discord": "DISCORD_AUTH_SECRET",
    }.get(provider)

  async def _get_redirect_uri(self, provider: str) -> str:
    if self._redirect_uri:
      return self._redirect_uri
    res = await self.db.run(get_config_request(ConfigKeyParams(key="Hostname")))
    if not res.rows:
      raise HTTPException(
        status_code=500,
        detail=f"{self._provider_title(provider)} OAuth redirect URI not configured",
      )
    self._redirect_uri = f"https://{res.rows[0]['element_value']}"
    return self._redirect_uri

  def _get_provider_client_id(self, provider: str) -> str:
    providers = getattr(self.auth, "providers", {})
    provider_data = providers.get(provider)
    audience = getattr(provider_data, "audience", None) if provider_data else None
    if not audience:
      raise HTTPException(
        status_code=500,
        detail=f"{self._provider_title(provider)} OAuth client_id not configured",
      )
    return audience

  async def _prepare_tokens(
    self,
    provider: str,
    code: str | None,
    id_token: str | None,
    access_token: str | None,
  ) -> tuple[str | None, str | None]:
    provider = provider.lower()
    if provider not in ("google", "microsoft", "discord"):
      raise HTTPException(status_code=400, detail="Unsupported auth provider")
    client_id = self._get_provider_client_id(provider)
    if code:
      secret_var = self._get_secret_var(provider)
      if not self.env or not secret_var:
        raise HTTPException(
          status_code=500,
          detail=f"{self._provider_title(provider)} OAuth client_secret not configured",
        )
      client_secret = self.env.get(secret_var)
      if not client_secret:
        raise HTTPException(
          status_code=500,
          detail=f"{self._provider_title(provider)} OAuth client_secret not configured",
        )
      redirect_uri = await self._get_redirect_uri(provider)
      id_token, access_token = await self.exchange_code_for_tokens(
        code, client_id, client_secret, redirect_uri, provider
      )
      if provider in ("google", "microsoft") and not id_token:
        raise HTTPException(status_code=400, detail="Missing id_token")
    else:
      if provider == "discord" and not access_token:
        raise HTTPException(status_code=400, detail="access_token required")
      if provider == "microsoft" and (not id_token or not access_token):
        raise HTTPException(
          status_code=400, detail="id_token and access_token required"
        )
    return id_token, access_token

  def normalize_provider_identifier(self, pid: str) -> str:
    try:
      return str(uuid.UUID(pid))
    except ValueError:
      return str(uuid.uuid5(uuid.NAMESPACE_URL, pid))

  async def set_user_default_provider(
    self,
    user_guid: str,
    provider: str,
    *,
    code: str | None = None,
    id_token: str | None = None,
    access_token: str | None = None,
  ) -> UsersProvidersSetProviderResult1:
    original = {
      "provider": provider,
      "code": code,
      "id_token": id_token,
      "access_token": access_token,
    }
    id_token, access_token = await self._prepare_tokens(
      provider, code, id_token, access_token
    )
    profile = None
    if id_token or access_token:
      _, profile, _ = await self.auth.handle_auth_login(
        provider, id_token, access_token
      )
    await self.db.run(
      set_provider_request(guid=user_guid, provider=provider),
    )
    if profile:
      raw_email = (profile.get("email") or "").strip()
      raw_name = (profile.get("username") or "").strip()
      email = raw_email
      display_name = raw_name or (raw_email.split("@")[0] if raw_email else "User")
      params = UpdateIfUneditedParams(
        guid=user_guid,
        email=email,
        display_name=display_name,
      )
      await self.db.run(update_if_unedited_request(params))
    return UsersProvidersSetProviderResult1(**original)

  async def link_user_provider(
    self,
    user_guid: str,
    provider: str,
    *,
    code: str | None = None,
    id_token: str | None = None,
    access_token: str | None = None,
  ) -> UsersProvidersLinkProviderResult1:
    provider_key = provider.lower()
    if provider_key == "google" and not code:
      raise HTTPException(status_code=400, detail="code required")
    id_token, access_token = await self._prepare_tokens(
      provider, code, id_token, access_token
    )
    provider_uid, _, _ = await self.auth.handle_auth_login(
      provider, id_token, access_token
    )
    provider_uid = self.normalize_provider_identifier(provider_uid)
    res = await self.db.run(
      get_by_provider_identifier_request(
        provider=provider,
        provider_identifier=provider_uid,
      ),
    )
    rows = self._normalize_query_payload(res.payload)
    if rows and rows[0].get("guid") != user_guid:
      raise HTTPException(status_code=409, detail="Provider already linked")
    await self.db.run(
      link_provider_request(
        guid=user_guid,
        provider=provider,
        provider_identifier=provider_uid,
      ),
    )
    return UsersProvidersLinkProviderResult1(provider=provider)

  async def unlink_user_provider(
    self,
    user_guid: str,
    provider: str,
    *,
    new_default: str | None = None,
  ) -> UsersProvidersUnlinkProviderResult1:
    res_prof = await self.db.run(
      get_profile_request(GuidParams(guid=user_guid))
    )
    default_provider = res_prof.rows[0].get("default_provider") if res_prof.rows else None
    res = await self.db.run(
      unlink_provider_request(guid=user_guid, provider=provider),
    )
    rows = self._normalize_query_payload(res.payload)
    remaining = rows[0].get("providers_remaining") if rows else 0
    if remaining == 0:
      await self.db.run(
        unlink_last_provider_request(guid=user_guid, provider=provider),
      )
    elif provider == default_provider:
      if not new_default:
        raise HTTPException(status_code=400, detail="new_default required")
      await self.db.run(
        set_provider_request(guid=user_guid, provider=new_default),
      )
      await self.db.run(
        revoke_provider_tokens_request(
          RevokeProviderTokensParams(guid=user_guid, provider=provider)
        )
      )
    return UsersProvidersUnlinkProviderResult1(provider=provider)

  async def unlink_last_provider_record(self, guid: str, provider: str) -> None:
    assert self.db
    await self.db.run(
      unlink_last_provider_request(guid=guid, provider=provider),
    )

  async def get_user_by_provider_identifier(
    self, provider: str, provider_identifier: str
  ) -> UsersProvidersGetByProviderIdentifierResult1:
    res = await self.db.run(
      get_by_provider_identifier_request(
        provider=provider,
        provider_identifier=provider_identifier,
      ),
    )
    rows = self._normalize_query_payload(res.payload)
    if not rows:
      return UsersProvidersGetByProviderIdentifierResult1()
    return UsersProvidersGetByProviderIdentifierResult1(**rows[0])

  async def create_user_from_provider(
    self,
    provider: str,
    provider_identifier: str,
    provider_email: str,
    provider_displayname: str,
    provider_profile_image: str | None = None,
  ) -> UsersProvidersCreateFromProviderResult1:
    res = await self.db.run(
      get_user_by_email_request(email=provider_email),
    )
    rows = self._normalize_query_payload(res.payload)
    if rows:
      raise HTTPException(status_code=409, detail="Email already registered")
    res = await self.db.run(
      create_from_provider_request(
        provider=provider,
        provider_identifier=provider_identifier,
        provider_email=provider_email,
        provider_displayname=provider_displayname,
        provider_profile_image=provider_profile_image,
      ),
    )
    rows = self._normalize_query_payload(res.payload)
    if not rows:
      return UsersProvidersCreateFromProviderResult1()
    return UsersProvidersCreateFromProviderResult1(**rows[0])

  async def register_discord_user(self, discord_id: str) -> dict:
    auth: AuthModule = self.app.state.auth
    await auth.on_ready()
    guid, _, _ = await auth.get_discord_user_security(discord_id)
    if guid:
      return {
        "success": True,
        "message": "You are already registered.",
        "user_guid": guid,
        "credits": None,
      }
    return {
      "success": False,
      "message": "Registration is disabled.",
      "user_guid": guid,
      "credits": None,
    }

  async def exchange_code_for_tokens(
    self,
    code: str,
    client_id: str,
    client_secret: str,
    redirect_uri: str,
    provider: str = "google",
    code_verifier: str | None = None,
  ) -> tuple[str | None, str]:
    """Exchange an authorization code for tokens.

    Args:
      code: Authorization code from the provider.
      client_id: OAuth client ID.
      client_secret: OAuth client secret.
      redirect_uri: Redirect URI registered with the provider.
      provider: Provider identifier from the ``auth_providers`` table
        (e.g., ``"discord"`` or its numeric ID) used to select the token
        endpoint.

    Returns:
      A tuple of ``(id_token, access_token)``. ``id_token`` may be ``None``
      for providers that do not issue one.
    """
    token_endpoint = self.TOKEN_ENDPOINTS.get(provider)
    if not token_endpoint:
      raise HTTPException(status_code=400, detail="Unsupported auth provider")
    data = {
      "code": code,
      "client_id": client_id,
      "client_secret": client_secret,
      "redirect_uri": redirect_uri,
      "grant_type": "authorization_code",
    }
    if code_verifier:
      data["code_verifier"] = code_verifier
    logging.debug(
      "[exchange_code_for_tokens] data=%s",
      {k: v for k, v in data.items() if k != "client_secret"},
    )
    logging.debug("[exchange_code_for_tokens] exchanging code for tokens")
    async with aiohttp.ClientSession() as session:
      async with session.post(token_endpoint, data=data) as resp:
        if resp.status != 200:
          error = await resp.text()
          logging.error(
            "[exchange_code_for_tokens] failed status=%s error=%s", resp.status, error,
          )
          raise HTTPException(status_code=400, detail="Failed to exchange authorization code")
        token_data = await resp.json()
    id_token = token_data.get("id_token")
    access_token = token_data.get("access_token")
    if not access_token:
      logging.error("[exchange_code_for_tokens] missing access token in response")
      raise HTTPException(status_code=400, detail="Invalid token response")
    if not id_token:
      logging.warning("[exchange_code_for_tokens] id_token missing in response")
    return id_token, access_token

  def extract_identifiers(
    self,
    provider_uid: str | None,
    payload: dict,
    provider: str = "google",
  ) -> list[str]:
    identifiers = []
    if provider_uid:
      identifiers.append(provider_uid)
    oid = payload.get("oid")
    sub = payload.get("sub")
    if oid and oid not in identifiers:
      identifiers.append(oid)
    if sub and sub not in identifiers:
      identifiers.append(sub)
    base_id = None
    for candidate in (oid, sub, provider_uid):
      if not candidate:
        continue
      try:
        base_id = str(uuid.UUID(candidate))
        break
      except ValueError:
        continue
    if base_id:
      home_account_id = base64.urlsafe_b64encode(
        b"\x00" * 16 + uuid.UUID(base_id).bytes
      ).decode("utf-8").rstrip("=")
      if home_account_id not in identifiers:
        identifiers.append(home_account_id)
      logging.debug(
        f"[extract_identifiers] home_account_id={home_account_id[:40]}",
      )
    else:
      bad = oid or sub or provider_uid
      if bad and provider == "microsoft":
        try:
          uuid.UUID(bad)
        except Exception as e:
          logging.exception(
            f"[extract_identifiers] home_account_id generation failed for {bad}: {e}",
          )
    return identifiers

  async def lookup_user(self, provider: str, identifiers: list[str]):
    def _norm(pid: str) -> str | None:
      try:
        return str(uuid.UUID(pid))
      except ValueError:
        try:
          pad = pid + "=" * (-len(pid) % 4)
          raw = base64.urlsafe_b64decode(pad)
          if len(raw) >= 16:
            return str(uuid.UUID(bytes=raw[-16:]))
        except Exception:
          return None
      return None

    checked = set()
    for pid in identifiers:
      uid = _norm(pid)
      if not uid or uid in checked:
        continue
      checked.add(uid)
      logging.debug(f"[lookup_user] checking identifier={pid[:40]}")
      res = await self.db.run(
        get_by_provider_identifier_request(
          provider=provider,
          provider_identifier=uid,
        ),
      )
      rows = self._normalize_query_payload(res.payload)
      if rows:
        logging.debug(f"[lookup_user] user found with identifier={pid[:40]}")
        return rows[0]
    return None

  async def create_session(
    self,
    user_guid: str,
    provider: str,
    fingerprint: str,
    user_agent: str | None,
    ip_address: str | None,
  ):
    rotation_token, rot_exp = self.auth.make_rotation_token(user_guid)
    logging.debug(f"[create_session] rotation_token={rotation_token[:40]}")
    now = datetime.now(timezone.utc)
    roles, _ = await self.auth.get_user_roles(user_guid)
    session_exp = now + timedelta(minutes=DEFAULT_SESSION_TOKEN_EXPIRY)
    placeholder = uuid.uuid4().hex
    res = await self.db.run(
      create_session_request(
        CreateSessionParams(
          access_token=placeholder,
          expires=session_exp,
          fingerprint=fingerprint,
          rotkey=rotation_token,
          rotkey_iat=now,
          rotkey_exp=rot_exp,
          user_guid=user_guid,
          provider=provider,
          user_agent=user_agent,
          ip_address=ip_address,
        ),
      ),
    )
    row = res.rows[0] if res.rows else {}
    session_guid = row.get("session_guid")
    device_guid = row.get("device_guid")
    session_token, _ = self.auth.make_session_token(
      user_guid, rotation_token, session_guid, device_guid, roles, exp=session_exp,
    )
    await self.db.run(
      update_device_token_request(
        UpdateDeviceTokenParams(device_guid=device_guid, access_token=session_token),
      ),
    )
    logging.debug(f"[create_session] session_token={session_token[:40]}")
    return session_token, session_exp, rotation_token, rot_exp

  async def resolve_user(
    self,
    provider: str,
    provider_uid: str,
    profile: dict,
    payload: dict,
    confirm: bool | None = None,
    reauth_token: str | None = None,
  ):
    identifiers = self.extract_identifiers(provider_uid, payload, provider)
    user = await self.lookup_user(provider, identifiers)
    needs_relink = False
    if user and user.get("element_soft_deleted_at"):
      needs_relink = True
    elif not user:
      await self.db.run(
        get_any_by_provider_identifier_request(
          provider_identifier=provider_uid,
        ),
      )
      needs_relink = True

    if needs_relink:
      request = relink_provider_request(
        provider=provider,
        provider_identifier=provider_uid,
        email=profile["email"],
        display_name=profile["username"],
        profile_image=profile.get("profilePicture"),
        confirm=confirm,
        reauth_token=reauth_token,
      )
      res = await self.db.run(request)
      rows = self._normalize_query_payload(res.payload)
      user = rows[0] if rows else None

    if not user:
      res = await self.db.run(
        create_from_provider_request(
          provider=provider,
          provider_identifier=provider_uid,
          provider_email=profile["email"],
          provider_displayname=profile["username"],
          provider_profile_image=profile.get("profilePicture"),
        ),
      )
      rows = self._normalize_query_payload(res.payload)
      user = rows[0] if rows else None
      if not user:
        res = await self.db.run(
          get_by_provider_identifier_request(
            provider=provider,
            provider_identifier=provider_uid,
          ),
        )
        rows = self._normalize_query_payload(res.payload)
        user = rows[0] if rows else None
      if not user:
        logging.debug("[resolve_user] failed to create user")
        raise HTTPException(status_code=500, detail="Unable to create user")

    return user

  async def login_provider(
    self,
    provider: str,
    *,
    fingerprint: str | None,
    code: str | None = None,
    id_token: str | None = None,
    access_token: str | None = None,
    confirm: bool | None = None,
    reauth_token: str | None = None,
    user_agent: str | None = None,
    ip_address: str | None = None,
  ):
    provider = provider.lower()
    if not fingerprint:
      raise HTTPException(status_code=400, detail="Missing fingerprint")
    id_token, access_token = await self._prepare_tokens(
      provider, code, id_token, access_token
    )
    provider_uid, profile, payload = await self.auth.handle_auth_login(
      provider, id_token, access_token
    )
    provider_uid = self.normalize_provider_identifier(provider_uid)
    user = await self.resolve_user(
      provider,
      provider_uid,
      profile,
      payload,
      confirm=confirm,
      reauth_token=reauth_token,
    )
    user_guid = user["guid"]
    new_img = profile.get("profilePicture")
    if new_img and new_img != user.get("profile_image"):
      await self.db.run(
        update_profile_request(
          UpdateProfileParams(
            guid=user_guid,
            provider=provider,
            image_b64=new_img,
          ),
        )
      )
      user["profile_image"] = new_img
    if user.get("provider_name") == provider:
      params = UpdateIfUneditedParams(
        guid=user_guid,
        email=profile["email"],
        display_name=profile["username"],
      )
      res_prof = await self.db.run(update_if_unedited_request(params))
      rows = self._normalize_query_payload(res_prof.payload)
      if rows:
        updated = rows[0]
        if updated.get("display_name"):
          user["display_name"] = updated["display_name"]
        if updated.get("email"):
          user["email"] = updated["email"]
    session_token, session_exp, rotation_token, rot_exp = await self.create_session(
      user_guid, provider, fingerprint, user_agent, ip_address
    )
    return {
      "session_token": session_token,
      "session_exp": session_exp,
      "rotation_token": rotation_token,
      "rotation_exp": rot_exp,
      "user": user,
      "profile": profile,
    }
