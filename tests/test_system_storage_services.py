import types, sys, pathlib
from fastapi import FastAPI
from fastapi.testclient import TestClient
from starlette.requests import Request
from types import SimpleNamespace
from pydantic import BaseModel

# stub rpc package
pkg = types.ModuleType('rpc')
pkg.__path__ = [str(pathlib.Path(__file__).resolve().parent.parent / 'rpc')]
sys.modules.setdefault('rpc', pkg)

rpc_system_pkg = types.ModuleType('rpc.system')
rpc_system_pkg.__path__ = [str(pathlib.Path(__file__).resolve().parent.parent / 'rpc/system')]
sys.modules.setdefault('rpc.system', rpc_system_pkg)

rpc_system_storage_pkg = types.ModuleType('rpc.system.storage')
rpc_system_storage_pkg.__path__ = [str(pathlib.Path(__file__).resolve().parent.parent / 'rpc/system/storage')]
sys.modules.setdefault('rpc.system.storage', rpc_system_storage_pkg)

# stub server.models
server_pkg = types.ModuleType('server')
models_pkg = types.ModuleType('server.models')


class RPCResponse(BaseModel):
  op: str
  payload: dict
  version: int = 1


class AuthContext(BaseModel):
  user_guid: str = ''
  roles: list[str] = []


models_pkg.RPCResponse = RPCResponse
models_pkg.AuthContext = AuthContext
server_pkg.models = models_pkg
sys.modules.setdefault('server', server_pkg)
sys.modules.setdefault('server.models', models_pkg)

import importlib.util

svc_spec = importlib.util.spec_from_file_location(
  'rpc.system.storage.services',
  pathlib.Path(__file__).resolve().parent.parent / 'rpc/system/storage/services.py',
)
svc = importlib.util.module_from_spec(svc_spec)
sys.modules['rpc.system.storage.services'] = svc
svc_spec.loader.exec_module(svc)

system_storage_get_stats_v1 = svc.system_storage_get_stats_v1


async def fake_unbox(request: Request):
  body = await request.json()
  op = body.get('op')
  payload = body.get('payload')
  rpc_req = SimpleNamespace(op=op, payload=payload, version=1)
  auth_ctx = SimpleNamespace(user_guid='u1', roles=[])
  return rpc_req, auth_ctx, None


svc.unbox_request = fake_unbox


class DummyStorageModule:
  def __init__(self):
    self.reindex_called = False

  async def reindex(self):
    self.reindex_called = True

  async def get_storage_stats(self):
    return {
      'file_count': 5,
      'total_bytes': 10,
      'folder_count': 2,
      'db_rows': 7,
    }


app = FastAPI()
app.state.storage = DummyStorageModule()


@app.post('/rpc')
async def rpc_endpoint(request: Request):
  return await system_storage_get_stats_v1(request)


client = TestClient(app)


def test_get_stats_service_triggers_reindex():
  resp = client.post('/rpc', json={
    'op': 'urn:system:storage:get_stats:1',
    'payload': {'reindex': True},
  })
  assert resp.status_code == 200
  assert app.state.storage.reindex_called is True
  assert resp.json()['payload'] == {
    'file_count': 5,
    'total_bytes': 10,
    'folder_count': 2,
    'db_rows': 7,
  }

