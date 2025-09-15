import base64, logging, uuid
import aiohttp
from datetime import datetime, timezone, timedelta

from fastapi import FastAPI, HTTPException
from . import BaseModule

from server.modules.auth_module import AuthModule
try:
  from server.modules.auth_module import DEFAULT_SESSION_TOKEN_EXPIRY
except Exception:
  DEFAULT_SESSION_TOKEN_EXPIRY = 15
from server.modules.db_module import DbModule
from server.modules.discord_module import DiscordModule


class OauthModule(BaseModule):
  TOKEN_ENDPOINTS = {
    "google": "https://oauth2.googleapis.com/token",
    "microsoft": "https://login.microsoftonline.com/consumers/oauth2/v2.0/token",
    "discord": "https://discord.com/api/oauth2/token",
  }

  def __init__(self, app: FastAPI):
    super().__init__(app)
    self.discord: DiscordModule | None = None

  async def startup(self):
    self.auth: AuthModule = self.app.state.auth
    await self.auth.on_ready()
    self.db: DbModule = self.app.state.db
    await self.db.on_ready()
    self.discord = getattr(self.app.state, "discord", None)
    if self.discord:
      await self.discord.on_ready()
    self.mark_ready()

  async def shutdown(self):
    pass

  async def exchange_code_for_tokens(
    self,
    code: str,
    client_id: str,
    client_secret: str,
    redirect_uri: str,
    provider: str = "google",
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
        "db:users:providers:get_by_provider_identifier:1",
        {"provider": provider, "provider_identifier": uid},
      )
      if res.rows:
        logging.debug(f"[lookup_user] user found with identifier={pid[:40]}")
        return res.rows[0]
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
    await self.db.run(
      "db:users:session:set_rotkey:1",
      {"guid": user_guid, "rotkey": rotation_token, "iat": now, "exp": rot_exp},
    )
    roles, _ = await self.auth.get_user_roles(user_guid)
    session_exp = now + timedelta(minutes=DEFAULT_SESSION_TOKEN_EXPIRY)
    placeholder = uuid.uuid4().hex
    res = await self.db.run(
      "db:auth:session:create_session:1",
      {
        "access_token": placeholder,
        "expires": session_exp,
        "fingerprint": fingerprint,
        "user_agent": user_agent,
        "ip_address": ip_address,
        "user_guid": user_guid,
        "provider": provider,
      },
    )
    row = res.rows[0] if res.rows else {}
    session_guid = row.get("session_guid")
    device_guid = row.get("device_guid")
    session_token, _ = self.auth.make_session_token(
      user_guid, rotation_token, session_guid, device_guid, roles, exp=session_exp,
    )
    await self.db.run(
      "db:auth:session:update_device_token:1",
      {"device_guid": device_guid, "access_token": session_token},
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
        "db:users:providers:get_any_by_provider_identifier:1",
        {"provider": provider, "provider_identifier": provider_uid},
      )
      needs_relink = True

    if needs_relink:
      res = await self.db.run(
        f"db:auth:{provider}:oauth_relink:1",
        {
          "provider_identifier": provider_uid,
          "email": profile["email"],
          "display_name": profile["username"],
          "profile_image": profile.get("profilePicture"),
          "confirm": confirm,
          "reauth_token": reauth_token,
        },
      )
      user = res.rows[0] if res.rows else None

    if not user:
      res = await self.db.run(
        "db:users:providers:create_from_provider:1",
        {
          "provider": provider,
          "provider_identifier": provider_uid,
          "provider_email": profile["email"],
          "provider_displayname": profile["username"],
          "provider_profile_image": profile.get("profilePicture"),
        },
      )
      user = res.rows[0] if res.rows else None
      if not user:
        res = await self.db.run(
          "db:users:providers:get_by_provider_identifier:1",
          {"provider": provider, "provider_identifier": provider_uid},
        )
        user = res.rows[0] if res.rows else None
      if not user:
        logging.debug("[resolve_user] failed to create user")
        raise HTTPException(status_code=500, detail="Unable to create user")

    return user

