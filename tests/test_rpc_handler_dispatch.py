import asyncio

from fastapi import FastAPI

from server.models import RPCResponse


def test_dispatch_rpc_op_uses_discord_metadata():
  app = FastAPI()

  class DummyAuth:
    def __init__(self):
      self.calls = []
      self.role_registered = 0x1
      self.roles = {
        'ROLE_REGISTERED': 0x1,
        'ROLE_DISCORD_BOT': 0x2,
      }

    async def get_discord_user_security(self, discord_id):
      self.calls.append(discord_id)
      return ('guid-123', ['ROLE_REGISTERED', 'ROLE_DISCORD_BOT'], 0x3)

    async def user_has_role(self, guid, mask):
      return True

  app.state.auth = DummyAuth()

  import importlib, sys
  saved_modules = {
    name: mod
    for name, mod in sys.modules.items()
    if name == 'rpc' or name.startswith('rpc.')
  }
  for name in list(saved_modules):
    del sys.modules[name]

  rpc_pkg = importlib.import_module('rpc')
  from rpc.discord.handler import handle_discord_request
  import rpc.discord.command as command_mod
  handler_mod = importlib.import_module('rpc.handler')

  key = ('get_roles', '1')
  captured = {}

  async def dummy_command(request):
    captured['request'] = request
    rpc_request = request.state.rpc_request
    return RPCResponse(op=rpc_request.op, payload={'ok': True})

  orig_dispatch = command_mod.DISPATCHERS.get(key)
  command_mod.DISPATCHERS[key] = dummy_command
  orig_domain = rpc_pkg.HANDLERS.get('discord')
  rpc_pkg.HANDLERS['discord'] = handle_discord_request

  try:
    resp = asyncio.run(
      handler_mod.dispatch_rpc_op(
        app,
        'urn:discord:command:get_roles:1',
        None,
        discord_ctx={'guild_id': 1, 'channel_id': 2, 'user_id': 42},
      )
    )
  finally:
    if orig_dispatch is None:
      del command_mod.DISPATCHERS[key]
    else:
      command_mod.DISPATCHERS[key] = orig_dispatch
    if orig_domain is None:
      del rpc_pkg.HANDLERS['discord']
    else:
      rpc_pkg.HANDLERS['discord'] = orig_domain
    for name in list(sys.modules):
      if name == 'rpc' or name.startswith('rpc.'):
        del sys.modules[name]
    sys.modules.update(saved_modules)

  assert resp.payload['ok']
  assert app.state.auth.calls == ['42']
  request = captured['request']
  ctx = getattr(request.state, 'discord_ctx', None)
  assert getattr(getattr(ctx, 'guild', None), 'id', None) == 1
  assert getattr(getattr(ctx, 'channel', None), 'id', None) == 2
  assert getattr(getattr(ctx, 'author', None), 'id', None) == 42
  rpc_request = request.state.rpc_request
  assert rpc_request.user_guid == 'guid-123'
  assert 'ROLE_DISCORD_BOT' in rpc_request.roles
