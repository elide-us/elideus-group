from datetime import datetime, timezone

from fastapi import HTTPException, Request

from rpc.auth.session.models import AuthSessionAuthTokens, AuthSessionSessionToken
from rpc.helpers import get_rpcrequest_from_request
from rpc.models import RPCResponse
from server.modules.auth_module import AuthModule
from server.modules.authz_module import AuthzModule
from server.modules.db_module import DbModule


async def auth_microsoft_oauth_login_v1(request: Request):
  rpc_request, _, _ = await get_rpcrequest_from_request(request)
  req_payload = rpc_request.payload or {}

  provider = req_payload.get("provider", "microsoft")
  id_token = req_payload.get("idToken") or req_payload.get("id_token")
  access_token = req_payload.get("accessToken") or req_payload.get("access_token")
  if not id_token or not access_token:
    raise HTTPException(status_code=400, detail="Missing credentials")

  auth: AuthModule = request.app.state.auth
  db: DbModule = request.app.state.db

  provider_uid, profile, payload = await auth.handle_auth_login(provider, id_token, access_token)

  identifiers = []
  oid = payload.get("oid")
  sub = payload.get("sub")
  if oid:
    identifiers.append(oid)
  if sub and sub not in identifiers:
    identifiers.append(sub)

  user = None
  for pid in identifiers:
    res = await db.run(
      "urn:users:providers:get_by_provider_identifier:1",
      {"provider": provider, "provider_identifier": pid},
    )
    if res.rows:
      user = res.rows[0]
      break

  if not user:
    res = await db.run(
      "urn:users:providers:create_from_provider:1",
      {
        "provider": provider,
        "provider_identifier": provider_uid,
        "provider_email": profile["email"],
        "provider_displayname": profile["username"],
      },
    )
    user = res.rows[0] if res.rows else None
  if not user:
    raise HTTPException(status_code=500, detail="Unable to create user")

  user_guid = user["guid"]

  if profile.get("profilePicture"):
    await db.run(
      "urn:users:profile:set_profile_image:1",
      {"guid": user_guid, "image_b64": profile["profilePicture"], "provider": provider},
    )
  rotation_token, rot_exp = auth.make_rotation_token(user_guid)
  now = datetime.now(timezone.utc)
  await db.run(
    "db:users:session:set_rotkey:1",
    {"guid": user_guid, "rotkey": rotation_token, "iat": now, "exp": rot_exp},
  )

  roles_res = await db.run("urn:users:profile:get_roles:1", {"guid": user_guid})
  role_mask = int(roles_res.rows[0].get("element_roles", 0)) if roles_res.rows else 0
  authz: AuthzModule = request.app.state.authz
  roles = authz.mask_to_names(role_mask)

  bearer = auth.make_session_token(user_guid, rotation_token, roles, provider)
  session_claims = await auth.decode_session_token(bearer)

  payload = AuthSessionAuthTokens(bearerToken=bearer, session=AuthSessionSessionToken(**session_claims))
  return RPCResponse(op=rpc_request.op, payload=payload.model_dump(), version=rpc_request.version)

