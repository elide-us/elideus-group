import asyncio
import sys
import types
from types import SimpleNamespace

from fastapi import FastAPI

from server.modules.providers.social.discord_input_provider import DiscordInputProvider


def test_summarize_command_relies_on_ack(monkeypatch):
  app = FastAPI()

  class DummyChatModule:
    def __init__(self):
      self.deliveries = []

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
      self.deliveries.append(
        {
          'guild_id': guild_id,
          'channel_id': channel_id,
          'user_id': user_id,
          'summary_text': summary_text,
          'ack_message': ack_message,
          'success': success,
          'reason': reason,
        }
      )
      return {
        'success': False,
        'queue_id': 'noop',
        'summary_success': success,
        'dm_enqueued': False,
        'channel_ack_enqueued': bool(ack_message),
        'reason': reason,
        'ack_message': ack_message,
        'messages_collected': messages_collected,
        'token_count_estimate': token_count_estimate,
        'cap_hit': cap_hit,
      }

  class DummyQueue:
    def __init__(self):
      self.calls = []

    async def add(self, *args, **kwargs):
      self.calls.append((args, kwargs))

  class DummyOpenAI:
    def __init__(self):
      self.summary_queue = DummyQueue()

  class DummyDiscord:
    def __init__(self, app):
      self.app = app
      self.sent_user_messages = []
      self.sent_channel_messages = []
      self.rate_limits = []

    def bump_rate_limits(self, guild_id, user_id):
      self.rate_limits.append((guild_id, user_id))

    async def send_channel_message(self, channel_id, message):
      self.sent_channel_messages.append((channel_id, message))

    async def send_user_message(self, user_id, message):
      self.sent_user_messages.append((user_id, message))

  social_module = SimpleNamespace()
  discord = DummyDiscord(app)
  provider = DiscordInputProvider(social_module, discord)

  chat_module = DummyChatModule()
  app.state.discord_chat = chat_module
  app.state.openai = DummyOpenAI()

  ack_payload = {
    'success': True,
    'queue_id': 'queue-123',
    'messages_collected': 5,
    'token_count_estimate': 12,
    'cap_hit': False,
    'dm_enqueued': True,
    'channel_ack_enqueued': True,
    'reason': None,
    'ack_message': 'Summary queued for delivery to <@3>.',
  }

  class DummyResponse:
    def __init__(self, payload):
      self.payload = payload

  async def fake_handle_rpc_request(request):
    return DummyResponse(ack_payload)

  fake_handler_module = types.SimpleNamespace(handle_rpc_request=fake_handle_rpc_request)
  monkeypatch.setitem(sys.modules, 'rpc.handler', fake_handler_module)

  ctx = SimpleNamespace(
    guild=SimpleNamespace(id=1),
    channel=SimpleNamespace(id=2),
    author=SimpleNamespace(id=3),
  )

  asyncio.run(provider._handle_summarize_command(ctx, '2'))

  assert discord.sent_user_messages == []
  assert discord.sent_channel_messages == []
  assert chat_module.deliveries == []
  assert app.state.openai.summary_queue.calls == []
  assert ack_payload['queue_id']
  assert discord.rate_limits == [(1, 3)]
