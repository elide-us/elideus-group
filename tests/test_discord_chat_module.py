import asyncio
import importlib.util
import pathlib
import sys
import types
from fastapi import FastAPI
from types import SimpleNamespace

root_path = pathlib.Path(__file__).resolve().parent.parent

server_pkg = types.ModuleType('server')
server_pkg.__path__ = [str(root_path / 'server')]
sys.modules.setdefault('server', server_pkg)

helpers_spec = importlib.util.spec_from_file_location('server.helpers', root_path / 'server/helpers/__init__.py')
helpers_pkg = importlib.util.module_from_spec(helpers_spec)
helpers_spec.loader.exec_module(helpers_pkg)
sys.modules['server.helpers'] = helpers_pkg
setattr(server_pkg, 'helpers', helpers_pkg)

helpers_strings_spec = importlib.util.spec_from_file_location('server.helpers.strings', root_path / 'server/helpers/strings.py')
helpers_strings_mod = importlib.util.module_from_spec(helpers_strings_spec)
helpers_strings_spec.loader.exec_module(helpers_strings_mod)
sys.modules['server.helpers.strings'] = helpers_strings_mod
setattr(helpers_pkg, 'strings', helpers_strings_mod)

modules_spec = importlib.util.spec_from_file_location('server.modules', root_path / 'server/modules/__init__.py')
modules_pkg = importlib.util.module_from_spec(modules_spec)
modules_spec.loader.exec_module(modules_pkg)
sys.modules['server.modules'] = modules_pkg
setattr(server_pkg, 'modules', modules_pkg)

discord_chat_spec = importlib.util.spec_from_file_location(
  'server.modules.discord_chat_module',
  root_path / 'server/modules/discord_chat_module.py',
)
discord_chat_mod = importlib.util.module_from_spec(discord_chat_spec)
discord_chat_spec.loader.exec_module(discord_chat_mod)
sys.modules['server.modules.discord_chat_module'] = discord_chat_mod

DiscordChatModule = discord_chat_mod.DiscordChatModule


class PersonaOpenAIStub:
  def __init__(self):
    self.persona_requests: list[str] = []
    self.history_calls: list[dict] = []
    self.log_calls: list[dict] = []
    self.generate_calls: list[dict] = []
    self.finalize_calls: list[dict] = []
    self.persona_details = {
      "recid": 7,
      "models_recid": 11,
      "prompt": "be helpful",
      "tokens": 128,
      "model": "gpt-4o-mini",
      "name": "Helper",
    }
    self.history_entries = [
      {"role": "user", "content": "Hi"},
      {"role": "assistant", "content": "Hello"},
    ]

  async def on_ready(self):
    return None

  async def get_persona_definition(self, name: str):
    self.persona_requests.append(name)
    if name.lower() != "helper":
      return None
    return dict(self.persona_details)

  async def get_recent_persona_conversation_history(self, *, personas_recid: int, lookback_days: int, limit: int):
    self.history_calls.append(
      {
        "personas_recid": personas_recid,
        "lookback_days": lookback_days,
        "limit": limit,
      }
    )
    return list(self.history_entries)

  async def log_persona_conversation_input(
    self,
    personas_recid: int,
    models_recid: int,
    guild_id,
    channel_id,
    user_id,
    input_data,
    tokens,
  ):
    self.log_calls.append(
      {
        "personas_recid": personas_recid,
        "models_recid": models_recid,
        "guild_id": guild_id,
        "channel_id": channel_id,
        "user_id": user_id,
        "input_data": input_data,
        "tokens": tokens,
      }
    )
    return 4242

  async def generate_chat(self, **kwargs):
    self.generate_calls.append(kwargs)
    return {"content": "Final reply", "model": "gpt-4", "usage": {"total_tokens": 33}}

  async def finalize_persona_conversation(self, recid: int, output_data: str, tokens):
    self.finalize_calls.append(
      {
        "recid": recid,
        "output_data": output_data,
        "tokens": tokens,
      }
    )


def test_summarize_channel(monkeypatch):
  app = FastAPI()
  app.state.discord_bot = SimpleNamespace(on_ready=lambda: None)
  module = DiscordChatModule(app)

  async def dummy_fetch(guild_id, channel_id, hours, max_messages=5000):
    msg = SimpleNamespace(content="hello", author=SimpleNamespace(name="Alice"))
    return {"messages": [msg], "cap_hit": False}

  module.fetch_channel_history_backwards = dummy_fetch  # type: ignore

  res = asyncio.run(module.summarize_channel(1, 2, 1))
  assert res["messages_collected"] == 1
  assert "Alice: hello" in res["raw_text_blob"]


