import asyncio
import pytest
from fastapi import FastAPI
from types import SimpleNamespace

from server.modules.discord_chat_module import DiscordChatModule
from server.modules.providers import DBResult


def test_summarize_channel(monkeypatch):
  app = FastAPI()
  app.state.discord = SimpleNamespace(on_ready=lambda: None)
  module = DiscordChatModule(app)

  async def dummy_fetch(guild_id, channel_id, hours, max_messages=5000):
    msg = SimpleNamespace(content="hello", author=SimpleNamespace(name="Alice"))
    return {"messages": [msg], "cap_hit": False}

  module.fetch_channel_history_backwards = dummy_fetch  # type: ignore

  res = asyncio.run(module.summarize_channel(1, 2, 1))
  assert res["messages_collected"] == 1
  assert "Alice: hello" in res["raw_text_blob"]


def test_uwu_chat(monkeypatch):
  app = FastAPI()
  app.state.discord = SimpleNamespace(on_ready=lambda: None)

  class DummyOpenAI:
    def __init__(self):
      self.client = object()
      self.roles = []

    async def on_ready(self):
      pass

    async def fetch_chat(self, schemas, role, prompt, tokens, prompt_context="", **kwargs):
      self.roles.append(role)
      if role == "Summarize the following conversation into bullet points.":
        return {"content": "hi\nbye"}
      return {"content": "uwu hi"}

  app.state.openai = DummyOpenAI()
  module = DiscordChatModule(app)

  class DummyDB:
    async def run(self, op, args):
      assert op == "db:assistant:personas:get_by_name:1"
      assert args == {"name": "uwu"}
      return DBResult(rows=[{"instructions": "be fluffy"}], rowcount=1)

  module.db = DummyDB()

  async def dummy_summarize(guild_id, channel_id, hours, max_messages=5000):
    return {
      "messages_collected": 12,
      "token_count_estimate": 5,
      "raw_text_blob": "text",
      "cap_hit": False,
    }

  module.summarize_channel = dummy_summarize  # type: ignore

  res = asyncio.run(module.uwu_chat(1, 2, 3, "hey"))
  assert res["token_count_estimate"] == 5
  assert res["summary_lines"] == ["hi", "bye"]
  assert res["uwu_response_text"] == "uwu hi"
  assert app.state.openai.roles[-1] == "be fluffy"


def test_summarize_chat(monkeypatch):
  app = FastAPI()
  app.state.discord = SimpleNamespace(on_ready=lambda: None)

  class DummyOpenAI:
    def __init__(self):
      self.client = object()
      self.roles = []

    async def on_ready(self):
      pass

    async def fetch_chat(self, schemas, role, prompt, tokens, prompt_context="", **kwargs):
      self.roles.append(role)
      assert kwargs.get("user_id") == 4
      return {"content": "sum", "model": "gpt", "role": "assistant"}

  app.state.openai = DummyOpenAI()
  module = DiscordChatModule(app)

  class DummyDB:
    async def run(self, op, args):
      assert op == "db:assistant:personas:get_by_name:1"
      assert args == {"name": "summarize"}
      return DBResult(rows=[{"instructions": "sum role"}], rowcount=1)

  module.db = DummyDB()

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
  assert app.state.openai.roles[-1] == "sum role"


