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
      'display_name': getattr(self, 'name', 'u'),
      'email': 'e',
      'profile_image': 'img',
      'display_email': True,
      'credits': 0,
      'provider_name': 'microsoft',
      'rotation_token': None,
      'rotation_expires': None,
    }

  async def update_display_name(self, guid, name):
    self.updated = (guid, name)
    self.name = name

def test_get_profile_data_v1():
  app = FastAPI()
  app.state.auth = DummyAuth()
  app.state.database = DummyDB()
  req = Request({'type': 'http', 'app': app, 'headers': []})
  rpc_req = RPCRequest(op='op', payload={'bearerToken': 'token'})
  resp = asyncio.run(services.get_profile_data_v1(rpc_req, req))
  assert resp.op == 'urn:frontend:user:profile_data:1'
  assert resp.payload.email == 'e'
  assert resp.payload.displayEmail is True
  assert resp.payload.profilePicture == 'img'


def test_set_display_name_v1():
  app = FastAPI()
  auth = DummyAuth()
  db = DummyDB()
  app.state.auth = auth
  app.state.database = db
  req = Request({'type': 'http', 'app': app, 'headers': []})
  rpc_req = RPCRequest(op='op', payload={'bearerToken': 'token', 'displayName': 'n'})
  resp = asyncio.run(services.set_display_name_v1(rpc_req, req))
  assert resp.op == 'urn:frontend:user:set_display_name:1'
  assert resp.payload.username == 'n'
  assert db.updated == ('uid', 'n')
  assert resp.payload.profilePicture == 'img'

