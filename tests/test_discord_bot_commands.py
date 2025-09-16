import asyncio
import json
from types import SimpleNamespace

from fastapi import FastAPI

from server.modules.discord_module import DiscordModule


class DummyHistory:
  def __aiter__(self):
    return self

  async def __anext__(self):
    raise StopAsyncIteration


class DummyChannel:
  def __init__(self, id: int = 2):
    self.id = id
    self.sent: list[str] = []
    self.history_called = False

  async def send(self, content):
    self.sent.append(content)

  def history(self, limit=1):
    self.history_called = True
    return DummyHistory()


class DummyDMChannel(DummyChannel):
  pass


class DummyAuthor:
  def __init__(self):
    self.id = 3
    self.dm_channel = DummyDMChannel()

  async def send(self, content):
    await self.dm_channel.send(content)


def test_summarize_command(monkeypatch):
  app = FastAPI()
  module = DiscordModule(app)
  module.bot = module._init_discord_bot('!')
  module._init_bot_routes()

  async def dummy_handle(req):
    body = await req.body()
    dummy_handle.body = json.loads(body.decode())
    dummy_handle.called = True
    class DummyResp:
      payload = {
        "summary": "hi",
        "messages_collected": 1,
        "token_count_estimate": 2,
        "model": "gpt",
        "role": "role",
      }
    return DummyResp()
  dummy_handle.called = False
  dummy_handle.body = None
  import importlib
  rpc_mod = importlib.import_module("rpc.handler")
  monkeypatch.setattr(rpc_mod, "handle_rpc_request", dummy_handle)

  ctx = SimpleNamespace(
    guild=SimpleNamespace(id=1),
    channel=DummyChannel(),
    author=DummyAuthor(),
  )
  ctx.send = ctx.channel.send

  cmd = module.bot.get_command("summarize")
  asyncio.run(cmd.callback(ctx, hours="2"))
  assert dummy_handle.called
  assert dummy_handle.body["op"] == "urn:discord:chat:summarize_channel:1"
  assert dummy_handle.body["payload"]["hours"] == 2
  assert dummy_handle.body["payload"]["user_id"] == ctx.author.id
  assert ctx.author.dm_channel.sent == ["hi"]
  assert ctx.author.dm_channel.history_called


def test_summarize_command_usage_error(monkeypatch):
  app = FastAPI()
  module = DiscordModule(app)
  module.bot = module._init_discord_bot('!')
  module._init_bot_routes()
  ctx = SimpleNamespace(
    guild=SimpleNamespace(id=1),
    channel=DummyChannel(),
    author=DummyAuthor(),
  )
  ctx.send = ctx.channel.send
  cmd = module.bot.get_command("summarize")
  asyncio.run(cmd.callback(ctx, hours="bad"))
  assert ctx.channel.sent == ["Usage: !summarize <hours>"]


def test_summarize_command_empty_history(monkeypatch):
  app = FastAPI()
  module = DiscordModule(app)
  module.bot = module._init_discord_bot('!')
  module._init_bot_routes()

  async def dummy_handle(req):
    body = await req.body()
    dummy_handle.body = json.loads(body.decode())
    class DummyResp:
      payload = {
        "summary": "",
        "messages_collected": 0,
        "token_count_estimate": 0,
        "cap_hit": False,
        "model": "gpt",
        "role": "role",
      }
    return DummyResp()
  dummy_handle.body = None
  import importlib
  rpc_mod = importlib.import_module("rpc.handler")
  monkeypatch.setattr(rpc_mod, "handle_rpc_request", dummy_handle)

  ctx = SimpleNamespace(
    guild=SimpleNamespace(id=1),
    channel=DummyChannel(),
    author=DummyAuthor(),
  )
  ctx.send = ctx.channel.send
  cmd = module.bot.get_command("summarize")
  asyncio.run(cmd.callback(ctx, hours="1"))
  assert dummy_handle.body["payload"]["user_id"] == ctx.author.id
  assert ctx.channel.sent == ["No messages found in the specified time range"]


def test_summarize_command_cap_hit(monkeypatch):
  app = FastAPI()
  module = DiscordModule(app)
  module.bot = module._init_discord_bot('!')
  module._init_bot_routes()

  async def dummy_handle(req):
    body = await req.body()
    dummy_handle.body = json.loads(body.decode())
    class DummyResp:
      payload = {
        "summary": "hi",
        "messages_collected": 5000,
        "token_count_estimate": 2,
        "cap_hit": True,
        "model": "gpt",
        "role": "role",
      }
    return DummyResp()
  dummy_handle.body = None
  import importlib
  rpc_mod = importlib.import_module("rpc.handler")
  monkeypatch.setattr(rpc_mod, "handle_rpc_request", dummy_handle)

  ctx = SimpleNamespace(
    guild=SimpleNamespace(id=1),
    channel=DummyChannel(),
    author=DummyAuthor(),
  )
  ctx.send = ctx.channel.send
  cmd = module.bot.get_command("summarize")
  asyncio.run(cmd.callback(ctx, hours="1"))
  assert dummy_handle.body["payload"]["user_id"] == ctx.author.id
  assert ctx.channel.sent == ["Channel too active to summarize; message cap hit"]


