import asyncio, pathlib, sys, types
from types import SimpleNamespace

from fastapi import FastAPI

from server.modules.discord_bot_module import DiscordBotModule
from server.modules.discord_chat_module import DiscordChatModule
from server.modules.providers.social.discord_input_provider import DiscordInputProvider
from server.modules.social_input_module import SocialInputModule

root_path = pathlib.Path(__file__).resolve().parent.parent
pkg = types.ModuleType('rpc')
pkg.__path__ = [str(root_path / 'rpc')]
pkg.HANDLERS = {}
sys.modules.setdefault('rpc', pkg)


class DummyOutput:
  def __init__(self):
    self.channel_messages: list[tuple[int, str]] = []
    self.user_messages: list[tuple[int, str]] = []

  async def send_to_channel(self, channel_id: int, message: str):
    self.channel_messages.append((channel_id, message))

  async def send_to_user(self, user_id: int, message: str):
    self.user_messages.append((user_id, message))

  async def queue_channel_message(self, channel_id: int, message: str):
    self.channel_messages.append((channel_id, message))

  async def queue_user_message(self, user_id: int, message: str):
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

  chat_module = DiscordChatModule(app)
  chat_module.discord = bot_module
  app.state.discord_chat = chat_module
  chat_module.mark_ready()

  class DummyOpenAI:
    def __init__(self):
      self.persona_details = {
        "recid": 1,
        "models_recid": 2,
        "prompt": "be helpful",
        "tokens": 512,
        "model": "gpt-4o-mini",
      }

    async def on_ready(self):
      return None

    async def get_persona_definition(self, persona):
      details = dict(self.persona_details)
      details["name"] = persona
      return details

    async def get_recent_persona_conversation_history(self, personas_recid, lookback_days, limit):
      return []

    async def get_recent_channel_messages(self, *args, **kwargs):  # pragma: no cover - legacy compatibility
      return []

    async def log_persona_conversation_input(self, personas_recid, models_recid, guild_id, channel_id, user_id, message, extra):
      return 123

    async def generate_chat(self, **kwargs):
      return {"content": "Hello!", "model": "gpt-4o-mini", "usage": {"total_tokens": 33}}

    async def finalize_persona_conversation(self, conversation_id, output_data, tokens):
      return None

  app.state.openai = DummyOpenAI()

  return bot_module, provider, output


def _make_ctx():
  guild = SimpleNamespace(id=1)
  channel = SimpleNamespace(id=2)
  author = SimpleNamespace(id=3)
  return SimpleNamespace(guild=guild, channel=channel, author=author)


