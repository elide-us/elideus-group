import asyncio
from fastapi import FastAPI, Request
from rpc.handler import handle_rpc_request
from rpc.models import RPCRequest
from server.helpers import roles as role_helper

class DummyDB:
  def __init__(self):
    self.roles = {'ROLE_TEST': 2}
    self.users = {'u1': 2, 'u2': 0}

  async def list_roles(self):
    return [{'name': n, 'mask': m} for n, m in self.roles.items()]

  async def select_users_with_role(self, mask):
    return [{'guid': k, 'display_name': k} for k, v in self.users.items() if v & mask]

  async def select_users_without_role(self, mask):
    return [{'guid': k, 'display_name': k} for k, v in self.users.items() if not (v & mask)]

  async def get_user_roles(self, guid):
    return self.users.get(guid, 0)

  async def set_user_roles(self, guid, roles):
    self.users[guid] = roles

class DummyAuth:
  async def decode_bearer_token(self, token):
    return {'guid': token}

async def make_app():
  app = FastAPI()
  app.state.database = DummyDB()
  app.state.auth = DummyAuth()
  app.state.permcap = None
  app.state.env = None
  return app

def test_role_member_flow():
  app = asyncio.run(make_app())
  req = Request({'type': 'http', 'app': app, 'headers': []})
  rpc = RPCRequest(op='urn:admin:roles:get_members:1', payload={'role': 'ROLE_TEST'})
  resp = asyncio.run(handle_rpc_request(rpc, req))
  assert len(resp.payload.members) == 1
  rpc = RPCRequest(op='urn:admin:roles:add_member:1', payload={'role': 'ROLE_TEST', 'userGuid': 'u2'})
  resp = asyncio.run(handle_rpc_request(rpc, req))
  assert any(u.guid == 'u2' for u in resp.payload.members)
  rpc = RPCRequest(op='urn:admin:roles:remove_member:1', payload={'role': 'ROLE_TEST', 'userGuid': 'u1'})
  resp = asyncio.run(handle_rpc_request(rpc, req))
  assert all(u.guid != 'u1' for u in resp.payload.members)
