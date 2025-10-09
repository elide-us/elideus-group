import asyncio
from types import SimpleNamespace

from fastapi import FastAPI

from server.modules.discord_bot_module import DiscordBotModule


async def _capture_handler(parts, request, captured):
  captured['request'] = request
  return SimpleNamespace(payload={'ok': True}, op='urn:test:ops:trigger:1', version=1)


def test_call_rpc_attaches_discord_metadata():
  app = FastAPI()
  module = DiscordBotModule(app)

  import rpc

  class StubAuth:
    async def get_discord_user_security(self, discord_id: str):
      return (f'user-{discord_id}', ['ROLE_REGISTERED'], 0x1)

  app.state.auth = StubAuth()

  captured: dict[str, SimpleNamespace] = {}

  original_handlers = rpc.HANDLERS.copy()

  async def _handler(parts, request):
    return await _capture_handler(parts, request, captured)

  rpc.HANDLERS['test'] = _handler

  try:
    response = asyncio.run(
      module.call_rpc(
        'urn:test:ops:trigger:1',
        {'foo': 'bar'},
        metadata={'user_id': 7, 'guild_id': 9, 'channel_id': 11},
      )
    )
  finally:
    rpc.HANDLERS = original_handlers

  assert hasattr(response, 'payload')
  assert response.payload['ok'] is True

  request = captured['request']
  metadata = getattr(request.state, 'discord_metadata', None)
  assert metadata == {'user_id': '7', 'guild_id': '9', 'channel_id': '11'}
  assert request.headers['x-discord-id'] == '7'
  assert request.headers['x-discord-guild-id'] == '9'
  assert request.headers['x-discord-channel-id'] == '11'
