from fastapi import HTTPException, Request

from rpc.helpers import get_rpcrequest_from_request
from rpc.models import RPCResponse
from server.modules.db_module import DbModule
from .models import (
  UsersProfileProfile1,
  UsersProfileSetDisplay1,
  UsersProfileSetOptin1,
)


async def users_profile_get_profile_v1(request: Request):
  rpc_request, auth_ctx, _ = await get_rpcrequest_from_request(request)
  if not auth_ctx.user_guid:
    raise HTTPException(status_code=401, detail="Unauthorized")

  db: DbModule = request.app.state.db
  res = await db.run(rpc_request.op, {"guid": auth_ctx.user_guid})
  if not res.rows:
    raise HTTPException(status_code=404, detail="Profile not found")

  profile = UsersProfileProfile1(**res.rows[0])
  return RPCResponse(
    op=rpc_request.op,
    payload=profile.model_dump(),
    version=rpc_request.version,
  )

async def users_profile_set_display_v1(request: Request):
  rpc_request, auth_ctx, _ = await get_rpcrequest_from_request(request)
  if not auth_ctx.user_guid:
    raise HTTPException(status_code=401, detail="Unauthorized")

  payload = UsersProfileSetDisplay1(**(rpc_request.payload or {}))
  db: DbModule = request.app.state.db
  await db.run(rpc_request.op, {
    "guid": auth_ctx.user_guid,
    "display_name": payload.display_name,
  })
  return RPCResponse(
    op=rpc_request.op,
    payload=payload.model_dump(),
    version=rpc_request.version,
  )

async def users_profile_set_optin_v1(request: Request):
  rpc_request, auth_ctx, _ = await get_rpcrequest_from_request(request)
  if not auth_ctx.user_guid:
    raise HTTPException(status_code=401, detail="Unauthorized")

  payload = UsersProfileSetOptin1(**(rpc_request.payload or {}))
  db: DbModule = request.app.state.db
  await db.run(rpc_request.op, {
    "guid": auth_ctx.user_guid,
    "display_email": payload.display_email,
  })
  return RPCResponse(
    op=rpc_request.op,
    payload=payload.model_dump(),
    version=rpc_request.version,
  )

async def users_profile_get_roles_v1(request: Request):
  raise NotImplementedError("urn:users:profile:get_roles:1")

async def users_profile_set_roles_v1(request: Request):
  raise NotImplementedError("urn:users:profile:set_roles:1")

async def users_profile_set_profile_image_v1(request: Request):
  raise NotImplementedError("urn:users:profile:set_profile_image:1")

