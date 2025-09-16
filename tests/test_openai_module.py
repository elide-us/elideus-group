import asyncio
import logging
from fastapi import FastAPI
from types import SimpleNamespace

from server.modules.openai_module import OpenaiModule, SummaryQueue
from server.modules.providers import DBResult


def test_fetch_chat_message_order_and_return():
  app = FastAPI()
  module = OpenaiModule(app)

  class DummyCreate:
    async def create(self, **kwargs):
      self.kwargs = kwargs
      return SimpleNamespace(
        model=kwargs.get("model"),
        choices=[SimpleNamespace(message=SimpleNamespace(content="reply", role="assistant"))],
        usage=SimpleNamespace(total_tokens=11),
      )

  dummy_create = DummyCreate()
  module.client = SimpleNamespace(chat=SimpleNamespace(completions=dummy_create))

  res = asyncio.run(module.fetch_chat([], "sys", "user", 5, "ctx"))

  assert dummy_create.kwargs["messages"] == [
    {"role": "system", "content": "sys"},
    {"role": "user", "content": "ctx"},
    {"role": "user", "content": "user"},
  ]
  assert "tools" not in dummy_create.kwargs
  assert res == {"content": "reply", "model": "gpt-4o-mini", "role": "assistant"}


def test_fetch_chat_includes_tools_when_present():
  app = FastAPI()
  module = OpenaiModule(app)

  class DummyCreate:
    async def create(self, **kwargs):
      self.kwargs = kwargs
      return SimpleNamespace(
        model=kwargs.get("model"),
        choices=[SimpleNamespace(message=SimpleNamespace(content="reply", role="assistant"))],
        usage=SimpleNamespace(total_tokens=13),
      )

  dummy_create = DummyCreate()
  module.client = SimpleNamespace(chat=SimpleNamespace(completions=dummy_create))

  schemas = [
    {
      "type": "function",
      "function": {"name": "do_thing", "parameters": {"type": "object", "properties": {}}},
    }
  ]

  res = asyncio.run(module.fetch_chat(schemas, "sys", "user", 5))

  assert res == {"content": "reply", "model": "gpt-4o-mini", "role": "assistant"}
  assert dummy_create.kwargs["tools"] == schemas


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
    async def create(self, **kwargs):
      self.kwargs = kwargs
      return SimpleNamespace(
        model=kwargs.get("model"),
        choices=[SimpleNamespace(message=SimpleNamespace(content="hi", role="assistant"))],
        usage=SimpleNamespace(total_tokens=42),
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
        assert args == {"recid": 99, "output_data": "hi", "tokens": 42}
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
  assert dummy_create.kwargs["max_tokens"] == 5
  assert "tools" not in dummy_create.kwargs
  calls = [c[0] for c in module.db.calls]
  assert calls == [
    "db:assistant:personas:get_by_name:1",
    "db:assistant:conversations:insert:1",
    "db:assistant:conversations:update_output:1",
  ]


def test_log_conversation_end_warns_when_no_rows_updated(caplog):
  app = FastAPI()
  module = OpenaiModule(app)

  class DummyDB:
    async def run(self, op, args):
      assert op == "db:assistant:conversations:update_output:1"
      assert args == {"recid": 99, "output_data": "done", "tokens": 3}
      return DBResult(rowcount=0)

  module.db = DummyDB()

  with caplog.at_level(logging.WARNING):
    asyncio.run(module._log_conversation_end(99, "done", 3))

  assert "conversation update affected 0 rows (recid=99)" in caplog.text
