import asyncio
from types import SimpleNamespace

from fastapi import FastAPI

from server.modules.discord_bot_module import DiscordBotModule
from server.modules.discord_chat_module import DiscordChatModule
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


def test_persona_command_workflow(monkeypatch):
  bot_module, provider, output = _setup_bot()

  class DummyResp:
    def __init__(self, payload):
      self.payload = payload

  responses = {
    "urn:discord:chat:persona_command:1": {"success": True, "model": "gpt-4o-mini", "max_tokens": 512},
    "urn:discord:chat:get_persona:1": {
      "success": True,
      "persona_details": {"model": "gpt-4o-mini", "tokens": 512},
      "model": "gpt-4o-mini",
      "max_tokens": 512,
    },
    "urn:discord:chat:get_conversation_history:1": {
      "success": True,
      "conversation_history": [{"role": "user", "content": "Hi"}],
    },
    "urn:discord:chat:get_channel_history:1": {
      "success": True,
      "channel_history": [{"author": "user", "content": "Hi"}],
    },
    "urn:discord:chat:insert_conversation_input:1": {
      "success": True,
      "conversation_reference": "conv-1",
    },
    "urn:discord:chat:generate_persona_response:1": {
      "success": True,
      "response": {"text": "Hello!", "model": "gpt-4o-mini"},
      "model": "gpt-4o-mini",
    },
    "urn:discord:chat:deliver_persona_response:1": {
      "success": True,
      "ack_message": "Persona response queued for <@3>.",
      "reason": "persona_response_queued",
    },
  }

  async def dummy_dispatch(app_obj, op, payload=None, *, discord_ctx=None, headers=None):
    dummy_dispatch.calls.append((op, payload, discord_ctx))
    return DummyResp(responses.get(op, {"success": True}))

  dummy_dispatch.calls = []
  import importlib
  rpc_mod = importlib.import_module("rpc.handler")
  monkeypatch.setattr(rpc_mod, "dispatch_rpc_op", dummy_dispatch)

  ctx = _make_ctx()
  cmd = bot_module.bot.get_command("persona")
  asyncio.run(cmd.callback(ctx, request="helper Hello world"))

  assert [call[0] for call in dummy_dispatch.calls] == [
    "urn:discord:chat:persona_command:1",
    "urn:discord:chat:get_persona:1",
    "urn:discord:chat:get_conversation_history:1",
    "urn:discord:chat:get_channel_history:1",
    "urn:discord:chat:insert_conversation_input:1",
    "urn:discord:chat:generate_persona_response:1",
    "urn:discord:chat:deliver_persona_response:1",
  ]
  first_payload = dummy_dispatch.calls[0][1]
  first_metadata = dummy_dispatch.calls[0][2]
  assert first_payload["persona"] == "helper"
  assert first_payload["message"] == "Hello world"
  assert first_metadata == {"guild_id": ctx.guild.id, "channel_id": ctx.channel.id, "user_id": ctx.author.id}
  assert output.channel_messages == [(ctx.channel.id, "Persona response queued for <@3>.")]


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

