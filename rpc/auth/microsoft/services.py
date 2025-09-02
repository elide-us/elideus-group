from datetime import datetime, timezone, timedelta
import base64, logging, uuid
import aiohttp

from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder

from rpc.helpers import unbox_request
from server.models import RPCResponse
from server.modules.auth_module import AuthModule
try:
  from server.modules.auth_module import DEFAULT_SESSION_TOKEN_EXPIRY
except Exception:
  DEFAULT_SESSION_TOKEN_EXPIRY = 15
from server.modules.db_module import DbModule
from .models import AuthMicrosoftOauthLogin1

MICROSOFT_TOKEN_ENDPOINT = "https://login.microsoftonline.com/consumers/oauth2/v2.0/token"


async def exchange_code_for_tokens(
  code: str,
  client_id: str,
  client_secret: str,
  redirect_uri: str = "http://localhost:8000/userpage",
) -> tuple[str, str]:
  data = {
    "client_id": client_id,
    "client_secret": client_secret,
    "code": code,
    "grant_type": "authorization_code",
    "redirect_uri": redirect_uri,
  }
  logging.debug(
    "[exchange_code_for_tokens] data=%s",
    {k: v for k, v in data.items() if k != "client_secret"}
  )
  logging.debug("[exchange_code_for_tokens] exchanging code for tokens")
  async with aiohttp.ClientSession() as session:
    async with session.post(MICROSOFT_TOKEN_ENDPOINT, data=data) as resp:
      if resp.status != 200:
        error = await resp.text()
        logging.error(
          "[exchange_code_for_tokens] failed status=%s error=%s", resp.status, error
        )
        raise HTTPException(status_code=400, detail="Failed to exchange authorization code")
      token_data = await resp.json()
  id_token = token_data.get("id_token")
  access_token = token_data.get("access_token")
  if not id_token or not access_token:
    logging.error("[exchange_code_for_tokens] missing tokens in response")
    raise HTTPException(status_code=400, detail="Invalid token response")
  return id_token, access_token


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


def normalize_provider_identifier(pid: str) -> str:
  try:
    return str(uuid.UUID(pid))
  except ValueError:
    try:
      pad = pid + "=" * (-len(pid) % 4)
      raw = base64.urlsafe_b64decode(pad)
      if len(raw) >= 16:
        return str(uuid.UUID(bytes=raw[-16:]))
    except Exception:
      pass
    return str(uuid.uuid5(uuid.NAMESPACE_URL, pid))


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
  session_exp = now + timedelta(minutes=DEFAULT_SESSION_TOKEN_EXPIRY)
  placeholder = uuid.uuid4().hex
  res = await db.run(
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
  session_token, _ = auth.make_session_token(
    user_guid, rotation_token, session_guid, device_guid, roles, exp=session_exp
  )
  await db.run(
    "db:auth:session:update_device_token:1",
    {"device_guid": device_guid, "access_token": session_token},
  )
  logging.debug(f"[create_session] session_token={session_token[:40]}")
  return session_token, session_exp, rotation_token, rot_exp


async def auth_microsoft_oauth_login_v1(request: Request):
  rpc_request, _, _ = await unbox_request(request)
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
  provider_uid = normalize_provider_identifier(provider_uid)
  logging.debug(
    f"[auth_microsoft_oauth_login_v1] provider_uid={provider_uid[:40] if provider_uid else None}"
  )

  identifiers = extract_identifiers(provider_uid, payload)
  user = await lookup_user(db, provider, identifiers)

  if not user or user.get("element_soft_deleted_at"):
    res = await db.run(
      f"urn:auth:{provider}:oauth_relink:1",
      {
        "provider_identifier": provider_uid,
        "email": profile["email"],
        "display_name": profile["username"],
        "profile_image": profile.get("profilePicture"),
        "confirm": req_payload.get("confirm"),
        "reauth_token": req_payload.get("reauthToken") or req_payload.get("reAuthToken"),
      },
    )
    user = res.rows[0] if res.rows else None

  if not user:
    logging.debug("[auth_microsoft_oauth_login_v1] user not found, creating new user")
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
  new_img = profile.get("profilePicture")
  if new_img != user.get("profile_image"):
    await db.run(
      "urn:users:profile:set_profile_image:1",
      {"guid": user_guid, "image_b64": new_img, "provider": provider},
    )
    user["profile_image"] = new_img
  if user.get("provider_name") == "microsoft":
    res_prof = await db.run(
      "urn:users:profile:update_if_unedited:1",
      {
        "guid": user_guid,
        "email": profile["email"],
        "display_name": profile["username"],
      },
    )
    if res_prof.rows:
      updated = res_prof.rows[0]
      if updated.get("display_name"):
        user["display_name"] = updated["display_name"]
      if updated.get("email"):
        user["email"] = updated["email"]
  fingerprint = req_payload.get("fingerprint")
  user_agent = request.headers.get("user-agent")
  ip_address = request.client.host if request.client else None
  session_token, session_exp, rotation_token, rot_exp = await create_session(
    auth, db, user_guid, provider, fingerprint, user_agent, ip_address
  )

  payload = AuthMicrosoftOauthLogin1(
    sessionToken=session_token,
    display_name=user["display_name"],
    credits=user["credits"],
    profile_image=user.get("profile_image"),
  )
  rpc_resp = RPCResponse(op=rpc_request.op, payload=payload.model_dump(), version=rpc_request.version)
  response = JSONResponse(content=jsonable_encoder(rpc_resp))
  response.set_cookie(
    "rotation_token",
    rotation_token,
    httponly=True,
    secure=True,
    samesite="lax",
    expires=rot_exp,
  )
  return response