def test_summarize_command_transient_error(monkeypatch):
  app = FastAPI()
  module = DiscordModule(app)
  module.bot = module._init_discord_bot('!')
  module._init_bot_routes()

  async def dummy_handle(req):
    body = await req.body()
    dummy_handle.body = json.loads(body.decode())
    raise RuntimeError("boom")
  dummy_handle.body = None
  import importlib
  rpc_mod = importlib.import_module("rpc.handler")
  monkeypatch.setattr(rpc_mod, "handle_rpc_request", dummy_handle)

  ctx = SimpleNamespace(
    guild=SimpleNamespace(id=1),
    channel=DummyChannel(),
    author=DummyAuthor(),
  )
  ctx.send = ctx.channel.send
  cmd = module.bot.get_command("summarize")
  asyncio.run(cmd.callback(ctx, hours="1"))
  assert dummy_handle.body["payload"]["user_id"] == ctx.author.id
  assert ctx.channel.sent == ["Failed to fetch messages. Please try again later."]


def test_persona_command(monkeypatch):
  app = FastAPI()
  module = DiscordModule(app)
  module.bot = module._init_discord_bot('!')
  module._init_bot_routes()

  async def dummy_handle(req):
    body = await req.body()
    dummy_handle.body = json.loads(body.decode())
    dummy_handle.called = True
    class DummyResp:
      payload = {
        "persona": "stark",
        "persona_response_text": "It rains",
        "model": "gpt",
        "role": "role",
      }
    return DummyResp()
  dummy_handle.called = False
  dummy_handle.body = None
  import importlib
  rpc_mod = importlib.import_module("rpc.handler")
  monkeypatch.setattr(rpc_mod, "handle_rpc_request", dummy_handle)

  ctx = SimpleNamespace(
    guild=SimpleNamespace(id=1),
    channel=DummyChannel(),
    author=DummyAuthor(),
  )
  ctx.send = ctx.channel.send

  cmd = module.bot.get_command("persona")
  asyncio.run(cmd.callback(ctx, text="stark Tell me about rain"))
  assert dummy_handle.called
  assert dummy_handle.body["op"] == "urn:discord:chat:persona_response:1"
  assert dummy_handle.body["payload"] == {
    "persona": "stark",
    "message": "Tell me about rain",
    "guild_id": 1,
    "channel_id": ctx.channel.id,
    "user_id": ctx.author.id,
  }
  assert ctx.channel.sent == ["It rains"]
  assert ctx.channel.history_called


def test_persona_command_usage_error(monkeypatch):
  app = FastAPI()
  module = DiscordModule(app)
  module.bot = module._init_discord_bot('!')
  module._init_bot_routes()

  import importlib
  rpc_mod = importlib.import_module("rpc.handler")

  async def fail_handle(*args, **kwargs):
    raise AssertionError("should not call RPC")

  monkeypatch.setattr(rpc_mod, "handle_rpc_request", fail_handle)

  ctx = SimpleNamespace(
    guild=SimpleNamespace(id=1),
    channel=DummyChannel(),
    author=DummyAuthor(),
  )
  ctx.send = ctx.channel.send

  cmd = module.bot.get_command("persona")
  asyncio.run(cmd.callback(ctx, text="stark"))
  assert ctx.channel.sent == ["Usage: !persona <name> <message>"]
  assert not ctx.channel.history_called


def test_uwu_command(monkeypatch):
  app = FastAPI()
  module = DiscordModule(app)
  module.bot = module._init_discord_bot('!')
  module._init_bot_routes()

  async def dummy_handle(req):
    body = await req.body()
    dummy_handle.body = json.loads(body.decode())
    dummy_handle.called = True
    class DummyResp:
      payload = {
        "uwu_response_text": "uwu hi",
        "token_count_estimate": 3,
      }
    return DummyResp()
  dummy_handle.called = False
  dummy_handle.body = None
  import importlib
  rpc_mod = importlib.import_module("rpc.handler")
  monkeypatch.setattr(rpc_mod, "handle_rpc_request", dummy_handle)

  ctx = SimpleNamespace(
    guild=SimpleNamespace(id=1),
    channel=DummyChannel(),
    author=DummyAuthor(),
  )
  ctx.send = ctx.channel.send

  cmd = module.bot.get_command("uwu")
  asyncio.run(cmd.callback(ctx, text="hello world"))
  assert dummy_handle.called
  assert dummy_handle.body["op"] == "urn:discord:chat:uwu_chat:1"
  assert dummy_handle.body["payload"]["message"] == "hello world"
  assert ctx.channel.sent == ["uwu hi"]
  assert ctx.channel.history_called

