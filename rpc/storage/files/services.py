from fastapi import Request, HTTPException
from rpc.models import RPCRequest, RPCResponse
from rpc.storage.files.models import FrontendFilesList1, FileItem, FrontendFileDelete1, FrontendFileUpload1
from server.helpers.buffers import AsyncBufferWriter
import base64, re
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
  return RPCResponse(op='urn:storage:files:list:1', payload=payload, version=1)

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
  return RPCResponse(op='urn:storage:files:delete:1', payload=payload, version=1)

async def upload_file_v1(rpc_request: RPCRequest, request: Request) -> RPCResponse:
  data = FrontendFileUpload1(**(rpc_request.payload or {}))
  auth: AuthModule = request.app.state.auth
  storage: StorageModule = request.app.state.storage
  token_data = await auth.decode_bearer_token(data.bearerToken)
  guid = token_data['guid']

  m = re.match(r'^data:[^;]+;base64,(.*)$', data.dataUrl)
  if not m:
    raise HTTPException(status_code=400, detail='Invalid data URL')
  raw = base64.b64decode(m.group(1))
  async with AsyncBufferWriter(raw) as buf:
    await storage.write_buffer(buf, guid, data.filename, data.contentType)

  files = await storage.list_user_files(guid)
  items = [FileItem(name=f['name'], url=f['url'], contentType=f.get('content_type')) for f in files]
  payload = FrontendFilesList1(files=items)
  return RPCResponse(op='urn:storage:files:upload:1', payload=payload, version=1)
