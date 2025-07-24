import asyncio
from fastapi import FastAPI, Request
from rpc.models import RPCRequest
from rpc.account.users import services

class DummyDB:
  async def get_user_profile(self, guid):
    return {
      'guid': guid,
      'display_name': getattr(self, 'name', 'u'),
      'email': 'e',
      'profile_image': 'img',
      'display_email': False,
      'credits': 0,
      'provider_name': 'microsoft',
      'rotation_token': None,
      'rotation_expires': None,
    }
  async def update_display_name(self, guid, name):
    self.updated = (guid, name)
    self.name = name

class DummyStorage:
  async def get_user_folder_size(self, guid):
    return 0
  async def user_folder_exists(self, guid):
    return False
  async def ensure_user_folder(self, guid):
    return None

def test_set_user_display_name_v1():
  app = FastAPI()
  db = DummyDB()
  app.state.database = db
  app.state.storage = DummyStorage()
  req = Request({'type': 'http', 'app': app, 'headers': []})
  rpc = RPCRequest(op='op', payload={'userGuid': 'uid', 'displayName': 'n'})
  resp = asyncio.run(services.set_user_display_name_v1(rpc, req))
  assert resp.op == 'urn:account:users:set_display_name:1'
  assert resp.payload.username == 'n'
  assert db.updated == ('uid', 'n')
