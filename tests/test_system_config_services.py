import types, sys, pathlib
from types import SimpleNamespace
from fastapi import FastAPI
from fastapi.testclient import TestClient
from starlette.requests import Request

# Stub rpc package to avoid side effects from rpc.__init__
pkg = types.ModuleType('rpc')
pkg.__path__ = [str(pathlib.Path(__file__).resolve().parent.parent / 'rpc')]
sys.modules.setdefault('rpc', pkg)

rpc_system_pkg = types.ModuleType('rpc.system')
rpc_system_pkg.__path__ = [str(pathlib.Path(__file__).resolve().parent.parent / 'rpc/system')]
sys.modules.setdefault('rpc.system', rpc_system_pkg)

rpc_system_config_pkg = types.ModuleType('rpc.system.config')
rpc_system_config_pkg.__path__ = [str(pathlib.Path(__file__).resolve().parent.parent / 'rpc/system/config')]
sys.modules.setdefault('rpc.system.config', rpc_system_config_pkg)

# Stub server modules to prevent importing full server app
server_pkg = types.ModuleType('server')
modules_pkg = types.ModuleType('server.modules')
db_module_pkg = types.ModuleType('server.modules.db_module')
models_pkg = types.ModuleType('server.models')

class DbModule:  # minimal placeholder for import
  pass

db_module_pkg.DbModule = DbModule
modules_pkg.db_module = db_module_pkg
server_pkg.modules = modules_pkg
class AuthContext:
  def __init__(self, **data):
    self.role_mask = 0
    self.__dict__.update(data)
models_pkg.AuthContext = AuthContext
server_pkg.models = models_pkg

sys.modules.setdefault('server', server_pkg)
sys.modules.setdefault('server.modules', modules_pkg)
sys.modules.setdefault('server.modules.db_module', db_module_pkg)
sys.modules.setdefault('server.models', models_pkg)

import importlib.util

svc_spec = importlib.util.spec_from_file_location(
  "rpc.system.config.services",
  pathlib.Path(__file__).resolve().parent.parent / "rpc/system/config/services.py",
)
svc = importlib.util.module_from_spec(svc_spec)
sys.modules["rpc.system.config.services"] = svc
svc_spec.loader.exec_module(svc)

system_config_get_configs_v1 = svc.system_config_get_configs_v1
system_config_upsert_config_v1 = svc.system_config_upsert_config_v1
system_config_delete_config_v1 = svc.system_config_delete_config_v1

async def fake_get(request: Request):
  body = await request.json()
  op = body.get('op')
  payload = body.get('payload')
  rpc_req = SimpleNamespace(op=op, payload=payload, version=1)
  auth_ctx = SimpleNamespace(user_guid='u1', roles=['ROLE_SYSTEM_ADMIN'])
  return rpc_req, auth_ctx, None

svc.get_rpcrequest_from_request = fake_get

class DummyDb:
  def __init__(self):
    self.calls = []
  async def run(self, op: str, args: dict):
    self.calls.append((op, args))
    if op == 'urn:system:config:get_configs:1':
      assert args == {}
      rows = [{'element_key': 'DebugLogging', 'element_value': 'true'}]
      return SimpleNamespace(rows=rows, rowcount=1)
    if op == 'urn:system:config:upsert_config:1':
      return SimpleNamespace(rows=[], rowcount=1)
    if op == 'urn:system:config:delete_config:1':
      return SimpleNamespace(rows=[], rowcount=1)
    raise AssertionError(f'unexpected op {op}')

db = DummyDb()
app = FastAPI()
app.state.db = db

@app.post('/rpc')
async def rpc_endpoint(request: Request):
  body = await request.json()
  op = body['op']
  if op == 'urn:system:config:get_configs:1':
    return await system_config_get_configs_v1(request)
  if op == 'urn:system:config:upsert_config:1':
    return await system_config_upsert_config_v1(request)
  if op == 'urn:system:config:delete_config:1':
    return await system_config_delete_config_v1(request)
  raise AssertionError('unexpected op')

client = TestClient(app)

def test_get_configs_service():
  resp = client.post('/rpc', json={'op': 'urn:system:config:get_configs:1'})
  assert resp.status_code == 200
  data = resp.json()
  assert data['payload'] == {
    'items': [{'key': 'DebugLogging', 'value': 'true'}]
  }
  assert ('urn:system:config:get_configs:1', {}) in db.calls

def test_upsert_and_delete_config_service():
  resp = client.post('/rpc', json={'op': 'urn:system:config:upsert_config:1', 'payload': {'key': 'DebugLogging', 'value': 'true'}})
  assert resp.status_code == 200
  resp = client.post('/rpc', json={'op': 'urn:system:config:delete_config:1', 'payload': {'key': 'DebugLogging'}})
  assert resp.status_code == 200
  assert ('urn:system:config:upsert_config:1', {'key': 'DebugLogging', 'value': 'true'}) in db.calls
  assert ('urn:system:config:delete_config:1', {'key': 'DebugLogging'}) in db.calls
