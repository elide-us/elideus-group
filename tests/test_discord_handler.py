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
  return RPCRequest(op='urn:discord:command:get_roles:1'), AuthContext(user_guid='u1'), []

discord_handler.unbox_request = _stub_unbox_request

async def dummy_handler(parts, request):
  return RPCResponse(op='urn:discord:command:get_roles:1', payload={'roles': ['ROLE_A']}, version=1)

class DummyAuth:
  def __init__(self, allowed: bool):
    self.allowed = allowed
    self.roles = {"ROLE_DISCORD_BOT": 0x40}

  async def user_has_role(self, guid: str, mask: int) -> bool:
    return self.allowed

def _get_client(allowed: bool):
  app = FastAPI()
  app.state.auth = DummyAuth(allowed)
  discord_handler.HANDLERS = {'command': dummy_handler}

  @app.post('/rpc')
  async def rpc_endpoint(request: Request):
    return await discord_handler.handle_discord_request(['command'], request)

  return TestClient(app)

def test_discord_handler_rejects_missing_role():
  client = _get_client(False)
  resp = client.post('/rpc', json={'op': 'urn:discord:command:get_roles:1'})
  assert resp.status_code == 403
  data = resp.json()
  assert (
    data['detail']
    == 'You must have the Discord bot role assigned to use this bot.'
  )

def test_discord_handler_allows_role():
  client = _get_client(True)
  resp = client.post('/rpc', json={'op': 'urn:discord:command:get_roles:1'})
  assert resp.status_code == 200
  data = resp.json()
  assert data['payload'] == {'roles': ['ROLE_A']}
