import asyncio
from fastapi import FastAPI, Request
from rpc.models import RPCRequest
from rpc.auth.microsoft import services


class DummyAuth:
  async def verify_ms_id_token(self, idt):
    return {'sub': 'g'}
  async def fetch_ms_user_profile(self, act):
    return {'email': 'e', 'username': 'u', 'profilePicture': None}
  def make_bearer_token(self, guid):
    return 'token'
  def make_rotation_token(self, guid):
    return ('rtoken', '2025-01-01T00:00:00Z')

class DummyDB:
  async def select_user(self, provider, mid):
    return {
      'guid': 'uid',
      'provider_name': 'microsoft',
      'display_name': 'u',
      'email': 'e',
      'credits': 0,
    }

  async def insert_user(self, provider, mid, email, username):
    return await self.select_user(provider, mid)

  async def set_user_profile_image(self, guid, image):
    self.image = (guid, image)

  async def set_user_rotation_token(self, guid, token, exp):
    self.rtoken = (guid, token, exp)

  async def create_user_session(self, guid, bearer, rotation, exp):
    self.session = (guid, bearer, rotation, exp)
    return 'sid'


def test_user_login_v1():
  app = FastAPI()
  app.state.auth = DummyAuth()
  app.state.database = DummyDB()
  req = Request({'type': 'http', 'app': app, 'headers': []})
  rpc_req = RPCRequest(op='op', payload={'idToken': 'id', 'accessToken': 'ac', 'provider': 'microsoft'})
  resp = asyncio.run(services.user_login_v1(rpc_req, req))
  assert resp.op == 'urn:auth:microsoft:login_data:1'
  assert resp.payload.bearerToken == 'token'
  assert resp.payload.rotationToken == 'rtoken'


class DummyAuthImage(DummyAuth):
  async def fetch_ms_user_profile(self, act):
    return {'email': 'e', 'username': 'u', 'profilePicture': 'img'}


def test_user_login_profile_update():
  app = FastAPI()
  auth = DummyAuthImage()
  db = DummyDB()
  app.state.auth = auth
  app.state.database = db
  req = Request({'type': 'http', 'app': app, 'headers': []})
  rpc_req = RPCRequest(op='op', payload={'idToken': 'id', 'accessToken': 'ac', 'provider': 'microsoft'})
  asyncio.run(services.user_login_v1(rpc_req, req))
  assert db.image == ('uid', 'img')