def test_summarize_chat_uses_persona_definition(monkeypatch):
  app = FastAPI()
  app.state.discord_bot = SimpleNamespace(on_ready=lambda: None)

  class DummyOpenAI:
    def __init__(self):
      self.client = object()
      self.persona_requests: list[str] = []
      self.chat_calls: list[dict] = []

    async def on_ready(self):
      pass

    async def get_persona_definition(self, name: str):
      self.persona_requests.append(name)
      return {"name": name, "prompt": "sum role", "tokens": 32, "model": "gpt"}

    async def generate_chat(
      self,
      *,
      system_prompt: str,
      user_prompt: str | None = None,
      model: str | None = None,
      max_tokens: int | None = None,
      tools=None,
      prompt_context: str = "",
      persona: str | None = None,
      persona_details: dict | None = None,
      guild_id: int | None = None,
      channel_id: int | None = None,
      user_id: int | None = None,
      input_log: str | None = None,
      token_count: int | None = None,
    ):
      self.chat_calls.append(
        {
          "system_prompt": system_prompt,
          "user_prompt": user_prompt,
          "model": model,
          "max_tokens": max_tokens,
          "persona": persona,
          "guild_id": guild_id,
          "channel_id": channel_id,
          "user_id": user_id,
          "input_log": input_log,
          "token_count": token_count,
        }
      )
      return {"content": "sum", "model": model or "gpt", "role": "assistant"}

  app.state.openai = DummyOpenAI()
  module = DiscordChatModule(app)

  async def dummy_summarize(guild_id, channel_id, hours, max_messages=5000):
    return {
      "messages_collected": 2,
      "token_count_estimate": 5,
      "raw_text_blob": "text",
      "cap_hit": False,
    }

  module.summarize_channel = dummy_summarize  # type: ignore

  res = asyncio.run(module.summarize_chat(1, 2, 3, user_id=4))
  assert res["token_count_estimate"] == 5
  assert res["summary_text"] == "sum"
  assert res["model"] == "gpt"
  assert res["role"] == "sum role"
  assert app.state.openai.persona_requests == ["summarize"]
  last_call = app.state.openai.chat_calls[-1]
  assert last_call["persona"] == "summarize"
  assert last_call["system_prompt"] == "sum role"
  assert last_call["max_tokens"] == 32
  assert last_call["user_id"] == 4


def test_summarize_chat_handles_persona_failure(monkeypatch):
  app = FastAPI()
  app.state.discord_bot = SimpleNamespace(on_ready=lambda: None)

  class DummyOpenAI:
    def __init__(self):
      self.client = object()
      self.calls: list[dict] = []

    async def on_ready(self):
      pass

    async def get_persona_definition(self, name: str):
      raise RuntimeError("db offline")

    async def generate_chat(
      self,
      *,
      system_prompt: str,
      user_prompt: str | None = None,
      model: str | None = None,
      max_tokens: int | None = None,
      tools=None,
      prompt_context: str = "",
      persona: str | None = None,
      persona_details: dict | None = None,
      guild_id: int | None = None,
      channel_id: int | None = None,
      user_id: int | None = None,
      input_log: str | None = None,
      token_count: int | None = None,
    ):
      self.calls.append(
        {
          "system_prompt": system_prompt,
          "persona": persona,
          "max_tokens": max_tokens,
        }
      )
      return {"content": "fallback", "model": "gpt-4o-mini", "role": "assistant"}

  app.state.openai = DummyOpenAI()
  module = DiscordChatModule(app)

  async def dummy_summarize(guild_id, channel_id, hours, max_messages=5000):
    return {
      "messages_collected": 3,
      "token_count_estimate": 9,
      "raw_text_blob": "another",
      "cap_hit": False,
    }

  module.summarize_channel = dummy_summarize  # type: ignore

  res = asyncio.run(module.summarize_chat(10, 20, 6, user_id=7))
  assert res["summary_text"] == "fallback"
  assert res["model"] == "gpt-4o-mini"
  assert res["role"] == "assistant"
  assert app.state.openai.calls[-1]["persona"] == "summarize"
  assert app.state.openai.calls[-1]["system_prompt"] == ""
  assert app.state.openai.calls[-1]["max_tokens"] is None


