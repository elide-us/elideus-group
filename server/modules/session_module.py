from __future__ import annotations
import base64, logging, uuid
from datetime import datetime, timedelta, timezone
from fastapi import FastAPI, HTTPException

from server.modules import BaseModule
from server.modules.auth_module import AuthModule, DEFAULT_SESSION_TOKEN_EXPIRY
from server.modules.db_module import DbModule


class SessionModule(BaseModule):
  def __init__(self, app: FastAPI):
    super().__init__(app)

  async def startup(self):
    self.auth: AuthModule = self.app.state.auth
    await self.auth.on_ready()
    self.db: DbModule = self.app.state.db
    await self.db.on_ready()
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
  ) -> tuple[str, str, datetime, dict]:
    if not provider or not id_token or not access_token:
      raise HTTPException(status_code=400, detail="Missing credentials")

    provider_uid, provider_profile, payload = await self.auth.handle_auth_login(
      provider, id_token, access_token
    )

    identifiers = []
    if provider_uid:
      identifiers.append(provider_uid)
    oid = payload.get("oid")
    sub = payload.get("sub")
    if oid and oid not in identifiers:
      identifiers.append(oid)
    if sub and sub not in identifiers:
      identifiers.append(sub)
    base_id = oid or sub or provider_uid
    if base_id:
      try:
        home_account_id = base64.urlsafe_b64encode(
          b"\x00" * 16 + uuid.UUID(base_id).bytes
        ).decode("utf-8").rstrip("=")
        if home_account_id not in identifiers:
          identifiers.append(home_account_id)
      except Exception:
        pass

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

    user = None
    checked = set()
    for pid in identifiers:
      uid = _norm(pid)
      if not uid or uid in checked:
        continue
      checked.add(uid)
      res = await self.db.run(
        "urn:users:providers:get_by_provider_identifier:1",
        {"provider": provider, "provider_identifier": uid},
      )
      if res.rows:
        user = res.rows[0]
        break

    if not user:
      try:
        provider_uid = str(uuid.UUID(provider_uid))
      except ValueError:
        raise HTTPException(status_code=400, detail="Invalid provider identifier")
      res = await self.db.run(
        "urn:users:providers:create_from_provider:1",
        {
          "provider": provider,
          "provider_identifier": provider_uid,
          "provider_email": provider_profile["email"],
          "provider_displayname": provider_profile["username"],
          "provider_profile_image": provider_profile.get("profilePicture"),
        },
      )
      user = res.rows[0] if res.rows else None
      if not user:
        res = await self.db.run(
          "urn:users:providers:get_by_provider_identifier:1",
          {"provider": provider, "provider_identifier": provider_uid},
        )
        user = res.rows[0] if res.rows else None
    if not user:
      raise HTTPException(status_code=500, detail="Unable to create user")

    new_img = provider_profile.get("profilePicture")
    if new_img and new_img != user.get("profile_image"):
      await self.db.run(
        "urn:users:profile:set_profile_image:1",
        {"guid": user["guid"], "image_b64": new_img, "provider": provider},
      )
      user["profile_image"] = new_img

    user_guid = user["guid"]
    rotation_token, rot_exp = self.auth.make_rotation_token(user_guid)
    now = datetime.now(timezone.utc)
    await self.db.run(
      "db:users:session:set_rotkey:1",
      {"guid": user_guid, "rotkey": rotation_token, "iat": now, "exp": rot_exp},
    )

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
    row = res.rows[0] if res.rows else {}
    session_guid = row.get("session_guid")
    device_guid = row.get("device_guid")
    session_token, _ = self.auth.make_session_token(
      user_guid, rotation_token, session_guid, device_guid, roles, exp=session_exp
    )
    await self.db.run(
      "db:auth:session:update_device_token:1",
      {"device_guid": device_guid, "access_token": session_token},
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
