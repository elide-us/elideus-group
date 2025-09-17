import asyncio
import json
from types import SimpleNamespace

from fastapi import FastAPI

from server.modules.discord_bot_module import DiscordBotModule


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
    self.bot = False
    self.dm_channel = DummyDMChannel()

  async def send(self, content):
    await self.dm_channel.send(content)


class DummyMessage:
  def __init__(self, content: str, channel: DummyChannel, author: DummyAuthor, guild_id: int = 1, state=None):
    self.content = content
    self.channel = channel
    self.author = author
    self.guild = SimpleNamespace(id=guild_id)
    self._state = state or SimpleNamespace()
    self.attachments = []
    self.id = 1


def test_summarize_macro_dm(monkeypatch):
  app = FastAPI()
  module = DiscordBotModule(app)
  module.bot = module._init_discord_bot('!')
  module.bot._connection.user = SimpleNamespace(id=0)
  module._init_bot_routes()

  from discord.ext import commands as dc_commands

  async def fake_send(self, content, **kwargs):
    return await self.channel.send(content)

  monkeypatch.setattr(dc_commands.Context, 'send', fake_send)

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

  channel = DummyChannel()
  author = DummyAuthor()
  message = DummyMessage("!summarize 2", channel, author, state=module.bot._connection)
  asyncio.run(module.bot.process_commands(message))
  assert dummy_handle.called
  assert dummy_handle.body["op"] == "urn:discord:chat:summarize_channel:1"
  assert dummy_handle.body["payload"]["hours"] == 2
  assert dummy_handle.body["payload"]["user_id"] == author.id
  assert author.dm_channel.sent == ["hi"]
  assert author.dm_channel.history_called
  assert channel.sent == []


