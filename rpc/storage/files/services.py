from fastapi import HTTPException, Request

from rpc.helpers import unbox_request
from server.models import RPCResponse
from server.modules.storage_module import StorageModule

from .models import (
  StorageFilesDeleteFiles1,
  StorageFilesFiles1,
  StorageFilesFileItem1,
  StorageFilesCreateFolder1,
  StorageFilesSetGallery1,
  StorageFilesMoveFile1,
  StorageFilesUploadFiles1,
  StorageFilesGetLink1,
  StorageFilesGetFolderFiles1,
  StorageFilesDeleteFolder1,
  StorageFilesCreateUserFolder1,
  StorageFilesRenameFile1,
  StorageFilesGetMetadata1,
  StorageFilesFileMetadata1,
  StorageFilesUsageItem1,
  StorageFilesUsage1,
)


async def storage_files_get_files_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  user_guid = auth_ctx.user_guid
  if user_guid is None:
    raise HTTPException(status_code=400, detail="Missing user GUID")
  storage: StorageModule = request.app.state.storage
  files = await storage.list_files_by_user(user_guid)
  items = [StorageFilesFileItem1(**f) for f in files]
  payload = StorageFilesFiles1(files=items)
  await storage.reindex(user_guid)
  return RPCResponse(
    op=rpc_request.op,
    payload=payload.model_dump(),
    version=rpc_request.version,
  )


async def storage_files_upload_files_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  user_guid = auth_ctx.user_guid
  if user_guid is None:
    raise HTTPException(status_code=400, detail="Missing user GUID")
  data = StorageFilesUploadFiles1(**(rpc_request.payload or {}))
  storage: StorageModule = request.app.state.storage
  await storage.upload_files(user_guid, data.files)
  await storage.reindex(user_guid)
  return RPCResponse(
    op=rpc_request.op,
    payload=data.model_dump(),
    version=rpc_request.version,
  )


async def storage_files_delete_files_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  user_guid = auth_ctx.user_guid
  if user_guid is None:
    raise HTTPException(status_code=400, detail="Missing user GUID")
  data = StorageFilesDeleteFiles1(**(rpc_request.payload or {}))
  storage: StorageModule = request.app.state.storage
  await storage.delete_files(user_guid, data.files)
  await storage.reindex(user_guid)
  return RPCResponse(
    op=rpc_request.op,
    payload=data.model_dump(),
    version=rpc_request.version,
  )


async def storage_files_set_gallery_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  user_guid = auth_ctx.user_guid
  if user_guid is None:
    raise HTTPException(status_code=400, detail="Missing user GUID")
  data = StorageFilesSetGallery1(**(rpc_request.payload or {}))
  storage: StorageModule = request.app.state.storage
  await storage.set_gallery(user_guid, data.name, data.gallery)
  await storage.reindex(user_guid)
  return RPCResponse(
    op=rpc_request.op,
    payload=data.model_dump(),
    version=rpc_request.version,
  )


async def storage_files_create_folder_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  user_guid = auth_ctx.user_guid
  if user_guid is None:
    raise HTTPException(status_code=400, detail="Missing user GUID")
  data = StorageFilesCreateFolder1(**(rpc_request.payload or {}))
  storage: StorageModule = request.app.state.storage
  await storage.create_folder(user_guid, data.path)
  await storage.reindex(user_guid)
  return RPCResponse(
    op=rpc_request.op,
    payload=data.model_dump(),
    version=rpc_request.version,
  )


async def storage_files_move_file_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  user_guid = auth_ctx.user_guid
  if user_guid is None:
    raise HTTPException(status_code=400, detail="Missing user GUID")
  data = StorageFilesMoveFile1(**(rpc_request.payload or {}))
  storage: StorageModule = request.app.state.storage
  await storage.move_file(user_guid, data.src, data.dst)
  await storage.reindex(user_guid)
  return RPCResponse(
    op=rpc_request.op,
    payload=data.model_dump(),
    version=rpc_request.version,
  )


async def storage_files_rename_file_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  user_guid = auth_ctx.user_guid
  if user_guid is None:
    raise HTTPException(status_code=400, detail="Missing user GUID")
  data = StorageFilesRenameFile1(**(rpc_request.payload or {}))
  storage: StorageModule = request.app.state.storage
  await storage.rename_file(user_guid, data.old_name, data.new_name)
  await storage.reindex(user_guid)
  return RPCResponse(
    op=rpc_request.op,
    payload=data.model_dump(),
    version=rpc_request.version,
  )


