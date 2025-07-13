import asyncio
from fastapi import FastAPI, Request
from rpc.models import RPCRequest
from rpc.auth.microsoft import services


class DummyAuth:
  async def handle_ms_auth_login(self, idt, act):
    return 'g', {'email': 'e', 'username': 'u', 'profilePicture': None}
  def make_bearer_token(self, guid):
    return 'token'

class DummyDB:
  async def select_ms_user(self, mid):
    return {
      'guid': 'uid',
      'provider_name': 'microsoft',
      'username': 'u',
      'email': 'e',
      'backup_email': None,
      'credits': 0,
    }

  async def insert_ms_user(self, mid, email, username):
    return await self.select_ms_user(mid)


def test_user_login_v1():
  app = FastAPI()
  app.state.auth = DummyAuth()
  app.state.database = DummyDB()
  req = Request({'type': 'http', 'app': app})
  rpc_req = RPCRequest(op='op', payload={'idToken': 'id', 'accessToken': 'ac'})
  resp = asyncio.run(services.user_login_v1(rpc_req, req))
  assert resp.op == 'urn:auth:microsoft:login_data:1'
  assert resp.payload.bearerToken == 'token'

