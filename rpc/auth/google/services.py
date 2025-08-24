from datetime import datetime, timezone
import base64, logging, uuid, os
import aiohttp

from fastapi import HTTPException, Request
from pydantic import ValidationError

from rpc.helpers import unbox_request
from rpc.models import RPCResponse
from server.modules.auth_module import AuthModule
from server.modules.db_module import DbModule
from .models import AuthGoogleOauthLogin1, AuthGoogleOauthLoginPayload1


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
      "provider": provider,
    },
  )
  return session_token, session_exp


async def auth_google_oauth_login_v1(request: Request):
  rpc_request, _, _ = await unbox_request(request)
  try:
    req_payload = AuthGoogleOauthLoginPayload1(**(rpc_request.payload or {}))
  except ValidationError as e:
    raise HTTPException(status_code=400, detail=str(e))

  provider = req_payload.provider
  code = req_payload.code
  logging.debug(f"[auth_google_oauth_login_v1] provider={provider}")
  logging.debug(
    f"[auth_google_oauth_login_v1] code={code[:40] if code else None}"
  )

  auth: AuthModule = request.app.state.auth
  db: DbModule = request.app.state.db

  # Get provider metadata
  google_provider = getattr(auth, "providers", {}).get("google")

  # Require Google client_id from provider config
  if not google_provider or not google_provider.audience:
      raise HTTPException(status_code=500, detail="Google OAuth client_id not configured")
  client_id = google_provider.audience

  # Require client_secret from system config
  try:
    client_secret = await db.get_google_api_secret()
  except ValueError:
    raise HTTPException(status_code=500, detail="Google OAuth client_secret not configured")

  # Require redirect_uri from system config
  res_redirect = await db.run("urn:system:config:get_config:1", {"key": "GoogleAuthRedirectLocalhost"})
  if not res_redirect.rows:
      raise HTTPException(status_code=500, detail="Google OAuth redirect URI not configured")
  redirect_uri = res_redirect.rows[0]["value"]
  logging.debug("[auth_google_oauth_login_v1] GoogleApiId=%s", client_id)
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

  if not user:
    logging.debug("[auth_google_oauth_login_v1] user not found, creating new user")
    res = await db.run(
      "urn:users:providers:get_user_by_email:1",
      {"email": profile["email"]},
    )
    if res.rows:
      logging.debug("[auth_google_oauth_login_v1] email already registered")
      raise HTTPException(status_code=409, detail="Email already registered")
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

  new_img = profile.get("profilePicture")
  if new_img and new_img != user.get("profile_image"):
    await db.run(
      "urn:users:profile:set_profile_image:1",
      {"guid": user["guid"], "image_b64": new_img, "provider": provider},
    )
    user["profile_image"] = new_img

  user_guid = user["guid"]
  fingerprint = req_payload.fingerprint
  user_agent = request.headers.get("user-agent")
  ip_address = request.client.host if request.client else None
  session_token, session_exp = await create_session(
    auth, db, user_guid, provider, fingerprint, user_agent, ip_address
  )

  payload = AuthGoogleOauthLogin1(
    sessionToken=session_token,
    display_name=user["display_name"],
    credits=user["credits"],
    profile_image=user.get("profile_image"),
  )
  return RPCResponse(op=rpc_request.op, payload=payload.model_dump(), version=rpc_request.version)
