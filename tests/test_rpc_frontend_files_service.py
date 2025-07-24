import asyncio
from fastapi import FastAPI, Request
from rpc.models import RPCRequest
from rpc.frontend.files import services

class DummyAuth:
  async def decode_bearer_token(self, token):
    return {'guid': token}

class DummyStorage:
  def __init__(self):
    self.files = [{'name': 'f.txt', 'url': 'u/f.txt', 'content_type': 'text/plain'}]
  async def list_user_files(self, guid):
    return self.files
  async def delete_user_file(self, guid, filename):
    self.files = [f for f in self.files if f['name'] != filename]


def test_list_files_v1():
  app = FastAPI()
  app.state.auth = DummyAuth()
  app.state.storage = DummyStorage()
  req = Request({'type': 'http', 'app': app, 'headers': []})
  rpc = RPCRequest(op='op', payload={'bearerToken': 'uid'})
  resp = asyncio.run(services.list_files_v1(rpc, req))
  assert resp.op == 'urn:frontend:files:list:1'
  assert len(resp.payload.files) == 1
  assert resp.payload.files[0].name == 'f.txt'


def test_delete_file_v1():
  app = FastAPI()
  app.state.auth = DummyAuth()
  app.state.storage = DummyStorage()
  req = Request({'type': 'http', 'app': app, 'headers': []})
  rpc = RPCRequest(op='op', payload={'bearerToken': 'uid', 'filename': 'f.txt'})
  resp = asyncio.run(services.delete_file_v1(rpc, req))
  assert resp.op == 'urn:frontend:files:delete:1'
  assert len(resp.payload.files) == 0
