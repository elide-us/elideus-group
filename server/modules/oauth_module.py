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

TOKEN_ENDPOINTS = {
  "google": "https://oauth2.googleapis.com/token",
  "microsoft": "https://login.microsoftonline.com/consumers/oauth2/v2.0/token",
}

class OauthModule(BaseModule):
  def __init__(self, app: FastAPI):
    super().__init__(app)

  async def startup(self):
    self.mark_ready()

  async def shutdown(self):
    pass

async def exchange_code_for_tokens(
  code: str,
  client_id: str,
  client_secret: str,
  redirect_uri: str,
  token_endpoint: str = TOKEN_ENDPOINTS["google"],
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
  if not id_token or not access_token:
    logging.error("[exchange_code_for_tokens] missing tokens in response")
    raise HTTPException(status_code=400, detail="Invalid token response")
  return id_token, access_token

def extract_identifiers(
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
    user_guid, rotation_token, session_guid, device_guid, roles, exp=session_exp,
  )
  await db.run(
    "db:auth:session:update_device_token:1",
    {"device_guid": device_guid, "access_token": session_token},
  )
  logging.debug(f"[create_session] session_token={session_token[:40]}")
  return session_token, session_exp, rotation_token, rot_exp
