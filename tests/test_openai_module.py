import asyncio
from fastapi import FastAPI
from types import SimpleNamespace

from server.modules.openai_module import OpenaiModule, SummaryQueue
from server.modules.providers import DBResult


def test_fetch_chat_message_order_and_return():
  app = FastAPI()
  module = OpenaiModule(app)

  class DummyCreate:
    async def create(self, model, max_tokens, tools, messages):
      self.args = {
        "model": model,
        "max_tokens": max_tokens,
        "tools": tools,
        "messages": messages,
      }
      return SimpleNamespace(
        model=model,
        choices=[SimpleNamespace(message=SimpleNamespace(content="reply", role="assistant"))],
      )

  dummy_create = DummyCreate()
  module.client = SimpleNamespace(chat=SimpleNamespace(completions=dummy_create))

  res = asyncio.run(module.fetch_chat([], "sys", "user", 5, "ctx"))

  assert dummy_create.args["messages"] == [
    {"role": "system", "content": "sys"},
    {"role": "user", "content": "ctx"},
    {"role": "user", "content": "user"},
  ]
  assert res == {"content": "reply", "model": "gpt-4o-mini", "role": "assistant"}


def test_summary_queue_executes_in_order():
  q = SummaryQueue(delay=0)
  called: list[int] = []

  async def func(x):
    called.append(x)

  async def run():
    await asyncio.gather(q.add(func, 1), q.add(func, 2))

  asyncio.run(run())
  assert called == [1, 2]


def test_fetch_chat_logs_conversation():
  app = FastAPI()
  module = OpenaiModule(app)

  class DummyCreate:
    async def create(self, model, max_tokens, tools, messages):
      self.args = {
        "model": model,
        "max_tokens": max_tokens,
        "tools": tools,
        "messages": messages,
      }
      return SimpleNamespace(
        model=model,
        choices=[SimpleNamespace(message=SimpleNamespace(content="hi", role="assistant"))],
      )
  dummy_create = DummyCreate()
  module.client = SimpleNamespace(chat=SimpleNamespace(completions=dummy_create))

  class DummyDB:
    def __init__(self):
      self.calls = []

    async def run(self, op, args):
      self.calls.append((op, args))
      if op == "db:assistant:personas:get_by_name:1":
        return DBResult(
          rows=[
            {
              "recid": 1,
              "models_recid": 2,
              "element_model": "gpt",
              "element_tokens": 5,
            }
          ],
          rowcount=1,
        )
      if op == "db:assistant:conversations:insert:1":
        assert args["personas_recid"] == 1
        assert args["models_recid"] == 2
        assert args["guild_id"] == "1"
        assert args["channel_id"] == "2"
        assert args["user_id"] == "3"
        assert args["input_data"] == "hello"
        assert args["tokens"] == 7
        return DBResult(rows=[{"recid": 99}], rowcount=1)
      if op == "db:assistant:conversations:update_output:1":
        assert args == {"recid": 99, "output_data": "hi"}
        return DBResult(rowcount=1)
      return DBResult()

  module.db = DummyDB()

  res = asyncio.run(
    module.fetch_chat(
      [],
      "role",
      "hello",
      None,
      persona="uwu",
      guild_id=1,
      channel_id=2,
      user_id=3,
      input_log="hello",
      token_count=7,
    )
  )
  assert res["content"] == "hi"
  assert dummy_create.args["max_tokens"] == 5
  calls = [c[0] for c in module.db.calls]
  assert calls == [
    "db:assistant:personas:get_by_name:1",
    "db:assistant:conversations:insert:1",
    "db:assistant:conversations:update_output:1",
  ]
