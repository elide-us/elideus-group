import asyncio
from fastapi import FastAPI
from types import SimpleNamespace

from server.modules.openai_module import OpenaiModule, SummaryQueue


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
