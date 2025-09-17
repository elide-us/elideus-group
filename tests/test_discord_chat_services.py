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
    self.summary_called = False
    self.summary_args = None

  async def on_ready(self):
    pass

  async def summarize_channel(self, guild_id, channel_id, hours, max_messages=5000):
    return {
      'raw_text_blob': 'hi',
      'messages_collected': 1,
      'token_count_estimate': 2,
      'cap_hit': False,
    }

  async def summarize_chat(self, guild_id, channel_id, hours, user_id=None, max_messages=5000):
    self.summary_called = True
    self.summary_args = (guild_id, channel_id, hours, user_id)
    return {
      'token_count_estimate': 2,
      'messages_collected': 1,
      'cap_hit': False,
      'summary_text': 'hi',
      'model': 'gpt',
      'role': 'role',
    }

class StubPersonasModule:
  def __init__(self, response=None):
    self.calls = []
    self._response = response

  async def on_ready(self):
    pass

  async def persona_response(self, persona, message, guild_id=None, channel_id=None, user_id=None):
    self.calls.append((persona, message, guild_id, channel_id, user_id))
    if self._response is None:
      return {
        'persona': persona,
        'response_text': 'persona reply',
        'model': 'gpt',
        'role': 'role',
      }
    result = dict(self._response)
    result.setdefault('persona', persona)
    return result


class StubDiscordPersonasModule:
  def __init__(self, personas):
    self.personas = personas
    self.calls = 0

  async def on_ready(self):
    pass

  async def list_personas(self):
    self.calls += 1
    return self.personas

def test_summarize_channel_handler():
  app = FastAPI()
  module = StubModule()
  app.state.discord_chat = module

  async def fake_unbox(request):
    return (
      RPCRequest(op='urn:discord:chat:summarize_channel:1', payload={'guild_id': 1, 'channel_id': 2, 'hours': 1, 'user_id': 3}),
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
  assert module.summary_called
  data = resp.json()
  expected = {
    "summary": "hi",
    "messages_collected": 1,
    "token_count_estimate": 2,
    "cap_hit": False,
    "model": "gpt",
    "role": "role",
  }
  assert data["payload"] == expected
  assert module.summary_args == (1, 2, 1, 3)

  chat_services.unbox_request = original


def test_persona_response_handler():
  app = FastAPI()
  module = StubPersonasModule()
  app.state.personas = module

  async def fake_unbox(request):
    return (
      RPCRequest(
        op='urn:discord:chat:persona_response:1',
        payload={
          'persona': 'stark',
          'message': 'Tell me about rain',
          'guild_id': 1,
          'channel_id': 2,
          'user_id': 3,
        },
      ),
      AuthContext(),
      [],
    )

  original = chat_services.unbox_request
  chat_services.unbox_request = fake_unbox

  @app.post('/rpc')
  async def rpc_endpoint(request: Request):
    return await chat_services.discord_chat_persona_response_v1(request)

  client = TestClient(app)
  resp = client.post('/rpc', json={'op': 'urn:discord:chat:persona_response:1'})
  assert resp.status_code == 200
  assert module.calls == [('stark', 'Tell me about rain', 1, 2, 3)]
  data = resp.json()
  expected = {
    'persona': 'stark',
    'persona_response_text': 'persona reply',
    'model': 'gpt',
    'role': 'role',
  }
  assert data['payload'] == expected

  chat_services.unbox_request = original


def test_persona_response_handler_uses_view_persona_details():
  app = FastAPI()
  module = StubPersonasModule(
    {
      'response_text': 'persona reply',
      'model': None,
      'role': '',
    },
  )
  app.state.personas = module
  personas_module = StubDiscordPersonasModule(
    [
      {
        'recid': 1,
        'name': 'Stark',
        'prompt': 'be stark',
        'tokens': 128,
        'models_recid': 2,
        'model': 'gpt-4o',
      }
    ]
  )
  app.state.discord_personas = personas_module

  async def fake_unbox(request):
    return (
      RPCRequest(
        op='urn:discord:chat:persona_response:1',
        payload={
          'persona': 'stark',
          'message': 'Tell me about rain',
          'guild_id': 1,
          'channel_id': 2,
          'user_id': 3,
        },
      ),
      AuthContext(),
      [],
    )

  original = chat_services.unbox_request
  chat_services.unbox_request = fake_unbox

  @app.post('/rpc')
  async def rpc_endpoint(request: Request):
    return await chat_services.discord_chat_persona_response_v1(request)

  client = TestClient(app)
  resp = client.post('/rpc', json={'op': 'urn:discord:chat:persona_response:1'})
  assert resp.status_code == 200
  assert personas_module.calls == 1
  assert module.calls == [('Stark', 'Tell me about rain', 1, 2, 3)]
  data = resp.json()
  expected = {
    'persona': 'Stark',
    'persona_response_text': 'persona reply',
    'model': 'gpt-4o',
    'role': 'be stark',
  }
  assert data['payload'] == expected

  chat_services.unbox_request = original
