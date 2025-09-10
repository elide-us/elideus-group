from fastapi import HTTPException, Request
from rpc.helpers import unbox_request
from server.models import RPCResponse
from typing import TYPE_CHECKING
if TYPE_CHECKING:
  from server.modules.public_users_module import PublicUsersModule
from .models import (
  PublicUsersProfile1,
  PublicUsersPublishedFile1,
  PublicUsersPublishedFiles1,
)

async def public_users_get_profile_v1(request: Request):
  rpc_request, _auth_ctx, _user_ctx = await unbox_request(request)
  payload = rpc_request.payload or {}
  guid = payload.get("guid")
  if not guid:
    raise HTTPException(status_code=400, detail="Missing user GUID")
  users_mod: PublicUsersModule = request.app.state.public_users
  row = await users_mod.get_profile(guid)
  if not row:
    raise HTTPException(status_code=404, detail="Profile not found")
  profile = PublicUsersProfile1(**row)
  return RPCResponse(
    op=rpc_request.op,
    payload=profile.model_dump(),
    version=rpc_request.version,
  )

async def public_users_get_published_files_v1(request: Request):
  rpc_request, _auth_ctx, _user_ctx = await unbox_request(request)
  payload = rpc_request.payload or {}
  guid = payload.get("guid")
  if not guid:
    raise HTTPException(status_code=400, detail="Missing user GUID")
  users_mod: PublicUsersModule = request.app.state.public_users
  rows = await users_mod.get_published_files(guid)
  files = [PublicUsersPublishedFile1(**r) for r in rows]
  payload_model = PublicUsersPublishedFiles1(files=files)
  return RPCResponse(
    op=rpc_request.op,
    payload=payload_model.model_dump(),
    version=rpc_request.version,
  )
