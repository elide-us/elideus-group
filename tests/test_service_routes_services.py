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

from rpc.service.routes.models import (
  ServiceRoutesDeleteRoute1,
  ServiceRoutesList1,
  ServiceRoutesRouteItem1,
)

# Stub server modules
server_pkg = types.ModuleType('server')
modules_pkg = types.ModuleType('server.modules')
modules_pkg.__path__ = []
models_pkg = types.ModuleType('server.models')
modules_models_pkg = types.ModuleType('server.modules.models')
modules_models_pkg.__path__ = []


class RPCResponse:
  def __init__(self, **data):
    self.__dict__.update(data)


class RPCRequest:
  def __init__(self, **data):
    self.__dict__.update(data)


class AuthContext:
  def __init__(self):
    self.user_guid = None
    self.roles = []
    self.role_mask = 0
    self.provider = None
    self.claims = {}


models_pkg.RPCResponse = RPCResponse
models_pkg.RPCRequest = RPCRequest
models_pkg.AuthContext = AuthContext
server_pkg.modules = modules_pkg
server_pkg.models = models_pkg
modules_pkg.models = modules_models_pkg

sys.modules.setdefault('server', server_pkg)
sys.modules.setdefault('server.modules', modules_pkg)
sys.modules.setdefault('server.models', models_pkg)
sys.modules.setdefault('server.modules.models', modules_models_pkg)

import importlib.util

service_routes_models_spec = importlib.util.spec_from_file_location(
  'server.modules.models.service_routes',
  pathlib.Path(__file__).resolve().parent.parent / 'server/modules/models/service_routes.py',
)
service_routes_models = importlib.util.module_from_spec(service_routes_models_spec)
sys.modules['server.modules.models.service_routes'] = service_routes_models
modules_models_pkg.service_routes = service_routes_models
service_routes_models_spec.loader.exec_module(service_routes_models)

ServiceRouteCollection = service_routes_models.ServiceRouteCollection
ServiceRouteDelete = service_routes_models.ServiceRouteDelete
ServiceRouteItem = service_routes_models.ServiceRouteItem

service_routes_module_pkg = types.ModuleType('server.modules.service_routes_module')


class StubServiceRoutesModule:
  def __init__(self):
    self.calls = []

  async def on_ready(self):
    self.calls.append(('on_ready', None))

  async def get_routes(self, user_guid, roles):
    self.calls.append(('get_routes', user_guid, tuple(roles)))
    route = ServiceRouteItem(
      path='/a',
      name='A',
      icon='home',
      sequence=1,
      required_roles=['ROLE_SERVICE_ADMIN'],
    )
    return ServiceRouteCollection(routes=[route])

  async def upsert_route(self, user_guid, roles, route):
    self.calls.append(('upsert_route', user_guid, tuple(roles), route))
    return route

  async def delete_route(self, user_guid, roles, path):
    self.calls.append(('delete_route', user_guid, tuple(roles), path))
    return ServiceRouteDelete(path=path)


service_routes_module_pkg.ServiceRoutesModule = StubServiceRoutesModule
modules_pkg.service_routes_module = service_routes_module_pkg


registry_pkg = types.ModuleType('server.registry')
registry_pkg.__path__ = []

registry_system_pkg = types.ModuleType('server.registry.system')
registry_system_pkg.__path__ = []

sys.modules.setdefault('server.registry', registry_pkg)
sys.modules.setdefault('server.registry.system', registry_system_pkg)

server_pkg.registry = registry_pkg
registry_pkg.system = registry_system_pkg

sys.modules.setdefault('server.modules.service_routes_module', service_routes_module_pkg)
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


app = FastAPI()
module = StubServiceRoutesModule()
app.state.service_routes = module


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
  assert ('get_routes', 'u1', ('ROLE_SERVICE_ADMIN',)) in module.calls


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
  assert any(call[0] == 'upsert_route' and call[3].path == '/a' for call in module.calls)
  assert ('delete_route', 'u1', ('ROLE_SERVICE_ADMIN',), '/a') in module.calls
