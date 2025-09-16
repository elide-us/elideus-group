import asyncio

import pytest
from fastapi import FastAPI

from server.modules.personas_module import PersonasModule
from server.modules.providers import DBResult


class DummyDB:
  def __init__(self, row):
    self.row = row
    self.calls = []

  async def run(self, op, args):
    assert op == "db:assistant:personas:get_by_name:1"
    self.calls.append(args)
    return DBResult(rows=[self.row] if self.row else [], rowcount=1 if self.row else 0)


class DummyOpenAI:
  def __init__(self):
    self.client = object()
    self.calls = []

  async def on_ready(self):
    pass

  async def fetch_chat(self, schemas, role, prompt, tokens, **kwargs):
    self.calls.append({
      "persona": kwargs.get("persona"),
      "prompt": prompt,
      "role": role,
      "tokens": tokens,
      "input_log": kwargs.get("input_log"),
    })
    return {"content": "Response", "model": "gpt", "role": "assistant"}


def test_persona_response_calls_openai():
  app = FastAPI()
  module = PersonasModule(app)
  module.db = DummyDB({
    "element_prompt": "be stark",
    "element_tokens": 42,
    "element_model": "gpt",
  })
  module.openai = DummyOpenAI()

  res = asyncio.run(module.persona_response("stark", "Tell me", guild_id=1, channel_id=2, user_id=3))
  assert res == {
    "persona": "stark",
    "response_text": "Response",
    "model": "gpt",
    "role": "assistant",
  }
  assert module.openai.calls == [{
    "persona": "stark",
    "prompt": "Tell me",
    "role": "be stark",
    "tokens": 42,
    "input_log": "Tell me",
  }]
  assert module.db.calls == [{"name": "stark"}]


def test_persona_response_missing_persona():
  app = FastAPI()
  module = PersonasModule(app)
  module.db = DummyDB(None)
  module.openai = DummyOpenAI()

  with pytest.raises(ValueError):
    asyncio.run(module.persona_response("unknown", "Hello"))
  assert module.db.calls == [{"name": "unknown"}]


def test_persona_response_stub_without_openai():
  app = FastAPI()
  module = PersonasModule(app)
  module.db = DummyDB({
    "element_prompt": "be stark",
    "element_tokens": 42,
    "element_model": "gpt",
  })
  module.openai = None

  res = asyncio.run(module.persona_response("stark", "Hi"))
  assert res == {
    "persona": "stark",
    "response_text": "[[STUB: persona response here]]",
    "model": "gpt",
    "role": "be stark",
  }
