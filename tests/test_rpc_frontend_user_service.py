import asyncio
from fastapi import FastAPI, Request
from rpc.models import RPCRequest
from rpc.frontend.user import services

class DummyAuth:
  async def decode_bearer_token(self, token):
    return {'guid': 'uid'}

class DummyDB:
  async def get_user_profile(self, guid):
    return {
      'guid': guid,
      'display_name': 'u',
      'email': 'e',
      'display_email': True,
      'credits': 0,
      'provider_name': 'microsoft',
      'rotation_token': None,
      'rotation_expires': None,
    }

def test_get_profile_data_v1():
  app = FastAPI()
  app.state.auth = DummyAuth()
  app.state.database = DummyDB()
  req = Request({'type': 'http', 'app': app})
  rpc_req = RPCRequest(op='op', payload={'bearerToken': 'token'})
  resp = asyncio.run(services.get_profile_data_v1(rpc_req, req))
  assert resp.op == 'urn:frontend:user:profile_data:1'
  assert resp.payload.email == 'e'
  assert resp.payload.displayEmail is True
