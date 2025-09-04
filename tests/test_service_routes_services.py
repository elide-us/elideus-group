import types, sys, pathlib
from types import SimpleNamespace
from fastapi import FastAPI
from fastapi.testclient import TestClient
from starlette.requests import Request

# Stub rpc packages
pkg = types.ModuleType('rpc')
pkg.__path__ = [str(pathlib.Path(__file__).resolve().parent.parent / 'rpc')]
sys.modules.setdefault('rpc', pkg)

rpc_service_pkg = types.ModuleType('rpc.service')
rpc_service_pkg.__path__ = [str(pathlib.Path(__file__).resolve().parent.parent / 'rpc/service')]
sys.modules.setdefault('rpc.service', rpc_service_pkg)

rpc_service_routes_pkg = types.ModuleType('rpc.service.routes')
rpc_service_routes_pkg.__path__ = [str(pathlib.Path(__file__).resolve().parent.parent / 'rpc/service/routes')]
sys.modules.setdefault('rpc.service.routes', rpc_service_routes_pkg)

# Stub server modules
server_pkg = types.ModuleType('server')
modules_pkg = types.ModuleType('server.modules')
db_module_pkg = types.ModuleType('server.modules.db_module')
auth_module_pkg = types.ModuleType('server.modules.auth_module')
models_pkg = types.ModuleType('server.models')


class DbModule:
  pass


db_module_pkg.DbModule = DbModule
modules_pkg.db_module = db_module_pkg


class AuthModule:
  def __init__(self):
    self.roles = {'ROLE_SERVICE_ADMIN': 1}

  def mask_to_names(self, mask):
    return [name for name, bit in self.roles.items() if mask & bit]

  def names_to_mask(self, names):
    mask = 0
    for n in names:
      mask |= self.roles.get(n, 0)
    return mask


auth_module_pkg.AuthModule = AuthModule
modules_pkg.auth_module = auth_module_pkg


class RPCResponse:
  def __init__(self, **data):
    self.__dict__.update(data)


models_pkg.RPCResponse = RPCResponse
server_pkg.modules = modules_pkg
server_pkg.models = models_pkg

sys.modules.setdefault('server', server_pkg)
sys.modules.setdefault('server.modules', modules_pkg)
sys.modules.setdefault('server.modules.db_module', db_module_pkg)
sys.modules.setdefault('server.modules.auth_module', auth_module_pkg)
sys.modules.setdefault('server.models', models_pkg)

import importlib.util

svc_spec = importlib.util.spec_from_file_location(
  'rpc.service.routes.services',
  pathlib.Path(__file__).resolve().parent.parent / 'rpc/service/routes/services.py',
)
svc = importlib.util.module_from_spec(svc_spec)
sys.modules['rpc.service.routes.services'] = svc
svc_spec.loader.exec_module(svc)

service_routes_get_routes_v1 = svc.service_routes_get_routes_v1
service_routes_upsert_route_v1 = svc.service_routes_upsert_route_v1
service_routes_delete_route_v1 = svc.service_routes_delete_route_v1


async def fake_unbox(request: Request):
  body = await request.json()
  op = body.get('op')
  payload = body.get('payload')
  rpc_req = SimpleNamespace(op=op, payload=payload, version=1)
  auth_ctx = SimpleNamespace(user_guid='u1', roles=['ROLE_SERVICE_ADMIN'])
  return rpc_req, auth_ctx, None


svc.unbox_request = fake_unbox


class DummyDb:
  def __init__(self):
    self.calls = []

  async def run(self, op: str, args: dict):
    self.calls.append((op, args))
    if op == 'urn:service:routes:get_routes:1':
      rows = [{
        'element_path': '/a',
        'element_name': 'A',
        'element_icon': 'home',
        'element_sequence': 1,
        'element_roles': 1,
      }]
      return SimpleNamespace(rows=rows, rowcount=1)
    if op in ('urn:service:routes:upsert_route:1', 'urn:service:routes:delete_route:1'):
      return SimpleNamespace(rows=[], rowcount=1)
    raise AssertionError(f'unexpected op {op}')


db = DummyDb()
auth = AuthModule()

app = FastAPI()
app.state.db = db
app.state.auth = auth


@app.post('/rpc')
async def rpc_endpoint(request: Request):
  body = await request.json()
  op = body['op']
  if op == 'urn:service:routes:get_routes:1':
    return await service_routes_get_routes_v1(request)
  if op == 'urn:service:routes:upsert_route:1':
    return await service_routes_upsert_route_v1(request)
  if op == 'urn:service:routes:delete_route:1':
    return await service_routes_delete_route_v1(request)
  raise AssertionError('unexpected op')


client = TestClient(app)


def test_get_routes_service():
  resp = client.post('/rpc', json={'op': 'urn:service:routes:get_routes:1'})
  assert resp.status_code == 200
  data = resp.json()
  assert data['payload'] == {
    'routes': [{
      'path': '/a',
      'name': 'A',
      'icon': 'home',
      'sequence': 1,
      'required_roles': ['ROLE_SERVICE_ADMIN'],
    }]
  }
  assert ('urn:service:routes:get_routes:1', {}) in db.calls


def test_upsert_and_delete_route_service():
  upsert_payload = {
    'path': '/a',
    'name': 'A',
    'icon': 'home',
    'sequence': 1,
    'required_roles': ['ROLE_SERVICE_ADMIN'],
  }
  resp = client.post('/rpc', json={'op': 'urn:service:routes:upsert_route:1', 'payload': upsert_payload})
  assert resp.status_code == 200
  resp = client.post('/rpc', json={'op': 'urn:service:routes:delete_route:1', 'payload': {'path': '/a'}})
  assert resp.status_code == 200
  assert ('urn:service:routes:upsert_route:1', {
    'path': '/a',
    'name': 'A',
    'icon': 'home',
    'sequence': 1,
    'roles': 1,
  }) in db.calls
  assert ('urn:service:routes:delete_route:1', {'path': '/a'}) in db.calls
