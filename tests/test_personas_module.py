import asyncio

import pytest
from fastapi import FastAPI

from server.modules.personas_module import PersonasModule


class DummyOpenAI:
  def __init__(self, persona: dict | None):
    self.client = object()
    self.calls = []
    self.persona = persona
    self.definitions = []

  async def on_ready(self):
    pass

  async def get_persona_definition(self, name: str):
    self.definitions.append(name)
    if not self.persona:
      return None
    return self.persona

  async def submit_chat_prompt(self, **kwargs):
    self.calls.append(kwargs)
    return {"content": "Response", "model": "gpt", "role": "assistant"}


def test_persona_response_calls_openai():
  app = FastAPI()
  module = PersonasModule(app)
  module.openai = DummyOpenAI({
    "name": "stark",
    "prompt": "be stark",
    "tokens": 42,
    "model": "gpt",
    "recid": 1,
    "models_recid": 2,
  })

  res = asyncio.run(module.persona_response("stark", "Tell me", guild_id=1, channel_id=2, user_id=3))
  assert res == {
    "persona": "stark",
    "response_text": "Response",
    "model": "gpt",
    "role": "assistant",
  }
  assert module.openai.definitions == ["stark"]
  call = module.openai.calls[0]
  expected = {
    "system_prompt": "be stark",
    "model": "gpt",
    "max_tokens": 42,
    "user_prompt": "Tell me",
    "persona_name": "stark",
    "persona_recid": 1,
    "models_recid": 2,
    "guild_id": 1,
    "channel_id": 2,
    "user_id": 3,
    "input_log": "Tell me",
    "token_count": None,
  }
  for key, value in expected.items():
    assert call.get(key) == value


def test_persona_response_missing_persona():
  app = FastAPI()
  module = PersonasModule(app)
  module.openai = DummyOpenAI(None)

  with pytest.raises(ValueError):
    asyncio.run(module.persona_response("unknown", "Hello"))


def test_persona_response_stub_without_openai():
  app = FastAPI()
  module = PersonasModule(app)
  module.openai = None

  res = asyncio.run(module.persona_response("stark", "Hi"))
  assert res == {
    "persona": "stark",
    "response_text": "[[STUB: persona response here]]",
    "model": "",
    "role": "",
  }
