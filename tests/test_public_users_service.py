import sys, types, pathlib
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

# Stub rpc package
pkg = types.ModuleType('rpc')
pkg.__path__ = [str(pathlib.Path(__file__).resolve().parent.parent / 'rpc')]
sys.modules.setdefault('rpc', pkg)

# Stub server package with minimal models
server_pkg = types.ModuleType('server')
models_pkg = types.ModuleType('server.models')
from pydantic import BaseModel

class RPCRequest(BaseModel):
  op: str
  payload: dict | None = None
  version: int = 1

class RPCResponse(BaseModel):
  op: str
  payload: dict
  version: int = 1

models_pkg.RPCRequest = RPCRequest
models_pkg.RPCResponse = RPCResponse
server_pkg.models = models_pkg
sys.modules.setdefault('server', server_pkg)
sys.modules.setdefault('server.models', models_pkg)

from rpc.public.users.services import (
  public_users_get_profile_v1,
  public_users_get_published_files_v1,
)

class DummyPublicUsersModule:
  async def get_profile(self, guid: str):
    assert guid == '123'
    return {'display_name': 'Alice', 'email': 'alice@example.com', 'profile_image': 'abc'}

  async def get_published_files(self, guid: str):
    assert guid == '123'
    return [{'path': '/a', 'filename': 'file.txt'}]

app = FastAPI()
app.state.public_users = DummyPublicUsersModule()

@app.post('/rpc')
async def rpc_endpoint(request: Request):
  body = await request.json()
  if body['op'] == 'urn:public:users:get_profile:1':
    return await public_users_get_profile_v1(request)
  if body['op'] == 'urn:public:users:get_published_files:1':
    return await public_users_get_published_files_v1(request)
  raise AssertionError('unexpected op')

client = TestClient(app)

def test_get_profile_service():
  resp = client.post('/rpc', json={'op': 'urn:public:users:get_profile:1', 'payload': {'guid': '123'}})
  assert resp.status_code == 200
  data = resp.json()
  assert data['payload'] == {
    'display_name': 'Alice',
    'email': 'alice@example.com',
    'profile_image': 'abc',
  }

def test_get_published_files_service():
  resp = client.post('/rpc', json={'op': 'urn:public:users:get_published_files:1', 'payload': {'guid': '123'}})
  assert resp.status_code == 200
  data = resp.json()
  assert data['payload'] == {
    'files': [{'path': '/a', 'filename': 'file.txt'}]
  }
