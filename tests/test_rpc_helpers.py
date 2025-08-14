from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
import pathlib, sys, types

# Avoid importing rpc.__init__ which has side effects that trigger circular imports
pkg = types.ModuleType('rpc')
pkg.__path__ = [str(pathlib.Path(__file__).resolve().parent.parent / 'rpc')]
sys.modules.setdefault('rpc', pkg)

models_mod = types.ModuleType('rpc.models')

class RPCRequest:
  def __init__(self, **data):
    self.__dict__.update(data)

class RPCResponse:
  def __init__(self, **data):
    self.__dict__.update(data)

models_mod.RPCRequest = RPCRequest
models_mod.RPCResponse = RPCResponse
sys.modules['rpc.models'] = models_mod

ROOT = pathlib.Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
  sys.path.insert(0, str(ROOT))

server_pkg = types.ModuleType('server')
server_pkg.__path__ = [str(ROOT / 'server')]
sys.modules.pop('server', None)
sys.modules['server'] = server_pkg

from rpc.helpers import get_rpcrequest_from_request

app = FastAPI()

@app.post('/rpc')
async def parse_rpc(request: Request):
  rpc_request, auth_ctx, parts = await get_rpcrequest_from_request(request)
  return {'user_role': auth_ctx.role_mask, 'parts': parts}

client = TestClient(app)

def test_public_request_without_token():
  resp = client.post('/rpc', json={'op': 'urn:public:links:get_home_links:1'})
  assert resp.status_code == 200
  data = resp.json()
  assert data['user_role'] == 0
  assert data['parts'][1] == 'public'

def test_private_request_requires_token():
  resp = client.post('/rpc', json={'op': 'urn:users:profile:get_profile:1'})
  assert resp.status_code == 401
