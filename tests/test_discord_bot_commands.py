import asyncio
import json
from types import SimpleNamespace

from fastapi import FastAPI

from server.modules.discord_bot_module import DiscordBotModule
from server.modules.providers.social.discord_input_provider import DiscordInputProvider
from server.modules.social_input_module import SocialInputModule


class DummyOutput:
  def __init__(self):
    self.channel_messages: list[tuple[int, str]] = []
    self.user_messages: list[tuple[int, str]] = []

  async def send_to_channel(self, channel_id: int, message: str):
    self.channel_messages.append((channel_id, message))

  async def send_to_user(self, user_id: int, message: str):
    self.user_messages.append((user_id, message))


def _setup_bot():
  app = FastAPI()
  bot_module = DiscordBotModule(app)
  bot_module.bot = bot_module._init_discord_bot('!')
  bot_module.mark_ready()
  output = DummyOutput()
  bot_module.output_module = output
  app.state.discord_output = output

  social = SocialInputModule(app)
  social.discord = bot_module
  bot_module.register_social_input_module(social)

  provider = DiscordInputProvider(social, bot_module)
  asyncio.run(social.register_provider(provider))

  return bot_module, provider, output


def _make_ctx():
  guild = SimpleNamespace(id=1)
  channel = SimpleNamespace(id=2)
  author = SimpleNamespace(id=3)
  return SimpleNamespace(guild=guild, channel=channel, author=author)


def test_summarize_command(monkeypatch):
  bot_module, provider, output = _setup_bot()

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

  ctx = _make_ctx()
  cmd = bot_module.bot.get_command("summarize")
  asyncio.run(cmd.callback(ctx, hours="2"))

  assert dummy_handle.called
  assert dummy_handle.body["op"] == "urn:discord:chat:summarize_channel:1"
  assert dummy_handle.body["payload"]["hours"] == 2
  assert dummy_handle.body["payload"]["user_id"] == ctx.author.id
  assert output.user_messages == [(ctx.author.id, "hi")]
  assert output.channel_messages == []


def test_summarize_command_usage_error(monkeypatch):
  bot_module, provider, output = _setup_bot()
  ctx = _make_ctx()
  cmd = bot_module.bot.get_command("summarize")
  asyncio.run(cmd.callback(ctx, hours="bad"))
  assert output.channel_messages == [(ctx.channel.id, "Usage: !summarize <hours>")]


def test_summarize_command_empty_history(monkeypatch):
  bot_module, provider, output = _setup_bot()

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

  ctx = _make_ctx()
  cmd = bot_module.bot.get_command("summarize")
  asyncio.run(cmd.callback(ctx, hours="1"))

  assert dummy_handle.body["payload"]["user_id"] == ctx.author.id
  assert output.channel_messages == [(ctx.channel.id, "No messages found in the specified time range")]


def test_summarize_command_cap_hit(monkeypatch):
  bot_module, provider, output = _setup_bot()

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

  ctx = _make_ctx()
  cmd = bot_module.bot.get_command("summarize")
  asyncio.run(cmd.callback(ctx, hours="1"))

  assert dummy_handle.body["payload"]["user_id"] == ctx.author.id
  assert output.channel_messages == [(ctx.channel.id, "Channel too active to summarize; message cap hit")]


def test_summarize_command_transient_error(monkeypatch):
  bot_module, provider, output = _setup_bot()

  async def dummy_handle(req):
    body = await req.body()
    dummy_handle.body = json.loads(body.decode())
    raise RuntimeError("boom")

  dummy_handle.body = None
  import importlib
  rpc_mod = importlib.import_module("rpc.handler")
  monkeypatch.setattr(rpc_mod, "handle_rpc_request", dummy_handle)

  ctx = _make_ctx()
  cmd = bot_module.bot.get_command("summarize")
  asyncio.run(cmd.callback(ctx, hours="1"))

  assert dummy_handle.body["payload"]["user_id"] == ctx.author.id
  assert output.channel_messages == [(ctx.channel.id, "Failed to fetch messages. Please try again later.")]


