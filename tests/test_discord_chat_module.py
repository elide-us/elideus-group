import asyncio
import pytest
from fastapi import FastAPI
from types import SimpleNamespace

from server.modules.discord_chat_module import DiscordChatModule


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

    async def on_ready(self):
      pass

    async def fetch_chat(self, schemas, role, prompt, tokens, prompt_context=""):
      if role == "Summarize the following conversation into bullet points.":
        return SimpleNamespace(content="hi\nbye")
      return SimpleNamespace(content="uwu hi")

  app.state.openai = DummyOpenAI()
  module = DiscordChatModule(app)

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
