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
  assert ctx.author.dm_channel.sent == ["hi"]
  assert ctx.author.dm_channel.history_called


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

