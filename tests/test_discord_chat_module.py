import asyncio
from fastapi import FastAPI
from types import SimpleNamespace

from server.modules.discord_chat_module import DiscordChatModule


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
