from __future__ import annotations

from fastapi import HTTPException, Request
from rpc.helpers import unbox_request
from server.models import RPCResponse
from typing import TYPE_CHECKING
if TYPE_CHECKING:
  from server.modules.public_users_module import PublicUsersModule
from .models import (
  PublicUsersGetProfileRequest1,
  PublicUsersGetPublishedFilesRequest1,
  PublicUsersProfile1,
  PublicUsersPublishedFile1,
  PublicUsersPublishedFiles1,
)


async def public_users_get_profile_v1(request: Request):
  rpc_request, _auth_ctx, _user_ctx = await unbox_request(request)
  input_payload = PublicUsersGetProfileRequest1(**(rpc_request.payload or {}))
  module: PublicUsersModule = request.app.state.public_users
  row = await module.get_profile(input_payload.guid)
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
  input_payload = PublicUsersGetPublishedFilesRequest1(**(rpc_request.payload or {}))
  module: PublicUsersModule = request.app.state.public_users
  rows = await module.get_published_files(input_payload.guid)
  files = [PublicUsersPublishedFile1(**r) for r in rows]
  payload_model = PublicUsersPublishedFiles1(files=files)
  return RPCResponse(
    op=rpc_request.op,
    payload=payload_model.model_dump(),
    version=rpc_request.version,
  )
