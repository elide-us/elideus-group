import asyncio
from fastapi import FastAPI, Request
from rpc.models import RPCRequest
from rpc.storage.files import services

class DummyAuth:
  async def decode_bearer_token(self, token):
    return {'guid': token}

class DummyStorage:
  def __init__(self):
    self.files = [{'name': 'f.txt', 'url': 'u/f.txt', 'content_type': 'text/plain'}]
    self.written = None
  async def list_user_files(self, guid):
    return self.files
  async def delete_user_file(self, guid, filename):
    self.files = [f for f in self.files if f['name'] != filename]
  async def write_buffer(self, buf, guid, filename, content_type=None):
    self.written = (guid, filename, content_type, buf.read())
    self.files.append({'name': filename, 'url': f'u/{filename}', 'content_type': content_type})


def test_list_files_v1():
  app = FastAPI()
  app.state.auth = DummyAuth()
  app.state.storage = DummyStorage()
  req = Request({'type': 'http', 'app': app, 'headers': []})
  rpc = RPCRequest(op='op', payload={'bearerToken': 'uid'})
  resp = asyncio.run(services.list_files_v1(rpc, req))
  assert resp.op == 'urn:storage:files:list:1'
  assert len(resp.payload.files) == 1
  assert resp.payload.files[0].name == 'f.txt'


def test_delete_file_v1():
  app = FastAPI()
  app.state.auth = DummyAuth()
  app.state.storage = DummyStorage()
  req = Request({'type': 'http', 'app': app, 'headers': []})
  rpc = RPCRequest(op='op', payload={'bearerToken': 'uid', 'filename': 'f.txt'})
  resp = asyncio.run(services.delete_file_v1(rpc, req))
  assert resp.op == 'urn:storage:files:delete:1'
  assert len(resp.payload.files) == 0


def test_upload_file_v1():
  app = FastAPI()
  app.state.auth = DummyAuth()
  app.state.storage = DummyStorage()
  req = Request({'type': 'http', 'app': app, 'headers': []})
  payload = {
    'bearerToken': 'uid',
    'filename': 'img.png',
    'dataUrl': 'data:image/png;base64,aGVsbG8=',
    'contentType': 'image/png'
  }
  rpc = RPCRequest(op='op', payload=payload)
  resp = asyncio.run(services.upload_file_v1(rpc, req))
  assert resp.op == 'urn:storage:files:upload:1'
  assert any(f.name == 'img.png' for f in resp.payload.files)
  assert app.state.storage.written[2] == 'image/png'
