import importlib.util
import pathlib
import sys
import types

from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
from types import SimpleNamespace

# Stub rpc package to avoid side effects from rpc.__init__
pkg = types.ModuleType('rpc')
pkg.__path__ = [str(pathlib.Path(__file__).resolve().parent.parent / 'rpc')]
pkg.HANDLERS = {}
sys.modules.setdefault('rpc', pkg)

# Load server models
spec = importlib.util.spec_from_file_location(
  'server.models', pathlib.Path(__file__).resolve().parent.parent / 'server/models.py'
)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
sys.modules['server.models'] = mod
RPCRequest = mod.RPCRequest
AuthContext = mod.AuthContext

from rpc.discord.bsky import services as bsky_services


class StubBskyModule:
  def __init__(self, response=None, error: Exception | None = None):
    self.calls: list[str] = []
    self.ready = False
    self.response = response
    self.error = error

  async def on_ready(self):
    self.ready = True

  async def post_message(self, message: str):
    self.calls.append(message)
    if self.error:
      raise self.error
    return self.response or SimpleNamespace(
      uri='at://example/record',
      cid='cid123',
      handle='example.handle',
      display_name='Example',
    )


def test_bsky_post_message_handler():
  app = FastAPI()
  module = StubBskyModule()
  app.state.bsky = module

  async def fake_unbox(request):
    return (
      RPCRequest(op='urn:discord:bsky:post:1', payload={'message': 'hello world'}),
      AuthContext(),
      [],
    )

  original = bsky_services.unbox_request
  bsky_services.unbox_request = fake_unbox

  @app.post('/rpc')
  async def rpc_endpoint(request: Request):
    return await bsky_services.discord_bsky_post_message_v1(request)

  client = TestClient(app)
  resp = client.post('/rpc', json={'op': 'urn:discord:bsky:post:1'})
  assert resp.status_code == 200
  assert module.ready is True
  assert module.calls == ['hello world']
  data = resp.json()
  expected = {
    'uri': 'at://example/record',
    'cid': 'cid123',
    'handle': 'example.handle',
    'display_name': 'Example',
  }
  assert data['payload'] == expected

  bsky_services.unbox_request = original


def test_bsky_post_message_handler_error():
  app = FastAPI()
  module = StubBskyModule(error=ValueError('missing creds'))
  app.state.bsky = module

  async def fake_unbox(request):
    return (
      RPCRequest(op='urn:discord:bsky:post:1', payload={'message': 'hello world'}),
      AuthContext(),
      [],
    )

  original = bsky_services.unbox_request
  bsky_services.unbox_request = fake_unbox

  @app.post('/rpc')
  async def rpc_endpoint(request: Request):
    return await bsky_services.discord_bsky_post_message_v1(request)

  client = TestClient(app)
  resp = client.post('/rpc', json={'op': 'urn:discord:bsky:post:1'})
  assert resp.status_code == 400
  assert module.calls == ['hello world']
  data = resp.json()
  assert data['detail'] == 'missing creds'

  bsky_services.unbox_request = original
