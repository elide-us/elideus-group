from fastapi import Request

from rpc.helpers import unbox_request
from server.models import RPCResponse

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
  rpc_request, _, _ = await unbox_request(request)
  payload = StorageFilesFiles1(files=[])
  return RPCResponse(
    op=rpc_request.op,
    payload=payload.model_dump(),
    version=rpc_request.version,
  )


async def storage_files_upload_files_v1(request: Request):
  rpc_request, _, _ = await unbox_request(request)
  data = StorageFilesUploadFiles1(**(rpc_request.payload or {}))
  return RPCResponse(
    op=rpc_request.op,
    payload=data.model_dump(),
    version=rpc_request.version,
  )


async def storage_files_delete_files_v1(request: Request):
  rpc_request, _, _ = await unbox_request(request)
  data = StorageFilesDeleteFiles1(**(rpc_request.payload or {}))
  return RPCResponse(
    op=rpc_request.op,
    payload=data.model_dump(),
    version=rpc_request.version,
  )


async def storage_files_set_gallery_v1(request: Request):
  rpc_request, _, _ = await unbox_request(request)
  data = StorageFilesSetGallery1(**(rpc_request.payload or {}))
  return RPCResponse(
    op=rpc_request.op,
    payload=data.model_dump(),
    version=rpc_request.version,
  )


async def storage_files_create_folder_v1(request: Request):
  rpc_request, _, _ = await unbox_request(request)
  data = StorageFilesCreateFolder1(**(rpc_request.payload or {}))
  return RPCResponse(
    op=rpc_request.op,
    payload=data.model_dump(),
    version=rpc_request.version,
  )


async def storage_files_move_file_v1(request: Request):
  rpc_request, _, _ = await unbox_request(request)
  data = StorageFilesMoveFile1(**(rpc_request.payload or {}))
  return RPCResponse(
    op=rpc_request.op,
    payload=data.model_dump(),
    version=rpc_request.version,
  )

