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
  async def handle_auth_login(self, provider, id_token, access_token):
    data = await self.verify_ms_id_token(id_token)
    profile = await self.fetch_ms_user_profile(access_token)
    return data['sub'], profile

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

  async def set_user_profile_image(self, guid, image, provider):
    self.image = (guid, image, provider)

  async def set_user_rotation_token(self, guid, token, exp):
    self.rtoken = (guid, token, exp)

  async def create_user_session(self, guid, bearer, rotation, exp):
    self.session = (guid, bearer, rotation, exp)
    return 'sid'

  async def get_user_roles(self, guid):
    return 0


def test_user_login_v1():
  app = FastAPI()
  app.state.auth = DummyAuth()
  app.state.mssql = DummyDB()
  req = Request({'type': 'http', 'app': app, 'headers': []})
  rpc_req = RPCRequest(op='op', payload={'idToken': 'id', 'accessToken': 'ac', 'provider': 'microsoft'})
  resp = asyncio.run(services.user_login_v1(rpc_req, req))
  assert resp.op == 'urn:auth:microsoft:login_data:1'
  assert resp.payload.bearerToken == 'token'
  assert resp.payload.rotationToken == 'rtoken'


class DummyAuthImage(DummyAuth):
  async def fetch_ms_user_profile(self, act):
    return {'email': 'e', 'username': 'u', 'profilePicture': 'img'}


class DummyDiscord:
  def __init__(self):
    self.messages = []

  async def send_sys_message(self, msg):
    self.messages.append(msg)


def test_user_login_profile_update():
  app = FastAPI()
  auth = DummyAuthImage()
  db = DummyDB()
  app.state.auth = auth
  app.state.mssql = db
  req = Request({'type': 'http', 'app': app, 'headers': []})
  rpc_req = RPCRequest(op='op', payload={'idToken': 'id', 'accessToken': 'ac', 'provider': 'microsoft'})
  asyncio.run(services.user_login_v1(rpc_req, req))
  assert db.image == ('uid', 'img', 'microsoft')


def test_user_login_reports_discord():
  app = FastAPI()
  app.state.auth = DummyAuth()
  db = DummyDB()
  async def roles(guid):
    return 0
  db.get_user_roles = roles
  discord = DummyDiscord()
  app.state.mssql = db
  app.state.discord = discord
  req = Request({'type': 'http', 'app': app, 'headers': []})
  rpc_req = RPCRequest(op='op', payload={'idToken': 'id', 'accessToken': 'ac', 'provider': 'microsoft'})
  asyncio.run(services.user_login_v1(rpc_req, req))
  assert discord.messages == ["User login uid: u Credits: 0 Roles: None"]

