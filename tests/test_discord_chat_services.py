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
    self.delivery_calls = []

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

  async def deliver_summary(
    self,
    *,
    guild_id,
    channel_id,
    user_id,
    summary_text,
    ack_message,
    success,
    reason=None,
    messages_collected=None,
    token_count_estimate=None,
    cap_hit=None,
  ):
    self.delivery_calls.append(
      {
        'guild_id': guild_id,
        'channel_id': channel_id,
        'user_id': user_id,
        'summary_text': summary_text,
        'ack_message': ack_message,
        'success': success,
        'reason': reason,
        'messages_collected': messages_collected,
        'token_count_estimate': token_count_estimate,
        'cap_hit': cap_hit,
      }
    )
    return {
      'success': bool(success and summary_text),
      'queue_id': 'queue-123',
      'summary_success': success,
      'dm_enqueued': bool(summary_text),
      'channel_ack_enqueued': bool(ack_message),
      'reason': reason,
      'ack_message': ack_message,
      'messages_collected': messages_collected,
      'token_count_estimate': token_count_estimate,
      'cap_hit': cap_hit,
    }

class StubOpenAIModule:
  def __init__(
    self,
    response=None,
    *,
    persona_details=None,
    history=None,
    conversation_id=777,
    generate_response=None,
  ):
    self.calls = []
    self.log_calls = []
    self.finalize_calls = []
    self.history_calls = []
    self.generate_calls = []
    self._response = response
    self._conversation_id = conversation_id
    self._persona_details = persona_details or {
      'stark': {
        'recid': 1,
        'models_recid': 2,
        'prompt': 'be stark',
        'tokens': 128,
        'model': 'gpt-4o-mini',
        'name': 'Stark',
      }
    }
    self._history = history or [
      {'role': 'user', 'content': 'Hi'},
      {'role': 'assistant', 'content': 'Hello there'},
    ]
    self._generate_response = generate_response or {
      'content': 'generated reply',
      'model': 'gpt-4o-mini',
      'usage': {'total_tokens': 50},
    }

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
    return dict(self._response)

  async def get_persona_definition(self, persona):
    key = persona.strip().lower()
    return self._persona_details.get(key)

  async def log_persona_conversation_input(
    self,
    personas_recid,
    models_recid,
    guild_id,
    channel_id,
    user_id,
    input_data,
    tokens,
  ):
    self.log_calls.append(
      {
        'personas_recid': personas_recid,
        'models_recid': models_recid,
        'guild_id': guild_id,
        'channel_id': channel_id,
        'user_id': user_id,
        'input_data': input_data,
        'tokens': tokens,
      }
    )
    return self._conversation_id

  async def finalize_persona_conversation(self, recid, output_data, tokens):
    self.finalize_calls.append(
      {
        'recid': recid,
        'output_data': output_data,
        'tokens': tokens,
      }
    )

  async def get_recent_persona_conversation_history(
    self,
    *,
    personas_recid,
    lookback_days,
    limit,
  ):
    self.history_calls.append(
      {
        'personas_recid': personas_recid,
        'lookback_days': lookback_days,
        'limit': limit,
      }
    )
    return list(self._history)

  async def generate_chat(self, **kwargs):
    self.generate_calls.append(kwargs)
    return dict(self._generate_response)


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
  assert len(module.delivery_calls) == 1
  delivery = module.delivery_calls[0]
  assert delivery['summary_text'] == 'hi'
  assert delivery['ack_message'] == 'Summary queued for delivery to <@3>.'
  data = resp.json()
  expected = {
    "success": True,
    "queue_id": "queue-123",
    "messages_collected": 1,
    "token_count_estimate": 2,
    "cap_hit": False,
    "dm_enqueued": True,
    "channel_ack_enqueued": True,
    "reason": None,
    "ack_message": "Summary queued for delivery to <@3>.",
  }
  assert data["payload"] == expected
  assert module.summary_args == (1, 2, 1, 3)

  chat_services.unbox_request = original


def test_persona_response_handler():
  app = FastAPI()
  module = StubOpenAIModule()
  app.state.openai = module

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


def test_persona_response_handler_uses_openai_results():
  app = FastAPI()
  module = StubOpenAIModule(
    {
      'persona': 'Stark',
      'response_text': 'persona reply',
      'model': 'gpt-4o',
      'role': 'be stark',
    },
  )
  app.state.openai = module

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
    'persona': 'Stark',
    'persona_response_text': 'persona reply',
    'model': 'gpt-4o',
    'role': 'be stark',
  }
  assert data['payload'] == expected

  chat_services.unbox_request = original


