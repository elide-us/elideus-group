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


class StubPersonaModule:
  def __init__(
    self,
    *,
    get_persona_result=None,
    conversation_history_result=None,
    channel_history_result=None,
    insert_result=None,
    generate_result=None,
    deliver_result=None,
  ):
    self.get_persona_calls = []
    self.get_conversation_history_calls = []
    self.get_channel_history_calls = []
    self.insert_calls = []
    self.generate_calls = []
    self.deliver_calls = []
    self._get_persona_result = get_persona_result or {
      'success': True,
      'persona_details': {'name': 'helper'},
      'model': 'gpt-4o-mini',
      'max_tokens': 256,
    }
    self._conversation_history_result = conversation_history_result or {
      'success': True,
      'conversation_history': [{'role': 'user', 'content': 'Hi'}],
      'personas_recid': 5,
      'models_recid': 9,
    }
    self._channel_history_result = channel_history_result or {
      'success': True,
      'channel_history': [{'author': 'alice', 'content': 'Hello'}],
    }
    self._insert_result = insert_result or {
      'success': True,
      'conversation_reference': 4321,
      'personas_recid': 7,
      'models_recid': 11,
    }
    self._generate_result = generate_result or {
      'success': True,
      'response': {'text': 'Final reply', 'model': 'gpt-4.1'},
      'model': 'gpt-4.1',
      'usage': {'total_tokens': 33},
      'conversation_reference': 9001,
    }
    self._deliver_result = deliver_result or {
      'success': True,
      'reason': 'persona_response_queued',
      'ack_message': 'Persona response queued.',
      'conversation_reference': 9001,
    }

  async def on_ready(self):
    pass

  async def get_persona(self, persona, *, guild_id=None, channel_id=None, user_id=None):
    self.get_persona_calls.append((persona, guild_id, channel_id, user_id))
    return dict(self._get_persona_result)

  async def get_conversation_history(self, persona, *, guild_id=None, channel_id=None, user_id=None, limit=5):
    self.get_conversation_history_calls.append((persona, guild_id, channel_id, user_id, limit))
    return dict(self._conversation_history_result)

  async def get_channel_history(self, guild_id, channel_id, *, persona=None, user_id=None):
    self.get_channel_history_calls.append((guild_id, channel_id, persona, user_id))
    return dict(self._channel_history_result)

  async def insert_conversation_input(
    self,
    persona,
    message,
    *,
    persona_details=None,
    conversation_history=None,
    guild_id=None,
    channel_id=None,
    user_id=None,
  ):
    self.insert_calls.append(
      {
        'persona': persona,
        'message': message,
        'persona_details': persona_details,
        'conversation_history': conversation_history,
        'guild_id': guild_id,
        'channel_id': channel_id,
        'user_id': user_id,
      }
    )
    return dict(self._insert_result)

  async def generate_persona_response(
    self,
    persona,
    message,
    *,
    persona_details=None,
    conversation_history=None,
    channel_history=None,
    model=None,
    max_tokens=None,
    conversation_reference=None,
    personas_recid=None,
    models_recid=None,
    guild_id=None,
    channel_id=None,
    user_id=None,
  ):
    self.generate_calls.append(
      {
        'persona': persona,
        'message': message,
        'persona_details': persona_details,
        'conversation_history': conversation_history,
        'channel_history': channel_history,
        'model': model,
        'max_tokens': max_tokens,
        'conversation_reference': conversation_reference,
        'personas_recid': personas_recid,
        'models_recid': models_recid,
        'guild_id': guild_id,
        'channel_id': channel_id,
        'user_id': user_id,
      }
    )
    return dict(self._generate_result)

  async def deliver_persona_response(
    self,
    *,
    persona,
    response,
    conversation_reference=None,
    guild_id=None,
    channel_id=None,
    user_id=None,
  ):
    self.deliver_calls.append((persona, response, conversation_reference, guild_id, channel_id, user_id))
    return dict(self._deliver_result)


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


def test_get_persona_handler_delegates_to_module():
  app = FastAPI()
  module = StubPersonaModule(
    get_persona_result={
      'success': True,
      'persona_details': {'name': 'Helper'},
      'model': 'gpt-4o-mini',
      'max_tokens': 128,
    }
  )
  app.state.discord_chat = module

  async def fake_unbox(request):
    return (
      RPCRequest(
        op='urn:discord:chat:get_persona:1',
        payload={'persona': 'helper', 'guild_id': 1, 'channel_id': 2, 'user_id': 3},
      ),
      AuthContext(),
      [],
    )

  original = chat_services.unbox_request
  chat_services.unbox_request = fake_unbox

  @app.post('/rpc')
  async def rpc_endpoint(request: Request):
    return await chat_services.discord_chat_get_persona_v1(request)

  client = TestClient(app)
  resp = client.post('/rpc', json={'op': 'urn:discord:chat:get_persona:1'})
  assert resp.status_code == 200
  assert module.get_persona_calls == [('helper', 1, 2, 3)]
  assert resp.json()['payload'] == module._get_persona_result

  chat_services.unbox_request = original