async def storage_files_get_link_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  user_guid = auth_ctx.user_guid
  if user_guid is None:
    raise HTTPException(status_code=400, detail="Missing user GUID")
  data = StorageFilesGetLink1(**(rpc_request.payload or {}))
  storage: StorageModule = request.app.state.storage
  url = await storage.get_file_link(user_guid, data.name)
  item = StorageFilesFileItem1(name=data.name, url=url)
  await storage.reindex(user_guid)
  return RPCResponse(
    op=rpc_request.op,
    payload=item.model_dump(),
    version=rpc_request.version,
  )


async def storage_files_get_metadata_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  user_guid = auth_ctx.user_guid
  if user_guid is None:
    raise HTTPException(status_code=400, detail="Missing user GUID")
  data = StorageFilesGetMetadata1(**(rpc_request.payload or {}))
  storage: StorageModule = request.app.state.storage
  meta = await storage.get_file_metadata(user_guid, data.name)
  item = StorageFilesFileMetadata1(**meta)
  await storage.reindex(user_guid)
  return RPCResponse(
    op=rpc_request.op,
    payload=item.model_dump(),
    version=rpc_request.version,
  )


async def storage_files_get_folder_files_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  user_guid = auth_ctx.user_guid
  if user_guid is None:
    raise HTTPException(status_code=400, detail="Missing user GUID")
  data = StorageFilesGetFolderFiles1(**(rpc_request.payload or {}))
  storage: StorageModule = request.app.state.storage
  files = await storage.list_files_by_folder(user_guid, data.path)
  items = [StorageFilesFileItem1(**f) for f in files]
  payload = StorageFilesFiles1(files=items)
  await storage.reindex(user_guid)
  return RPCResponse(
    op=rpc_request.op,
    payload=payload.model_dump(),
    version=rpc_request.version,
  )


async def storage_files_delete_folder_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  user_guid = auth_ctx.user_guid
  if user_guid is None:
    raise HTTPException(status_code=400, detail="Missing user GUID")
  data = StorageFilesDeleteFolder1(**(rpc_request.payload or {}))
  storage: StorageModule = request.app.state.storage
  await storage.delete_folder(user_guid, data.path)
  await storage.reindex(user_guid)
  return RPCResponse(
    op=rpc_request.op,
    payload=data.model_dump(),
    version=rpc_request.version,
  )


async def storage_files_create_user_folder_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  user_guid = auth_ctx.user_guid
  if user_guid is None:
    raise HTTPException(status_code=400, detail="Missing user GUID")
  data = StorageFilesCreateUserFolder1(**(rpc_request.payload or {}))
  storage: StorageModule = request.app.state.storage
  await storage.create_user_folder(user_guid, data.path)
  await storage.reindex(user_guid)
  return RPCResponse(
    op=rpc_request.op,
    payload=data.model_dump(),
    version=rpc_request.version,
  )


async def storage_files_get_usage_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  user_guid = auth_ctx.user_guid
  if user_guid is None:
    raise HTTPException(status_code=400, detail="Missing user GUID")
  storage: StorageModule = request.app.state.storage
  usage = await storage.get_usage(user_guid)
  items = [StorageFilesUsageItem1(**u) for u in usage.get("by_type", [])]
  payload = StorageFilesUsage1(total_size=usage.get("total_size", 0), by_type=items)
  await storage.reindex(user_guid)
  return RPCResponse(
    op=rpc_request.op,
    payload=payload.model_dump(),
    version=rpc_request.version,
  )


async def storage_files_get_public_files_v1(request: Request):
  rpc_request, _, _ = await unbox_request(request)
  storage: StorageModule = request.app.state.storage
  files = await storage.list_public_files()
  items = [StorageFilesFileItem1(**f) for f in files]
  payload = StorageFilesFiles1(files=items)
  await storage.reindex()
  return RPCResponse(
    op=rpc_request.op,
    payload=payload.model_dump(),
    version=rpc_request.version,
  )


async def storage_files_get_moderation_files_v1(request: Request):
  rpc_request, _, _ = await unbox_request(request)
  storage: StorageModule = request.app.state.storage
  files = await storage.list_flagged_for_moderation()
  items = [StorageFilesFileItem1(**f) for f in files]
  payload = StorageFilesFiles1(files=items)
  await storage.reindex()
  return RPCResponse(
    op=rpc_request.op,
    payload=payload.model_dump(),
    version=rpc_request.version,
  )

