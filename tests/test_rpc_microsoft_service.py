import asyncio
from fastapi import FastAPI, Request
from rpc.models import RPCRequest
from rpc.auth.microsoft import services
from types import SimpleNamespace

class DummyAuth:
  async def handle_ms_auth_login(self, idt, act):
    return 'g', {'email': 'e', 'username': 'u', 'profilePicture': None}
  def make_bearer_token(self, guid):
    return 'token'


def test_user_login_v1():
  app = FastAPI()
  app.state.modules = SimpleNamespace(get_module=lambda n: DummyAuth())
  req = Request({'type': 'http', 'app': app})
  rpc_req = RPCRequest(op='op', payload={'idToken': 'id', 'accessToken': 'ac'})
  resp = asyncio.run(services.user_login_v1(rpc_req, req))
  assert resp.op == 'urn:auth:microsoft:login_data:1'
  assert resp.payload.bearerToken == 'token'

