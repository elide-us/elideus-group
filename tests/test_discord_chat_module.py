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


def test_summarize_chat(monkeypatch):
  app = FastAPI()
  app.state.discord_bot = SimpleNamespace(on_ready=lambda: None)

  class DummyOpenAI:
    def __init__(self):
      self.client = object()
      self.prompts = []

    async def on_ready(self):
      pass

    async def get_persona_definition(self, name: str):
      assert name == "summarize"
      return {"name": "summarize", "prompt": "sum role", "tokens": 32, "model": "gpt"}

    async def submit_chat_prompt(self, **kwargs):
      self.prompts.append(kwargs.get("system_prompt"))
      assert kwargs.get("user_id") == 4
      assert kwargs.get("persona_name") == "summarize"
      return {"content": "sum", "model": "gpt", "role": "assistant"}

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
  assert app.state.openai.prompts[-1] == "sum role"


