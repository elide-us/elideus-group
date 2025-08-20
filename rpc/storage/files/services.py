import base64
import io

from fastapi import HTTPException, Request

from rpc.helpers import get_rpcrequest_from_request
from rpc.models import RPCResponse
from server.modules.storage_module import StorageModule

from .models import (
  StorageFilesDeleteFiles1,
  StorageFilesFiles1,
  StorageFilesFileItem1,
  StorageFilesSetGallery1,
  StorageFilesUploadFiles1,
)


async def storage_files_get_files_v1(request: Request):
  rpc_request, auth_ctx, _ = await get_rpcrequest_from_request(request)
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

