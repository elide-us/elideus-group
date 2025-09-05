import base64, logging, uuid
import aiohttp
from datetime import datetime, timezone, timedelta

from fastapi import HTTPException, Request
from pydantic import ValidationError

from rpc.helpers import unbox_request
from server.models import RPCResponse
from server.modules.env_module import EnvModule
from server.modules.auth_module import AuthModule
try:
  from server.modules.auth_module import DEFAULT_SESSION_TOKEN_EXPIRY
except Exception:
  DEFAULT_SESSION_TOKEN_EXPIRY = 15
from server.modules.db_module import DbModule
from .models import AuthGoogleOauthLogin1, AuthGoogleOauthLoginPayload1
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder


GOOGLE_TOKEN_ENDPOINT = "https://oauth2.googleapis.com/token"


async def exchange_code_for_tokens(
  code: str,
  client_id: str,
  client_secret: str,
  redirect_uri: str = "http://localhost:8000/userpage",
) -> tuple[str, str]:
  data = {
    "code": code,
    "client_id": client_id,
    "client_secret": client_secret,
    "redirect_uri": redirect_uri,
    "grant_type": "authorization_code",
  }
  logging.debug(
    "[exchange_code_for_tokens] data=%s",
    {k: v for k, v in data.items() if k != "client_secret"}
  )
  logging.debug("[exchange_code_for_tokens] exchanging code for tokens")
  async with aiohttp.ClientSession() as session:
    async with session.post(GOOGLE_TOKEN_ENDPOINT, data=data) as resp:
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


def normalize_provider_identifier(pid: str) -> str:
  try:
    return str(uuid.UUID(pid))
  except ValueError:
    return str(uuid.uuid5(uuid.NAMESPACE_URL, pid))

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
  fingerprint: str,
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


async def auth_google_oauth_login_v1(request: Request):
  rpc_request, _, _ = await unbox_request(request)
  try:
    req_payload = AuthGoogleOauthLoginPayload1(**(rpc_request.payload or {}))
  except ValidationError as e:
    raise HTTPException(status_code=400, detail=str(e))

  provider = req_payload.provider
  code = req_payload.code
  confirm = req_payload.confirm
  reauth_token = req_payload.reauthToken or (rpc_request.payload or {}).get("reAuthToken")
  logging.debug(f"[auth_google_oauth_login_v1] provider={provider}")
  logging.debug(
    f"[auth_google_oauth_login_v1] code={code[:40] if code else None}"
  )

  env: EnvModule = request.app.state.env
  auth: AuthModule = request.app.state.auth
  db: DbModule = request.app.state.db

  # Get provider metadata
  google_provider = getattr(auth, "providers", {}).get("google")

  # Require Google client_id from provider config
  if not google_provider or not google_provider.audience:
      raise HTTPException(status_code=500, detail="Google OAuth client_id not configured")
  client_id = google_provider.audience

  # Acquire client_secret from environment
  client_secret = env.get("GOOGLE_AUTH_SECRET")
  if not client_secret:
    raise HTTPException(status_code=500, detail="GOOGLE_AUTH_SECRET not configured")

  # Require redirect_uri from system config
  res_redirect = await db.run("urn:system:config:get_config:1", {"key": "Hostname"})
  if not res_redirect.rows:
      raise HTTPException(status_code=500, detail="Google OAuth redirect URI not configured")
  redirect_uri = res_redirect.rows[0]["value"]
  logging.debug("[auth_google_oauth_login_v1] GoogleClientId=%s", client_id)
  logging.debug("[auth_google_oauth_login_v1] redirect_uri=%s", redirect_uri)

  id_token, access_token = await exchange_code_for_tokens(
    code, client_id, client_secret, redirect_uri
  )

  provider_uid, profile, payload = await auth.handle_auth_login(
    provider, id_token, access_token
  )
  provider_uid = normalize_provider_identifier(provider_uid)
  logging.debug(
    f"[auth_google_oauth_login_v1] provider_uid={provider_uid[:40] if provider_uid else None}"
  )

  identifiers = extract_identifiers(provider_uid, payload)
  user = await lookup_user(db, provider, identifiers)

  if user and user.get("element_soft_deleted_at"):
    res = await db.run(
      f"urn:auth:{provider}:oauth_relink:1",
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
    res = await db.run(
      "urn:users:providers:get_any_by_provider_identifier:1",
      {"provider": provider, "provider_identifier": provider_uid},
    )
    if res.rows:
      res2 = await db.run(
        f"urn:auth:{provider}:oauth_relink:1",
        {
          "provider_identifier": provider_uid,
          "email": profile["email"],
          "display_name": profile["username"],
          "profile_image": profile.get("profilePicture"),
          "confirm": confirm,
          "reauth_token": reauth_token,
        },
      )
      user = res2.rows[0] if res2.rows else None

  if not user:
    res = await db.run(
      f"urn:auth:{provider}:oauth_relink:1",
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
    logging.debug("[auth_google_oauth_login_v1] user not found, creating new user")
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
      logging.debug("[auth_google_oauth_login_v1] fetching user after creation")
      res = await db.run(
        "urn:users:providers:get_by_provider_identifier:1",
        {"provider": provider, "provider_identifier": provider_uid},
      )
      user = res.rows[0] if res.rows else None
    if not user:
      logging.debug("[auth_google_oauth_login_v1] failed to create user")
      raise HTTPException(status_code=500, detail="Unable to create user")

  user_guid = user["guid"]
  new_img = profile.get("profilePicture")
  if new_img and new_img != user.get("profile_image"):
    await db.run(
      "urn:users:profile:set_profile_image:1",
      {"guid": user_guid, "image_b64": new_img, "provider": provider},
    )
    user["profile_image"] = new_img
  if user.get("provider_name") == "google":
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
  fingerprint = req_payload.fingerprint
  user_agent = request.headers.get("user-agent")
  ip_address = request.client.host if request.client else None
  session_token, session_exp, rotation_token, rot_exp = await create_session(
    auth, db, user_guid, provider, fingerprint, user_agent, ip_address
  )

  payload = AuthGoogleOauthLogin1(
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
