from fastapi import Request, HTTPException
from rpc.models import RPCRequest, RPCResponse
from rpc.frontend.files.models import FrontendFilesList1, FileItem, FrontendFileDelete1
from server.modules.auth_module import AuthModule
from server.modules.storage_module import StorageModule

async def list_files_v1(rpc_request: RPCRequest, request: Request) -> RPCResponse:
  payload = rpc_request.payload or {}
  token = payload.get('bearerToken')
  if not token:
    raise HTTPException(status_code=401, detail='Missing bearer token')
  auth: AuthModule = request.app.state.auth
  storage: StorageModule = request.app.state.storage
  data = await auth.decode_bearer_token(token)
  guid = data['guid']
  files = await storage.list_user_files(guid)
  items = [FileItem(name=f['name'], url=f['url'], contentType=f.get('content_type')) for f in files]
  payload = FrontendFilesList1(files=items)
  return RPCResponse(op='urn:frontend:files:list:1', payload=payload, version=1)

async def delete_file_v1(rpc_request: RPCRequest, request: Request) -> RPCResponse:
  payload = rpc_request.payload or {}
  token = payload.get('bearerToken')
  filename = payload.get('filename')
  if not token or filename is None:
    raise HTTPException(status_code=400, detail='Missing parameters')
  auth: AuthModule = request.app.state.auth
  storage: StorageModule = request.app.state.storage
  data = await auth.decode_bearer_token(token)
  guid = data['guid']
  await storage.delete_user_file(guid, filename)
  files = await storage.list_user_files(guid)
  items = [FileItem(name=f['name'], url=f['url'], contentType=f.get('content_type')) for f in files]
  payload = FrontendFilesList1(files=items)
  return RPCResponse(op='urn:frontend:files:delete:1', payload=payload, version=1)