def test_deliver_summary_enqueues_output():
  app = FastAPI()

  class DummyDiscord:
    def __init__(self):
      self.user_messages = []
      self.channel_messages = []

    async def on_ready(self):
      return None

    async def queue_user_message(self, user_id, message):
      self.user_messages.append((user_id, message))

    async def queue_channel_message(self, channel_id, message):
      self.channel_messages.append((channel_id, message))

  discord_bot = DummyDiscord()
  module = DiscordChatModule(app)
  module.discord = discord_bot

  res = asyncio.run(
    module.deliver_summary(
      guild_id=1,
      channel_id=2,
      user_id=3,
      summary_text="hello world",
      ack_message="queued",
      success=True,
      reason="queued",
      messages_collected=5,
      token_count_estimate=10,
      cap_hit=False,
    )
  )

  assert discord_bot.user_messages == [(3, "hello world")]
  assert discord_bot.channel_messages == [(2, "queued")]
  assert res["success"] is True
  assert res["queue_id"]


def test_get_persona_returns_details():
  app = FastAPI()
  openai = PersonaOpenAIStub()
  app.state.openai = openai
  module = DiscordChatModule(app)
  module.mark_ready()

  res = asyncio.run(module.get_persona("helper", guild_id=1, channel_id=2, user_id=3))
  assert res["success"] is True
  assert res["persona_details"]["name"] == "Helper"
  assert res["model"] == "gpt-4o-mini"
  assert res["max_tokens"] == 128
  assert openai.persona_requests == ["helper"]


def test_get_conversation_history_returns_history():
  app = FastAPI()
  openai = PersonaOpenAIStub()
  app.state.openai = openai
  module = DiscordChatModule(app)
  module.mark_ready()

  res = asyncio.run(module.get_conversation_history("helper", limit=10))
  assert res["success"] is True
  assert res["conversation_history"] == openai.history_entries
  assert res["personas_recid"] == 7
  assert openai.history_calls == [
    {"personas_recid": 7, "lookback_days": 30, "limit": 10}
  ]


def test_get_channel_history_formats_messages():
  app = FastAPI()
  module = DiscordChatModule(app)
  module.mark_ready()

  async def dummy_history(guild_id, channel_id, hours, max_messages=5000):
    msg = SimpleNamespace(
      content="Hello",
      author=SimpleNamespace(display_name="Alice"),
      created_at="now",
    )
    return {"messages": [msg], "cap_hit": False}

  module.fetch_channel_history_backwards = dummy_history  # type: ignore

  res = asyncio.run(module.get_channel_history(1, 2))
  assert res["success"] is True
  assert res["channel_history"] == [
    {"author": "Alice", "content": "Hello", "created_at": "now"}
  ]


def test_insert_conversation_input_logs_message():
  app = FastAPI()
  openai = PersonaOpenAIStub()
  app.state.openai = openai
  module = DiscordChatModule(app)
  module.mark_ready()

  res = asyncio.run(
    module.insert_conversation_input(
      "helper",
      "Tell me something",
      persona_details=openai.persona_details,
      guild_id=1,
      channel_id=2,
      user_id=3,
    )
  )
  assert res["success"] is True
  assert res["conversation_reference"] == 4242
  assert openai.log_calls == [
    {
      "personas_recid": 7,
      "models_recid": 11,
      "guild_id": 1,
      "channel_id": 2,
      "user_id": 3,
      "input_data": "Tell me something",
      "tokens": None,
    }
  ]


def test_generate_persona_response_updates_conversation():
  app = FastAPI()
  openai = PersonaOpenAIStub()
  app.state.openai = openai
  module = DiscordChatModule(app)
  module.mark_ready()

  res = asyncio.run(
    module.generate_persona_response(
      "helper",
      "What is up?",
      persona_details=openai.persona_details,
      conversation_history=openai.history_entries,
      channel_history=[{"author": "Bob", "content": "Hello"}],
      conversation_reference=999,
      guild_id=5,
      channel_id=6,
      user_id=7,
    )
  )
  assert res["success"] is True
  assert res["response"]["text"] == "Final reply"
  assert openai.generate_calls
  assert openai.finalize_calls == [
    {"recid": 999, "output_data": "Final reply", "tokens": 33}
  ]


def test_deliver_persona_response_enqueues_output():
  app = FastAPI()
  module = DiscordChatModule(app)
  module.mark_ready()

  class DummyDiscord:
    def __init__(self):
      self.channel_messages = []

    async def on_ready(self):
      return None

    async def queue_channel_message(self, channel_id, message):
      self.channel_messages.append((channel_id, message))

  discord_bot = DummyDiscord()
  module.discord = discord_bot

  res = asyncio.run(
    module.deliver_persona_response(
      persona="helper",
      response={"text": "queued"},
      conversation_reference=123,
      channel_id=44,
      user_id=55,
    )
  )
  assert res["success"] is True
  assert res["reason"] == "persona_response_queued"
  assert res["ack_message"] == "Persona response queued for <@55>."
  assert discord_bot.channel_messages == [(44, "queued")]
