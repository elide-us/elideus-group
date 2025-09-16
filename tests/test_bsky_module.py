import asyncio
from types import SimpleNamespace

import pytest
from fastapi import FastAPI

from server.modules import BaseModule
from server.modules.bsky_module import BskyModule


class DummyDb(BaseModule):
  def __init__(self, app: FastAPI, values: dict[str, str]):
    super().__init__(app)
    self.values = values

  async def startup(self):
    self.mark_ready()

  async def shutdown(self):
    pass

  async def run(self, op: str, args: dict):
    class Res:
      def __init__(self, rows):
        self.rows = rows
        self.rowcount = len(rows)
    if op == "db:system:config:get_config:1":
      key = args.get("key")
      if key in self.values:
        return Res([{ "value": self.values[key] }])
    return Res([])


def test_post_message():
  app = FastAPI()
  db = DummyDb(app, {"BskyPassword": "secret", "BskyHandle": "custom.handle"})
  asyncio.run(db.startup())
  app.state.db = db

  module = BskyModule(app)

  created_clients: list[SimpleNamespace] = []

  class StubRequest:
    def __init__(self):
      self.closed = False

    async def close(self):
      self.closed = True

  class StubClient:
    def __init__(self):
      self.request = StubRequest()
      self.login_calls: list[tuple[str, str]] = []
      self.send_post_calls: list = []

    async def login(self, handle: str, password: str):
      self.login_calls.append((handle, password))
      return SimpleNamespace(handle=handle, display_name="Custom")

    async def send_post(self, text):
      self.send_post_calls.append(text)
      return SimpleNamespace(uri="at://custom/1", cid="cid123")

  def factory():
    client = StubClient()
    created_clients.append(client)
    return client

  module._client_factory = factory

  asyncio.run(module.startup())

  result = asyncio.run(module.post_message("Hello Bluesky"))

  assert isinstance(result.uri, str)
  assert result.uri == "at://custom/1"
  assert result.cid == "cid123"
  assert result.handle == "custom.handle"
  assert result.display_name == "Custom"

  assert created_clients
  client = created_clients[0]
  assert client.login_calls == [("custom.handle", "secret")]
  assert len(client.send_post_calls) == 1
  assert client.request.closed is True

  asyncio.run(module.shutdown())
  asyncio.run(db.shutdown())


def test_post_message_requires_password():
  app = FastAPI()
  db = DummyDb(app, {})
  asyncio.run(db.startup())
  app.state.db = db

  module = BskyModule(app)
  asyncio.run(module.startup())

  with pytest.raises(ValueError) as exc:
    asyncio.run(module.post_message("Hello"))
  assert "BskyPassword" in str(exc.value)

  asyncio.run(module.shutdown())
  asyncio.run(db.shutdown())


def test_post_message_rejects_blank():
  app = FastAPI()
  db = DummyDb(app, {"BskyPassword": "secret"})
  asyncio.run(db.startup())
  app.state.db = db

  module = BskyModule(app)
  asyncio.run(module.startup())

  with pytest.raises(ValueError):
    asyncio.run(module.post_message("   "))

  asyncio.run(module.shutdown())
  asyncio.run(db.shutdown())