def test_summarize_command(monkeypatch):
  bot_module, provider, output = _setup_bot()

  class DummyResp:
    payload = {
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

  async def dummy_dispatch(app_obj, op, payload=None, *, discord_ctx=None, headers=None):
    dummy_dispatch.calls.append((app_obj, op, payload, discord_ctx))
    return DummyResp()

  dummy_dispatch.calls = []
  import importlib
  rpc_mod = importlib.import_module("rpc.handler")
  monkeypatch.setattr(rpc_mod, "dispatch_rpc_op", dummy_dispatch)

  ctx = _make_ctx()
  cmd = bot_module.bot.get_command("summarize")
  asyncio.run(cmd.callback(ctx, hours="2"))

  assert dummy_dispatch.calls
  _, op, payload, metadata = dummy_dispatch.calls[0]
  assert op == "urn:discord:chat:summarize_channel:1"
  assert payload["hours"] == 2
  assert payload["user_id"] == ctx.author.id
  assert metadata["guild_id"] == ctx.guild.id
  assert metadata["channel_id"] == ctx.channel.id
  assert metadata["user_id"] == ctx.author.id
  assert output.user_messages == []
  assert output.channel_messages == []


def test_summarize_command_usage_error(monkeypatch):
  bot_module, provider, output = _setup_bot()
  ctx = _make_ctx()
  cmd = bot_module.bot.get_command("summarize")
  asyncio.run(cmd.callback(ctx, hours="bad"))
  assert output.channel_messages == [(ctx.channel.id, "Usage: !summarize <hours>")]


def test_summarize_command_empty_history(monkeypatch):
  bot_module, provider, output = _setup_bot()

  class DummyResp:
    payload = {
      "success": False,
      "queue_id": "queue-123",
      "messages_collected": 0,
      "token_count_estimate": 0,
      "cap_hit": False,
      "dm_enqueued": False,
      "channel_ack_enqueued": True,
      "reason": "no_messages",
      "ack_message": "No messages found in the specified time range",
    }

  async def dummy_dispatch(app_obj, op, payload=None, *, discord_ctx=None, headers=None):
    dummy_dispatch.calls.append((app_obj, op, payload, discord_ctx))
    return DummyResp()

  dummy_dispatch.calls = []
  import importlib
  rpc_mod = importlib.import_module("rpc.handler")
  monkeypatch.setattr(rpc_mod, "dispatch_rpc_op", dummy_dispatch)

  ctx = _make_ctx()
  cmd = bot_module.bot.get_command("summarize")
  asyncio.run(cmd.callback(ctx, hours="1"))

  assert dummy_dispatch.calls
  _, _, payload, metadata = dummy_dispatch.calls[0]
  assert payload["user_id"] == ctx.author.id
  assert metadata["user_id"] == ctx.author.id
  assert output.channel_messages == [(ctx.channel.id, "No messages found in the specified time range")]


def test_summarize_command_cap_hit(monkeypatch):
  bot_module, provider, output = _setup_bot()

  class DummyResp:
    payload = {
      "success": False,
      "queue_id": "queue-123",
      "messages_collected": 5000,
      "token_count_estimate": 2,
      "cap_hit": True,
      "dm_enqueued": False,
      "channel_ack_enqueued": True,
      "reason": "cap_hit",
      "ack_message": "Channel too active to summarize; message cap hit",
    }

  async def dummy_dispatch(app_obj, op, payload=None, *, discord_ctx=None, headers=None):
    dummy_dispatch.calls.append((app_obj, op, payload, discord_ctx))
    return DummyResp()

  dummy_dispatch.calls = []
  import importlib
  rpc_mod = importlib.import_module("rpc.handler")
  monkeypatch.setattr(rpc_mod, "dispatch_rpc_op", dummy_dispatch)

  ctx = _make_ctx()
  cmd = bot_module.bot.get_command("summarize")
  asyncio.run(cmd.callback(ctx, hours="1"))

  assert dummy_dispatch.calls
  _, _, payload, metadata = dummy_dispatch.calls[0]
  assert payload["user_id"] == ctx.author.id
  assert metadata["user_id"] == ctx.author.id
  assert output.channel_messages == [(ctx.channel.id, "Channel too active to summarize; message cap hit")]


def test_summarize_command_transient_error(monkeypatch):
  bot_module, provider, output = _setup_bot()

  async def dummy_dispatch(app_obj, op, payload=None, *, discord_ctx=None, headers=None):
    dummy_dispatch.calls.append((app_obj, op, payload, discord_ctx))
    raise RuntimeError("boom")

  dummy_dispatch.calls = []
  import importlib
  rpc_mod = importlib.import_module("rpc.handler")
  monkeypatch.setattr(rpc_mod, "dispatch_rpc_op", dummy_dispatch)

  ctx = _make_ctx()
  cmd = bot_module.bot.get_command("summarize")
  asyncio.run(cmd.callback(ctx, hours="1"))

  assert dummy_dispatch.calls
  _, _, payload, metadata = dummy_dispatch.calls[0]
  assert payload["user_id"] == ctx.author.id
  assert metadata["user_id"] == ctx.author.id
  assert output.channel_messages == [(ctx.channel.id, "Failed to fetch messages. Please try again later.")]


def test_persona_command_workflow():
  bot_module, provider, output = _setup_bot()

  ctx = _make_ctx()
  cmd = bot_module.bot.get_command("persona")
  asyncio.run(cmd.callback(ctx, request="helper Hello world"))

  assert output.channel_messages == [
    (ctx.channel.id, "Hello!"),
    (ctx.channel.id, "Persona response queued for <@3>."),
  ]


def test_persona_command_usage_error():
  bot_module, provider, output = _setup_bot()
  ctx = _make_ctx()
  cmd = bot_module.bot.get_command("persona")
  asyncio.run(cmd.callback(ctx, request=None))
  assert output.channel_messages == [(ctx.channel.id, "Usage: !persona <persona> <message>")]


def test_persona_command_failure(monkeypatch):
  bot_module, provider, output = _setup_bot()
  module = bot_module.app.state.discord_chat

  async def dummy_handle(**kwargs):
    return {
      "success": False,
      "ack_message": "Persona chat is currently unavailable.",
      "reason": "persona_rpc_failure",
    }

  monkeypatch.setattr(module, "handle_persona_command", dummy_handle)

  ctx = _make_ctx()
  cmd = bot_module.bot.get_command("persona")
  asyncio.run(cmd.callback(ctx, request="helper hi"))

  assert output.channel_messages == [(ctx.channel.id, "Persona chat is currently unavailable.")]

