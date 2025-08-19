import base64
import io
import logging

from fastapi import HTTPException, Request

from rpc.helpers import get_rpcrequest_from_request
from rpc.models import RPCResponse
from server.modules.storage_module import StorageModule
from server.modules.auth_module import AuthModule

from .models import (
  StorageFilesDeleteFiles1,
  StorageFilesFiles1,
  StorageFilesFileItem1,
  StorageFilesSetGallery1,
  StorageFilesUploadFiles1,
)


def _require_storage_role(auth_ctx, request: Request):
  auth: AuthModule = request.app.state.auth
  required_mask = auth.roles.get("ROLE_STORAGE_ENABLED", 0)
  expected_mask = 0x0000000000000002
  has_role = (auth_ctx.role_mask & required_mask) == required_mask
  logging.debug(
    "[Storage] user roles=%s mask=%#018x required_mask=%#018x (ROLE_STORAGE_ENABLED expected %#018x) has_role=%s",
    auth_ctx.roles,
    auth_ctx.role_mask,
    required_mask,
    expected_mask,
    has_role,
  )
  if not has_role:
    raise HTTPException(status_code=403, detail="Forbidden")


async def storage_files_get_files_v1(request: Request):
  rpc_request, auth_ctx, _ = await get_rpcrequest_from_request(request)
  _require_storage_role(auth_ctx, request)
  storage: StorageModule = request.app.state.storage
  files = await storage.list_user_files(auth_ctx.user_guid)
  payload = StorageFilesFiles1(files=[StorageFilesFileItem1(**f) for f in files])
  return RPCResponse(
    op=rpc_request.op,
    payload=payload.model_dump(),
    version=rpc_request.version,
  )


async def storage_files_upload_files_v1(request: Request):
  rpc_request, auth_ctx, _ = await get_rpcrequest_from_request(request)
  _require_storage_role(auth_ctx, request)
  data = StorageFilesUploadFiles1(**(rpc_request.payload or {}))
  storage: StorageModule = request.app.state.storage
  await storage.ensure_user_folder(auth_ctx.user_guid)
  for item in data.files:
    buffer = io.BytesIO(base64.b64decode(item.content_b64))
    await storage.write_buffer(buffer, auth_ctx.user_guid, item.name, item.content_type)
  return RPCResponse(
    op=rpc_request.op,
    payload=data.model_dump(),
    version=rpc_request.version,
  )


async def storage_files_delete_files_v1(request: Request):
  rpc_request, auth_ctx, _ = await get_rpcrequest_from_request(request)
  _require_storage_role(auth_ctx, request)
  data = StorageFilesDeleteFiles1(**(rpc_request.payload or {}))
  storage: StorageModule = request.app.state.storage
  for name in data.files:
    await storage.delete_user_file(auth_ctx.user_guid, name)
  return RPCResponse(
    op=rpc_request.op,
    payload=data.model_dump(),
    version=rpc_request.version,
  )


async def storage_files_set_gallery_v1(request: Request):
  rpc_request, auth_ctx, _ = await get_rpcrequest_from_request(request)
  _require_storage_role(auth_ctx, request)
  data = StorageFilesSetGallery1(**(rpc_request.payload or {}))
  storage: StorageModule = request.app.state.storage
  files = await storage.list_user_files(auth_ctx.user_guid)
  if not any(f.get("name") == data.name for f in files):
    raise HTTPException(status_code=404, detail="File not found")
  return RPCResponse(
    op=rpc_request.op,
    payload=data.model_dump(),
    version=rpc_request.version,
  )

