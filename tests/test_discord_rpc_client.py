import asyncio
from types import SimpleNamespace

import pytest
from fastapi import FastAPI

from server.modules.discord_bot_module import DiscordBotModule


def test_call_rpc_populates_auth_context_and_metadata():
  app = FastAPI()
  module = DiscordBotModule(app)

  import rpc

  class StubAuth:
    async def get_discord_user_security(self, discord_id: str):
      return (f'user-{discord_id}', ['ROLE_REGISTERED'], 0x7)

  app.state.auth = StubAuth()

  captured: dict[str, SimpleNamespace] = {}

  original_handlers = dict(rpc.HANDLERS)

  async def _handler(parts, request):
    captured['request'] = request
    return SimpleNamespace(payload={'ok': True}, op='urn:test:ops:trigger:1', version=1)

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
    rpc.HANDLERS.clear()
    rpc.HANDLERS.update(original_handlers)

  assert hasattr(response, 'payload')
  assert response.payload['ok'] is True

  request = captured['request']
  rpc_request = request.state.rpc_request
  auth_ctx = request.state.auth_ctx
  metadata = request.state.discord_metadata

  assert rpc_request.user_guid == 'user-7'
  assert rpc_request.roles == ['ROLE_REGISTERED']
  assert rpc_request.role_mask == 0x7
  assert auth_ctx.user_guid == 'user-7'
  assert auth_ctx.roles == ['ROLE_REGISTERED']
  assert auth_ctx.role_mask == 0x7
  assert metadata == {'user_id': '7', 'guild_id': '9', 'channel_id': '11'}
  assert request.headers['x-discord-id'] == '7'
  assert request.headers['x-discord-guild-id'] == '9'
  assert request.headers['x-discord-channel-id'] == '11'


def test_call_rpc_requires_user_metadata():
  app = FastAPI()
  module = DiscordBotModule(app)

  import rpc

  class StubAuth:
    async def get_discord_user_security(self, discord_id: str):
      return ('guid', ['ROLE_REGISTERED'], 1)

  app.state.auth = StubAuth()

  with pytest.raises(RuntimeError, match='Discord user metadata is required'):
    asyncio.run(module.call_rpc('urn:test:ops:trigger:1'))


def test_call_rpc_raises_when_security_profile_missing():
  app = FastAPI()
  module = DiscordBotModule(app)

  import rpc

  class StubAuth:
    async def get_discord_user_security(self, discord_id: str):
      return ('', [], 0)

  app.state.auth = StubAuth()

  with pytest.raises(RuntimeError, match='No security profile for Discord user'):
    asyncio.run(module.call_rpc('urn:test:ops:trigger:1', metadata={'user_id': '999'}))
