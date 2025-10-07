import pathlib
import sys
import types
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

# Stub server models
server_pkg = types.ModuleType('server')
models_pkg = types.ModuleType('server.models')


class RPCResponse:
  def __init__(self, **data):
    data.setdefault('error', None)
    self.__dict__.update(data)


def ensure_json_serializable(value, *, field_name):
  return value


models_pkg.RPCResponse = RPCResponse
models_pkg.ensure_json_serializable = ensure_json_serializable
server_pkg.models = models_pkg

sys.modules.setdefault('server', server_pkg)
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


def _make_auth_context():
  return SimpleNamespace(user_guid='u1', roles=['ROLE_SERVICE_ADMIN'])


async def fake_unbox(request: Request):
  body = await request.json()
  op = body.get('op')
  payload = body.get('payload')
  rpc_req = SimpleNamespace(op=op, payload=payload, version=1)
  return rpc_req, _make_auth_context(), None


svc.unbox_request = fake_unbox


class DummyServiceRoutesModule:
  def __init__(self):
    self.list_calls = 0
    self.upsert_calls: list[dict[str, object]] = []
    self.delete_calls: list[str] = []

  async def list_routes(self):
    self.list_calls += 1
    return [
      {
        'path': '/a',
        'name': 'A',
        'icon': 'home',
        'sequence': 1,
        'required_roles': ['ROLE_SERVICE_ADMIN'],
      }
    ]

  async def upsert_route(self, **route):
    self.upsert_calls.append(route)
    return route

  async def delete_route(self, path: str):
    self.delete_calls.append(path)
    return {'path': path}


class FailingServiceRoutesModule(DummyServiceRoutesModule):
  async def upsert_route(self, **route):
    raise KeyError('Undefined roles: ROLE_UNKNOWN')


app = FastAPI()
app.state.service_routes = DummyServiceRoutesModule()


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


def _make_client():
  return TestClient(app)


def test_get_routes_service():
  client = _make_client()
  app.state.service_routes = DummyServiceRoutesModule()
  resp = client.post('/rpc', json={'op': 'urn:service:routes:get_routes:1', 'version': 1})
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
  assert app.state.service_routes.list_calls == 1


def test_upsert_and_delete_route_service():
  client = _make_client()
  module = DummyServiceRoutesModule()
  app.state.service_routes = module
  upsert_payload = {
    'path': '/a',
    'name': 'A',
    'icon': 'home',
    'sequence': 1,
    'required_roles': ['ROLE_SERVICE_ADMIN'],
  }
  resp = client.post('/rpc', json={'op': 'urn:service:routes:upsert_route:1', 'payload': upsert_payload, 'version': 1})
  assert resp.status_code == 200
  assert module.upsert_calls == [upsert_payload]
  resp = client.post('/rpc', json={'op': 'urn:service:routes:delete_route:1', 'payload': {'path': '/a'}, 'version': 1})
  assert resp.status_code == 200
  assert module.delete_calls == ['/a']


def test_upsert_route_invalid_role_returns_400():
  client = _make_client()
  app.state.service_routes = FailingServiceRoutesModule()
  upsert_payload = {
    'path': '/a',
    'name': 'A',
    'icon': 'home',
    'sequence': 1,
    'required_roles': ['ROLE_UNKNOWN'],
  }
  resp = client.post('/rpc', json={'op': 'urn:service:routes:upsert_route:1', 'payload': upsert_payload, 'version': 1})
  assert resp.status_code == 400
  data = resp.json()
  assert data['detail'] == "'Undefined roles: ROLE_UNKNOWN'"