def test_get_conversation_history_handler_uses_openai_module():
  app = FastAPI()
  module = StubOpenAIModule(
    persona_details={
      'helper': {
        'recid': 5,
        'models_recid': 9,
        'model': 'gpt-4o-mini',
        'tokens': 64,
        'name': 'Helper',
      }
    },
    history=[
      {'role': 'user', 'content': 'Hello'},
      {'role': 'assistant', 'content': 'Hi there'},
    ],
  )
  app.state.openai = module

  async def fake_unbox(request):
    return (
      RPCRequest(
        op='urn:discord:chat:get_conversation_history:1',
        payload={'persona': 'Helper'},
      ),
      AuthContext(),
      [],
    )

  original = chat_services.unbox_request
  chat_services.unbox_request = fake_unbox

  @app.post('/rpc')
  async def rpc_endpoint(request: Request):
    return await chat_services.discord_chat_get_conversation_history_v1(request)

  client = TestClient(app)
  resp = client.post('/rpc', json={'op': 'urn:discord:chat:get_conversation_history:1'})
  assert resp.status_code == 200
  data = resp.json()['payload']
  assert data['success'] is True
  assert data['conversation_history'] == module._history
  assert data['personas_recid'] == 5
  assert data['models_recid'] == 9
  assert module.history_calls == [
    {'personas_recid': 5, 'lookback_days': 30, 'limit': 5}
  ]

  chat_services.unbox_request = original


def test_insert_conversation_input_handler_logs_via_module():
  app = FastAPI()
  module = StubOpenAIModule(
    persona_details={
      'helper': {
        'recid': 7,
        'models_recid': 11,
        'model': 'gpt-4o-mini',
        'tokens': 256,
        'name': 'Helper',
      }
    },
    conversation_id=4321,
  )
  app.state.openai = module

  async def fake_unbox(request):
    return (
      RPCRequest(
        op='urn:discord:chat:insert_conversation_input:1',
        payload={
          'persona': 'helper',
          'message': 'Tell me something',
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
    return await chat_services.discord_chat_insert_conversation_input_v1(request)

  client = TestClient(app)
  resp = client.post('/rpc', json={'op': 'urn:discord:chat:insert_conversation_input:1'})
  assert resp.status_code == 200
  data = resp.json()['payload']
  assert data['success'] is True
  assert data['conversation_reference'] == 4321
  assert module.log_calls == [
    {
      'personas_recid': 7,
      'models_recid': 11,
      'guild_id': 1,
      'channel_id': 2,
      'user_id': 3,
      'input_data': 'Tell me something',
      'tokens': None,
    }
  ]

  chat_services.unbox_request = original


def test_generate_persona_response_handler_finalizes_conversation():
  app = FastAPI()
  module = StubOpenAIModule(
    persona_details={
      'helper': {
        'recid': 12,
        'models_recid': 14,
        'model': 'gpt-4o-mini',
        'tokens': 256,
        'name': 'Helper',
        'prompt': 'Assist helpfully',
      }
    },
    generate_response={
      'content': 'Final reply',
      'model': 'gpt-4.1',
      'usage': {'total_tokens': 33},
    },
  )
  app.state.openai = module

  async def fake_unbox(request):
    return (
      RPCRequest(
        op='urn:discord:chat:generate_persona_response:1',
        payload={
          'persona': 'helper',
          'message': 'What is up?',
          'conversation_reference': 9001,
        },
      ),
      AuthContext(),
      [],
    )

  original = chat_services.unbox_request
  chat_services.unbox_request = fake_unbox

  @app.post('/rpc')
  async def rpc_endpoint(request: Request):
    return await chat_services.discord_chat_generate_persona_response_v1(request)

  client = TestClient(app)
  resp = client.post('/rpc', json={'op': 'urn:discord:chat:generate_persona_response:1'})
  assert resp.status_code == 200
  payload = resp.json()['payload']
  assert payload['success'] is True
  assert payload['conversation_reference'] == 9001
  assert module.finalize_calls == [
    {'recid': 9001, 'output_data': 'Final reply', 'tokens': 33}
  ]
  assert module.generate_calls

  chat_services.unbox_request = original
