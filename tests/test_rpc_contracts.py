import asyncio
import sys
import types
from types import SimpleNamespace

import pytest
from fastapi import FastAPI, HTTPException
from starlette.requests import Request

from rpc.service import handler as service_handler
from rpc.service.handler import handle_service_request
import rpc.handler as root_handler
from rpc.handler import handle_rpc_request
from server.registry import RegistryRouter
from server.registry.types import DBRequest, DBResponse


def _make_request() -> Request:
  app = FastAPI()
  scope = {
    'type': 'http',
    'http_version': '1.1',
    'scheme': 'http',
    'method': 'POST',
    'path': '/rpc',
    'query_string': b'',
    'headers': [],
    'app': app,
  }
  return Request(scope)


def test_handle_rpc_request_rejects_non_urn_prefix(monkeypatch):
  request = _make_request()

  async def fake_unbox(req):
    rpc_request = SimpleNamespace(op='invalid', request_id='req-123', version=1)
    auth_ctx = SimpleNamespace(user_guid='user')
    return rpc_request, auth_ctx, ['invalid', 'service', 'noop']

  monkeypatch.setattr(root_handler, 'unbox_request', fake_unbox)

  with pytest.raises(HTTPException) as exc:
    asyncio.run(handle_rpc_request(request))

  assert exc.value.status_code == 400
  assert exc.value.detail['code'] == 'rpc.bad_request'
  assert 'Invalid URN prefix' in exc.value.detail['message']


def test_handle_rpc_request_unknown_domain(monkeypatch):
  request = _make_request()

  async def fake_unbox(req):
    rpc_request = SimpleNamespace(op='urn:missing:noop:op:1', request_id='req-456', version=1)
    auth_ctx = SimpleNamespace(user_guid='user')
    return rpc_request, auth_ctx, ['urn', 'missing', 'noop', 'op', '1']

  monkeypatch.setattr(root_handler, 'unbox_request', fake_unbox)

  with pytest.raises(HTTPException) as exc:
    asyncio.run(handle_rpc_request(request))

  assert exc.value.status_code == 404
  assert exc.value.detail['code'] == 'rpc.not_found'
  assert 'Unknown RPC domain' in exc.value.detail['message']


def test_service_handler_enforces_role_capabilities(monkeypatch):
  called = {'invoked': False}

  async def fake_handler(parts, request):
    called['invoked'] = True
    return DBResponse(rows=[], rowcount=0)

  monkeypatch.setitem(service_handler.HANDLERS, 'roles', fake_handler)

  async def fake_unbox(req):
    rpc_request = SimpleNamespace(op='urn:service:roles:list:1', request_id='req-service', version=1)
    auth_ctx = SimpleNamespace(user_guid='user-1')
    return rpc_request, auth_ctx, ['urn', 'service', 'roles', 'list', '1']

  monkeypatch.setattr(service_handler, 'unbox_request', fake_unbox)

  class DummyAuth:
    def __init__(self):
      self.required = []
      self.checked = []

    def require_role_mask(self, name):
      self.required.append(name)
      return 0x4000000000000000

    async def user_has_role(self, guid, mask):
      self.checked.append((guid, mask))
      return False

  services = SimpleNamespace(auth=DummyAuth())
  request = _make_request()
  request.app.state.services = services

  with pytest.raises(HTTPException) as exc:
    asyncio.run(handle_service_request(['roles'], request))

  assert exc.value.status_code == 403
  assert services.auth.required == ['ROLE_SERVICE_ADMIN']
  assert services.auth.checked == [('user-1', 0x4000000000000000)]
  assert called['invoked'] is False


def test_registry_router_detects_missing_provider_bindings(monkeypatch):
  router = RegistryRouter()
  subdomain = router.domain('demo').subdomain('widgets')
  subdomain.add_function('list', version=1, provider_map='demo.widgets.list')

  module_name = 'server.registry.providers.testcontracts'
  provider_module = types.ModuleType(module_name)
  provider_module.PROVIDER_QUERIES = {}
  monkeypatch.setitem(sys.modules, module_name, provider_module)

  with pytest.raises(RuntimeError) as exc:
    router.load_provider('testcontracts')

  message = str(exc.value)
  assert "provider 'testcontracts'" in message.lower()
  assert 'db:demo:widgets:list:1' in message


def test_registry_router_executes_bound_provider(monkeypatch):
  router = RegistryRouter()
  subdomain = router.domain('demo').subdomain('widgets')
  subdomain.add_function('list', version=1, provider_map='demo.widgets.list')

  async def fake_executor(request):
    return DBResponse(rows=[{'id': 1}], rowcount=1)

  module_name = 'server.registry.providers.contractdemo'
  provider_module = types.ModuleType(module_name)
  provider_module.PROVIDER_QUERIES = {'demo.widgets.list': {1: fake_executor}}
  monkeypatch.setitem(sys.modules, module_name, provider_module)

  router.load_provider('contractdemo')
  route = router.resolve('db:demo:widgets:list:1')
  assert route is not None

  executor = router.get_executor(route)
  request = DBRequest(op=route.key, params={})
  result = asyncio.run(executor(request))

  assert isinstance(result, DBResponse)
  assert result.rows == [{'id': 1}]
  assert result.rowcount == 1
