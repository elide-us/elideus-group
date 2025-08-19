from datetime import datetime, timezone
import base64, logging, uuid

from fastapi import HTTPException, Request

from rpc.helpers import get_rpcrequest_from_request
from rpc.models import RPCResponse
from server.modules.auth_module import AuthModule
from server.modules.db_module import DbModule
from .models import AuthMicrosoftOauthLogin1


def extract_identifiers(provider_uid: str | None, payload: dict) -> list[str]:
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
    except Exception as e:
      logging.exception(
        f"[extract_identifiers] home_account_id generation failed for {base_id}: {e}"
      )
    else:
      if home_account_id not in identifiers:
        identifiers.append(home_account_id)
      logging.debug(
        f"[extract_identifiers] home_account_id={home_account_id[:40]}"
      )
  return identifiers


async def lookup_user(db: DbModule, provider: str, identifiers: list[str]):
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
    res = await db.run(
      "urn:users:providers:get_by_provider_identifier:1",
      {"provider": provider, "provider_identifier": uid},
    )
    if res.rows:
      logging.debug(f"[lookup_user] user found with identifier={pid[:40]}")
      return res.rows[0]
  return None


async def create_session(
  auth: AuthModule,
  db: DbModule,
  user_guid: str,
  provider: str,
  fingerprint: str | None,
  user_agent: str | None,
  ip_address: str | None,
):
  rotation_token, rot_exp = auth.make_rotation_token(user_guid)
  logging.debug(f"[create_session] rotation_token={rotation_token[:40]}")
  now = datetime.now(timezone.utc)
  await db.run(
    "db:users:session:set_rotkey:1",
    {"guid": user_guid, "rotkey": rotation_token, "iat": now, "exp": rot_exp},
  )
  roles, _ = await auth.get_user_roles(user_guid)
  session_token, session_exp = auth.make_session_token(
    user_guid, rotation_token, roles, provider
  )
  logging.debug(f"[create_session] session_token={session_token[:40]}")
  await db.run(
    "db:auth:session:create_session:1",
    {
      "access_token": session_token,
      "expires": session_exp,
      "fingerprint": fingerprint,
      "user_agent": user_agent,
      "ip_address": ip_address,
      "user_guid": user_guid,
    },
  )
  return session_token, session_exp


async def auth_microsoft_oauth_login_v1(request: Request):
  rpc_request, _, _ = await get_rpcrequest_from_request(request)
  req_payload = rpc_request.payload or {}

  provider = req_payload.get("provider", "microsoft")
  id_token = req_payload.get("idToken") or req_payload.get("id_token")
  access_token = req_payload.get("accessToken") or req_payload.get("access_token")
  logging.debug(f"[auth_microsoft_oauth_login_v1] provider={provider}")
  logging.debug(
    f"[auth_microsoft_oauth_login_v1] id_token={id_token[:40] if id_token else None}"
  )
  logging.debug(
    f"[auth_microsoft_oauth_login_v1] access_token={access_token[:40] if access_token else None}"
  )
  if not id_token or not access_token:
    raise HTTPException(status_code=400, detail="Missing credentials")

  auth: AuthModule = request.app.state.auth
  db: DbModule = request.app.state.db

  provider_uid, profile, payload = await auth.handle_auth_login(
    provider, id_token, access_token
  )
  logging.debug(
    f"[auth_microsoft_oauth_login_v1] provider_uid={provider_uid[:40] if provider_uid else None}"
  )

  identifiers = extract_identifiers(provider_uid, payload)
  user = await lookup_user(db, provider, identifiers)

  if not user:
    logging.debug("[auth_microsoft_oauth_login_v1] user not found, creating new user")
    try:
      provider_uid = str(uuid.UUID(provider_uid))
    except ValueError:
      raise HTTPException(status_code=400, detail="Invalid provider identifier")
    res = await db.run(
      "urn:users:providers:create_from_provider:1",
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
      logging.debug("[auth_microsoft_oauth_login_v1] fetching user after creation")
      res = await db.run(
        "urn:users:providers:get_by_provider_identifier:1",
        {"provider": provider, "provider_identifier": provider_uid},
      )
      user = res.rows[0] if res.rows else None
  if not user:
    logging.debug("[auth_microsoft_oauth_login_v1] failed to create user")
    raise HTTPException(status_code=500, detail="Unable to create user")

  user_guid = user["guid"]
  fingerprint = req_payload.get("fingerprint")
  user_agent = request.headers.get("user-agent")
  ip_address = request.client.host if request.client else None
  session_token, session_exp = await create_session(
    auth, db, user_guid, provider, fingerprint, user_agent, ip_address
  )

  payload = AuthMicrosoftOauthLogin1(
    sessionToken=session_token,
    display_name=user["display_name"],
    credits=user["credits"],
    profile_image=user.get("profile_image"),
  )
  return RPCResponse(op=rpc_request.op, payload=payload.model_dump(), version=rpc_request.version)

