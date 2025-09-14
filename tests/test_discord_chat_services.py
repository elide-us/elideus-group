import importlib.util
import pathlib
import sys
import types
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

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

from rpc.discord.chat import services as chat_services


class StubModule:
  def __init__(self):
    self.called = False
    self.args = None
    self.uwu_called = False
    self.uwu_args = None
    self.updated = False
    self.update_args = None

  async def on_ready(self):
    pass

  async def summarize_channel(self, guild_id, channel_id, hours, max_messages=5000):
    return {
      'raw_text_blob': 'hi',
      'messages_collected': 1,
      'token_count_estimate': 2,
      'cap_hit': False,
    }

  async def uwu_chat(self, guild_id, channel_id, user_id, message, hours=1, max_messages=12):
    self.uwu_called = True
    self.uwu_args = (guild_id, channel_id, user_id, message)
    return {
      'token_count_estimate': 2,
      'summary_lines': ['hi'],
      'uwu_response_text': 'uwu hey',
    }

  async def log_conversation(self, persona, guild_id, channel_id, input_data, output_data):
    self.called = True
    self.args = (persona, guild_id, channel_id, input_data, output_data)
    return 42

  async def update_conversation_output(self, recid, output_data):
    self.updated = True
    self.update_args = (recid, output_data)

def test_uwu_chat_logs_conversation():
  app = FastAPI()
  module = StubModule()
  app.state.discord_chat = module

  async def fake_unbox(request):
    return (
      RPCRequest(op='urn:discord:chat:uwu_chat:1', payload={'message': 'hey', 'guild_id': 1, 'channel_id': 2, 'user_id': 3}),
      AuthContext(),
      [],
    )

  original = chat_services.unbox_request
  chat_services.unbox_request = fake_unbox

  @app.post('/rpc')
  async def rpc_endpoint(request: Request):
    return await chat_services.discord_chat_uwu_chat_v1(request)

  client = TestClient(app)
  resp = client.post('/rpc', json={'op': 'urn:discord:chat:uwu_chat:1'})
  assert resp.status_code == 200
  assert module.called
  assert module.updated
  assert module.uwu_called
  data = resp.json()
  expected = {
    "uwu_response_text": "uwu hey",
    "summary_lines": ["hi"],
    "token_count_estimate": 2,
  }
  assert data["payload"] == expected
  assert module.uwu_args == (1, 2, 3, 'hey')
  assert module.args == ('uwu', 1, 2, 'hey', '')
  assert module.update_args == (42, 'uwu hey')

  chat_services.unbox_request = original


def test_summarize_channel_logs_conversation():
  app = FastAPI()
  module = StubModule()
  app.state.discord_chat = module

  async def fake_unbox(request):
    return (
      RPCRequest(op='urn:discord:chat:summarize_channel:1', payload={'guild_id': 1, 'channel_id': 2, 'hours': 1}),
      AuthContext(),
      [],
    )

  original = chat_services.unbox_request
  chat_services.unbox_request = fake_unbox

  @app.post('/rpc')
  async def rpc_endpoint(request: Request):
    return await chat_services.discord_chat_summarize_channel_v1(request)

  client = TestClient(app)
  resp = client.post('/rpc', json={'op': 'urn:discord:chat:summarize_channel:1'})
  assert resp.status_code == 200
  assert module.called
  data = resp.json()
  expected = {
    "summary": "hi",
    "messages_collected": 1,
    "token_count_estimate": 2,
    "cap_hit": False,
  }
  assert data["payload"] == expected
  assert module.args[0] == 'summary'
  assert module.args[1] == 1
  assert module.args[2] == 2

  chat_services.unbox_request = original
