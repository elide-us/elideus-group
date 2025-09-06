from fastapi import HTTPException, Request

from rpc.helpers import unbox_request
from server.models import RPCResponse
from server.modules.storage_module import StorageModule
from server.modules.storage_cache_module import StorageCacheModule

from .models import (
  StorageFilesDeleteFiles1,
  StorageFilesFiles1,
  StorageFilesFileItem1,
  StorageFilesCreateFolder1,
  StorageFilesSetGallery1,
  StorageFilesMoveFile1,
  StorageFilesUploadFiles1,
)


async def storage_files_get_files_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  cache: StorageCacheModule = request.app.state.storage_cache
  files = await cache.list_user_files(auth_ctx.user_guid)
  payload = StorageFilesFiles1(files=[StorageFilesFileItem1(**f) for f in files])
  return RPCResponse(
    op=rpc_request.op,
    payload=payload.model_dump(),
    version=rpc_request.version,
  )


async def storage_files_upload_files_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  data = StorageFilesUploadFiles1(**(rpc_request.payload or {}))
  storage: StorageModule = request.app.state.storage
  await storage.upload_files(auth_ctx.user_guid, data.files)
  return RPCResponse(
    op=rpc_request.op,
    payload=data.model_dump(),
    version=rpc_request.version,
  )


async def storage_files_delete_files_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  data = StorageFilesDeleteFiles1(**(rpc_request.payload or {}))
  storage: StorageModule = request.app.state.storage
  await storage.delete_files(auth_ctx.user_guid, data.files)
  return RPCResponse(
    op=rpc_request.op,
    payload=data.model_dump(),
    version=rpc_request.version,
  )


async def storage_files_set_gallery_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  data = StorageFilesSetGallery1(**(rpc_request.payload or {}))
  storage: StorageModule = request.app.state.storage
  try:
    await storage.ensure_user_file(auth_ctx.user_guid, data.name)
  except FileNotFoundError:
    raise HTTPException(status_code=404, detail="File not found")
  return RPCResponse(
    op=rpc_request.op,
    payload=data.model_dump(),
    version=rpc_request.version,
  )


async def storage_files_create_folder_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  data = StorageFilesCreateFolder1(**(rpc_request.payload or {}))
  storage: StorageModule = request.app.state.storage
  await storage.create_folder(auth_ctx.user_guid, data.path)
  return RPCResponse(
    op=rpc_request.op,
    payload=data.model_dump(),
    version=rpc_request.version,
  )


async def storage_files_move_file_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  data = StorageFilesMoveFile1(**(rpc_request.payload or {}))
  storage: StorageModule = request.app.state.storage
  await storage.move_file(auth_ctx.user_guid, data.src, data.dst)
  return RPCResponse(
    op=rpc_request.op,
    payload=data.model_dump(),
    version=rpc_request.version,
  )


async def storage_files_refresh_cache_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  cache: StorageCacheModule = request.app.state.storage_cache
  files = await cache.refresh_user_cache(auth_ctx.user_guid)
  payload = StorageFilesFiles1(files=[StorageFilesFileItem1(**f) for f in files])
  return RPCResponse(
    op=rpc_request.op,
    payload=payload.model_dump(),
    version=rpc_request.version,
  )

