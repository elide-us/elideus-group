import asyncio
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

  async def queue_channel_message(self, channel_id: int, message: str):
    self.channel_messages.append((channel_id, message))

  async def queue_user_message(self, user_id: int, message: str):
    self.user_messages.append((user_id, message))


class DummyChannel:
  def __init__(self, id: int = 2):
    self.id = id
    self.sent: list[str] = []

  async def send(self, content):
    self.sent.append(content)


class DummyAuthor:
  def __init__(self):
    self.id = 3
    self.bot = False


class DummyMessage:
  def __init__(self, content: str, channel: DummyChannel, author: DummyAuthor, guild_id: int = 1, state=None):
    self.content = content
    self.channel = channel
    self.author = author
    self.guild = SimpleNamespace(id=guild_id)
    self._state = state or SimpleNamespace()
    self.attachments = []
    self.id = 1


def _setup_bot():
  app = FastAPI()
  module = DiscordBotModule(app)
  module.bot = module._init_discord_bot('!')
  module.mark_ready()
  output = DummyOutput()
  module.output_module = output
  app.state.discord_output = output

  social = SocialInputModule(app)
  social.discord = module
  module.register_social_input_module(social)

  provider = DiscordInputProvider(social, module)
  asyncio.run(social.register_provider(provider))
  return module, output


def test_summarize_macro_dm(monkeypatch):
  module, output = _setup_bot()
  module.bot._connection.user = SimpleNamespace(id=0)

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

  channel = DummyChannel()
  author = DummyAuthor()
  message = DummyMessage("!summarize 2", channel, author, state=module.bot._connection)
  asyncio.run(module.bot.process_commands(message))

  assert dummy_dispatch.calls
  _, op, payload, metadata = dummy_dispatch.calls[0]
  assert op == "urn:discord:chat:summarize_channel:1"
  assert payload["hours"] == 2
  assert payload["user_id"] == author.id
  assert metadata["user_id"] == author.id
  assert output.user_messages == []
  assert output.channel_messages == []
  assert channel.sent == []