def test_get_conversation_history_handler_uses_module():
  app = FastAPI()
  module = StubPersonaModule(
    conversation_history_result={
      'success': True,
      'conversation_history': [{'role': 'user', 'content': 'Hello'}],
      'personas_recid': 5,
      'models_recid': 9,
    }
  )
  app.state.discord_chat = module

  async def fake_unbox(request):
    return (
      RPCRequest(
        op='urn:discord:chat:get_conversation_history:1',
        payload={'persona': 'Helper', 'guild_id': 1},
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
  assert module.get_conversation_history_calls == [('Helper', 1, None, None, 5)]
  assert resp.json()['payload'] == module._conversation_history_result

  chat_services.unbox_request = original


def test_get_channel_history_handler_delegates_to_module():
  app = FastAPI()
  module = StubPersonaModule(
    channel_history_result={
      'success': True,
      'channel_history': [{'author': 'bob', 'content': 'Ping'}],
    }
  )
  app.state.discord_chat = module

  async def fake_unbox(request):
    return (
      RPCRequest(
        op='urn:discord:chat:get_channel_history:1',
        payload={'guild_id': 10, 'channel_id': 20, 'persona': 'helper'},
      ),
      AuthContext(),
      [],
    )

  original = chat_services.unbox_request
  chat_services.unbox_request = fake_unbox

  @app.post('/rpc')
  async def rpc_endpoint(request: Request):
    return await chat_services.discord_chat_get_channel_history_v1(request)

  client = TestClient(app)
  resp = client.post('/rpc', json={'op': 'urn:discord:chat:get_channel_history:1'})
  assert resp.status_code == 200
  assert module.get_channel_history_calls == [(10, 20, 'helper', None)]
  assert resp.json()['payload'] == module._channel_history_result

  chat_services.unbox_request = original


def test_insert_conversation_input_handler_uses_module():
  app = FastAPI()
  module = StubPersonaModule()
  app.state.discord_chat = module

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
          'persona_details': {'recid': 7, 'models_recid': 11},
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
  assert module.insert_calls == [
    {
      'persona': 'helper',
      'message': 'Tell me something',
      'persona_details': {'recid': 7, 'models_recid': 11},
      'conversation_history': None,
      'guild_id': 1,
      'channel_id': 2,
      'user_id': 3,
    }
  ]
  assert resp.json()['payload'] == module._insert_result

  chat_services.unbox_request = original


def test_generate_persona_response_handler_uses_module():
  app = FastAPI()
  module = StubPersonaModule()
  app.state.discord_chat = module

  async def fake_unbox(request):
    return (
      RPCRequest(
        op='urn:discord:chat:generate_persona_response:1',
        payload={
          'persona': 'helper',
          'message': 'What is up?',
          'conversation_reference': 9001,
          'persona_details': {'recid': 12},
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
  assert module.generate_calls[0]['persona'] == 'helper'
  assert module.generate_calls[0]['message'] == 'What is up?'
  assert resp.json()['payload'] == module._generate_result

  chat_services.unbox_request = original


def test_deliver_persona_response_handler_uses_module():
  app = FastAPI()
  module = StubPersonaModule()
  app.state.discord_chat = module

  async def fake_unbox(request):
    return (
      RPCRequest(
        op='urn:discord:chat:deliver_persona_response:1',
        payload={
          'persona': 'helper',
          'response': {'text': 'hi'},
          'conversation_reference': 9001,
          'channel_id': 22,
          'user_id': 33,
        },
      ),
      AuthContext(),
      [],
    )

  original = chat_services.unbox_request
  chat_services.unbox_request = fake_unbox

  @app.post('/rpc')
  async def rpc_endpoint(request: Request):
    return await chat_services.discord_chat_deliver_persona_response_v1(request)

  client = TestClient(app)
  resp = client.post('/rpc', json={'op': 'urn:discord:chat:deliver_persona_response:1'})
  assert resp.status_code == 200
  assert module.deliver_calls == [('helper', {'text': 'hi'}, 9001, None, 22, 33)]
  assert resp.json()['payload'] == module._deliver_result

  chat_services.unbox_request = original
