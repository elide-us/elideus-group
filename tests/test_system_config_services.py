import types, sys, pathlib
from fastapi import FastAPI
from fastapi.testclient import TestClient
from starlette.requests import Request
from types import SimpleNamespace
from pydantic import BaseModel

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

# Stub server.models
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
  'rpc.system.config.services',
  pathlib.Path(__file__).resolve().parent.parent / 'rpc/system/config/services.py',
)
svc = importlib.util.module_from_spec(svc_spec)
sys.modules['rpc.system.config.services'] = svc
svc_spec.loader.exec_module(svc)

system_config_get_configs_v1 = svc.system_config_get_configs_v1
system_config_upsert_config_v1 = svc.system_config_upsert_config_v1
system_config_delete_config_v1 = svc.system_config_delete_config_v1

async def fake_get(request: Request):
  body = await request.json()
  op = body.get('op')
  payload = body.get('payload')
  rpc_req = SimpleNamespace(op=op, payload=payload, version=1)
  auth_ctx = SimpleNamespace(user_guid='u1', roles=[])
  return rpc_req, auth_ctx, None

svc.unbox_request = fake_get

class DummySystemConfigModule:
  def __init__(self):
    self.calls = []
  async def get_configs(self, user_guid, roles):
    self.calls.append(('get_configs', user_guid, roles))
    from rpc.system.config.models import SystemConfigConfigItem1, SystemConfigList1
    item = SystemConfigConfigItem1(key='LoggingLevel', value='4')
    return SystemConfigList1(items=[item])
  async def upsert_config(self, user_guid, roles, key, value):
    self.calls.append(('upsert_config', key, value))
    from rpc.system.config.models import SystemConfigConfigItem1
    return SystemConfigConfigItem1(key=key, value=value)
  async def delete_config(self, user_guid, roles, key):
    self.calls.append(('delete_config', key))
    from rpc.system.config.models import SystemConfigDeleteConfig1
    return SystemConfigDeleteConfig1(key=key)

app = FastAPI()
mod = DummySystemConfigModule()
app.state.system_config = mod

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
    'items': [{'key': 'LoggingLevel', 'value': '4'}]
  }
  assert ('get_configs', 'u1', []) in mod.calls

def test_upsert_and_delete_config_service():
  resp = client.post('/rpc', json={'op': 'urn:system:config:upsert_config:1', 'payload': {'key': 'LoggingLevel', 'value': '2'}})
  assert resp.status_code == 200
  resp = client.post('/rpc', json={'op': 'urn:system:config:delete_config:1', 'payload': {'key': 'LoggingLevel'}})
  assert resp.status_code == 200
  assert ('upsert_config', 'LoggingLevel', '2') in mod.calls
  assert ('delete_config', 'LoggingLevel') in mod.calls
