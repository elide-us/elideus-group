from fastapi import HTTPException, Request

from rpc.helpers import unbox_request
from server.models import RPCResponse
from server.modules.db_module import DbModule
from .models import (
  UsersProfileProfile1,
  UsersProfileSetDisplay1,
  UsersProfileSetOptin1,
  UsersProfileRoles1,
  UsersProfileSetProfileImage1,
)


"""User profile service helpers.

`auth_ctx.user_guid` is populated for authenticated RPC requests. These
functions assume this GUID exists, and raise a validation error if the
GUID is missing.
"""


async def users_profile_get_profile_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  user_guid = auth_ctx.user_guid
  if user_guid is None:
    raise HTTPException(status_code=400, detail="Missing user GUID")

  db: DbModule = request.app.state.db
  res = await db.run(rpc_request.op, {"guid": user_guid})
  if not res.rows:
    raise HTTPException(status_code=404, detail="Profile not found")
  row = res.rows[0]
  row["guid"] = str(row.get("guid", ""))
  auth_providers = row.get("auth_providers")
  if isinstance(auth_providers, str):
    import json
    row["auth_providers"] = json.loads(auth_providers) if auth_providers else []
  profile = UsersProfileProfile1(**row)
  return RPCResponse(
    op=rpc_request.op,
    payload=profile.model_dump(),
    version=rpc_request.version,
  )

async def users_profile_set_display_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  user_guid = auth_ctx.user_guid
  if user_guid is None:
    raise HTTPException(status_code=400, detail="Missing user GUID")

  payload = UsersProfileSetDisplay1(**(rpc_request.payload or {}))
  db: DbModule = request.app.state.db
  await db.run(rpc_request.op, {
    "guid": user_guid,
    "display_name": payload.display_name,
  })
  return RPCResponse(
    op=rpc_request.op,
    payload=payload.model_dump(),
    version=rpc_request.version,
  )

async def users_profile_set_optin_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  user_guid = auth_ctx.user_guid
  if user_guid is None:
    raise HTTPException(status_code=400, detail="Missing user GUID")

  payload = UsersProfileSetOptin1(**(rpc_request.payload or {}))
  db: DbModule = request.app.state.db
  await db.run(rpc_request.op, {
    "guid": user_guid,
    "display_email": payload.display_email,
  })
  return RPCResponse(
    op=rpc_request.op,
    payload=payload.model_dump(),
    version=rpc_request.version,
  )

async def users_profile_get_roles_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  user_guid = auth_ctx.user_guid
  if user_guid is None:
    raise HTTPException(status_code=400, detail="Missing user GUID")

  db: DbModule = request.app.state.db
  res = await db.run(rpc_request.op, {"guid": user_guid})
  roles = int(res.rows[0].get("element_roles", 0)) if res.rows else 0
  payload = UsersProfileRoles1(roles=roles)
  return RPCResponse(
    op=rpc_request.op,
    payload=payload.model_dump(),
    version=rpc_request.version,
  )

async def users_profile_set_profile_image_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  user_guid = auth_ctx.user_guid
  if user_guid is None:
    raise HTTPException(status_code=400, detail="Missing user GUID")

  payload = UsersProfileSetProfileImage1(**(rpc_request.payload or {}))
  db: DbModule = request.app.state.db
  await db.run(rpc_request.op, {
    "guid": user_guid,
    "image_b64": payload.image_b64,
    "provider": payload.provider,
  })
  return RPCResponse(
    op=rpc_request.op,
    payload=payload.model_dump(),
    version=rpc_request.version,
  )

