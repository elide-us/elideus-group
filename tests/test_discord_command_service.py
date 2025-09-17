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

from rpc.discord.command import services as discord_services


async def _stub_unbox_request(request):
  return RPCRequest(op='urn:discord:command:get_roles:1'), AuthContext(roles=['ROLE_A']), []

discord_services.unbox_request = _stub_unbox_request

app = FastAPI()


@app.post('/rpc')
async def rpc_endpoint(request: Request):
  return await discord_services.discord_command_get_roles_v1(request)


client = TestClient(app)


def test_discord_command_get_roles_service():
  resp = client.post('/rpc', json={'op': 'urn:discord:command:get_roles:1'})
  assert resp.status_code == 200
  data = resp.json()
  assert data['op'] == 'urn:discord:command:get_roles:1'
  assert data['payload'] == {'roles': ['ROLE_A']}

