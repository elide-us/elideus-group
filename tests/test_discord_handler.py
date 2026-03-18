import importlib.util
import pathlib
import sys
import types
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

# Stub rpc package to avoid side effects from rpc.__init__
pkg = types.ModuleType('rpc')
pkg.__path__ = [str(pathlib.Path(__file__).resolve().parent.parent / 'rpc')]
sys.modules.setdefault('rpc', pkg)

# Load server models
def _load_models():
  spec = importlib.util.spec_from_file_location(
    'server.models', pathlib.Path(__file__).resolve().parent.parent / 'server/models.py'
  )
  mod = importlib.util.module_from_spec(spec)
  spec.loader.exec_module(mod)
  sys.modules['server.models'] = mod
  return mod

models = _load_models()
RPCRequest = models.RPCRequest
AuthContext = models.AuthContext
RPCResponse = models.RPCResponse

# Stub server modules
modules_pkg = types.ModuleType('server.modules')
sys.modules.setdefault('server.modules', modules_pkg)
auth_module_pkg = types.ModuleType('server.modules.auth_module')
class AuthModule: ...
auth_module_pkg.AuthModule = AuthModule
modules_pkg.auth_module = auth_module_pkg
sys.modules['server.modules.auth_module'] = auth_module_pkg

from rpc.discord import handler as discord_handler

async def _stub_unbox_request(request):
  return RPCRequest(op='urn:discord:chat:get_roles:1'), AuthContext(user_guid='u1'), []

discord_handler.unbox_request = _stub_unbox_request

async def dummy_handler(parts, request):
  return RPCResponse(op='urn:discord:chat:get_roles:1', payload={'roles': ['ROLE_A']}, version=1)

class DummyAuth:
  def __init__(self, error_detail: str | None = None):
    self.error_detail = error_detail
    self.calls = []

  async def check_domain_access(self, domain: str, user_guid: str) -> None:
    self.calls.append((domain, user_guid))
    if self.error_detail is not None:
      from fastapi import HTTPException
      raise HTTPException(status_code=403, detail=self.error_detail)

def _get_client(error_detail: str | None = None, subdomain: str = 'chat'):
  app = FastAPI()
  app.state.auth = DummyAuth(error_detail)
  discord_handler.HANDLERS = {subdomain: dummy_handler}

  @app.post('/rpc')
  async def rpc_endpoint(request: Request):
    return await discord_handler.handle_discord_request([subdomain], request)

  return TestClient(app), app.state.auth

def test_discord_handler_rejects_unconfigured_domain_access():
  client, auth = _get_client('Domain access not configured')
  resp = client.post('/rpc', json={'op': 'urn:discord:chat:get_roles:1'})
  assert resp.status_code == 403
  data = resp.json()
  assert data['detail'] == 'Domain access not configured'
  assert auth.calls == [('discord', 'u1')]

def test_discord_handler_allows_domain_role():
  client, auth = _get_client()
  resp = client.post('/rpc', json={'op': 'urn:discord:chat:get_roles:1'})
  assert resp.status_code == 200
  data = resp.json()
  assert data['payload'] == {'roles': ['ROLE_A']}
  assert auth.calls == [('discord', 'u1')]

def test_discord_handler_rejects_command_without_domain_role():
  client, auth = _get_client('Forbidden', subdomain='command')
  resp = client.post('/rpc', json={'op': 'urn:discord:command:get_roles:1'})
  assert resp.status_code == 403
  assert resp.json()['detail'] == 'Forbidden'
  assert auth.calls == [('discord', 'u1')]
