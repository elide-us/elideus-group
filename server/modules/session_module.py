from __future__ import annotations
import logging, uuid
from datetime import datetime, timedelta, timezone
from fastapi import FastAPI, HTTPException

from server.modules import BaseModule
from server.modules.auth_module import AuthModule, DEFAULT_SESSION_TOKEN_EXPIRY
from server.modules.db_module import DbModule
from server.modules.oauth_module import OauthModule
from server.modules.discord_module import DiscordModule


class SessionModule(BaseModule):
  def __init__(self, app: FastAPI):
    super().__init__(app)
    self.discord: DiscordModule | None = None

  async def startup(self):
    self.auth: AuthModule = self.app.state.auth
    await self.auth.on_ready()
    self.db: DbModule = self.app.state.db
    await self.db.on_ready()
    self.oauth: OauthModule = self.app.state.oauth
    await self.oauth.on_ready()
    self.discord = getattr(self.app.state, "discord", None)
    if self.discord:
      await self.discord.on_ready()
    self.mark_ready()

  async def shutdown(self):
    pass

  async def issue_token(
    self,
    provider: str,
    id_token: str,
    access_token: str,
    fingerprint: str,
    user_agent: str | None,
    ip_address: str | None,
    confirm: bool | None = None,
    reauth_token: str | None = None,
  ) -> tuple[str, str, datetime, dict]:
    if not provider or not id_token or not access_token:
      raise HTTPException(status_code=400, detail="Missing credentials")

    provider_uid, provider_profile, payload = await self.auth.handle_auth_login(
      provider, id_token, access_token
    )

    try:
      user = await self.oauth.resolve_user(
        provider,
        provider_uid,
        provider_profile,
        payload,
        confirm=confirm,
        reauth_token=reauth_token,
      )
    except HTTPException as e:
      if e.status_code == 409:
        raise
      raise

    new_img = provider_profile.get("profilePicture")
    if new_img and new_img != user.get("profile_image"):
      await self.db.run(
        "urn:users:profile:set_profile_image:1",
        {"guid": user["guid"], "image_b64": new_img, "provider": provider},
      )
      user["profile_image"] = new_img

    user_guid = user["guid"]
    session_token, _, rotation_token, rot_exp = await self.oauth.create_session(
      user_guid, provider, fingerprint, user_agent, ip_address
    )

    profile = {
      "display_name": user["display_name"],
      "email": user.get("email"),
      "credits": user.get("credits"),
      "profile_image": user.get("profile_image"),
    }
    return session_token, rotation_token, rot_exp, profile

  async def refresh_token(
    self,
    rotation_token: str,
    fingerprint: str,
    user_agent: str | None,
    ip_address: str | None,
  ) -> str:
    data = self.auth.decode_rotation_token(rotation_token)
    user_guid = data["guid"]
    stored = await self.db.run("db:users:session:get_rotkey:1", {"guid": user_guid})
    row = stored.rows[0] if stored.rows else None
    if not row or row.get("rotkey") != rotation_token:
      raise HTTPException(status_code=401, detail="Invalid rotation token")
    provider = row.get("provider_name") or "microsoft"
    roles, _ = await self.auth.get_user_roles(user_guid)
    session_exp = datetime.now(timezone.utc) + timedelta(
      minutes=DEFAULT_SESSION_TOKEN_EXPIRY
    )
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
    row2 = res.rows[0] if res.rows else {}
    session_guid = row2.get("session_guid")
    device_guid = row2.get("device_guid")
    session_token, _ = self.auth.make_session_token(
      user_guid, rotation_token, session_guid, device_guid, roles, exp=session_exp
    )
    await self.db.run(
      "db:auth:session:update_device_token:1",
      {"device_guid": device_guid, "access_token": session_token},
    )
    return session_token

  async def invalidate_token(self, user_guid: str) -> None:
    now = datetime.now(timezone.utc)
    await self.db.run(
      "db:users:session:set_rotkey:1",
      {"guid": user_guid, "rotkey": "", "iat": now, "exp": now},
    )

  async def logout_device(self, token: str) -> None:
    await self.db.run(
      "db:auth:session:revoke_device_token:1",
      {"access_token": token},
    )

  async def get_session(
    self,
    token: str,
    ip_address: str | None,
    user_agent: str | None,
  ) -> dict:
    res = await self.db.run(
      "db:auth:session:get_by_access_token:1", {"access_token": token}
    )
    session = res.rows[0] if res.rows else None
    if not session:
      raise HTTPException(status_code=401, detail="Invalid session token")

    if session.get("revoked_at"):
      raise HTTPException(status_code=401, detail="Session revoked")

    expires_at = session.get("expires_at")
    if expires_at:
      try:
        exp_dt = datetime.fromisoformat(expires_at)
      except ValueError:
        exp_dt = None
      if exp_dt and exp_dt.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
        raise HTTPException(status_code=401, detail="Session expired")

    try:
      await self.db.run(
        "db:auth:session:update_session:1",
        {"access_token": token, "ip_address": ip_address, "user_agent": user_agent},
      )
    except Exception as e:
      logging.error("[SessionModule.get_session] Failed to update session metadata: %s", e)

    payload = {
      "session_guid": session.get("session_guid"),
      "device_guid": session.get("device_guid"),
      "user_guid": session.get("user_guid"),
      "issued_at": session.get("issued_at"),
      "expires_at": session.get("expires_at"),
      "device_fingerprint": session.get("device_fingerprint"),
      "user_agent": session.get("user_agent"),
      "ip_last_seen": session.get("ip_last_seen"),
    }
    return payload
