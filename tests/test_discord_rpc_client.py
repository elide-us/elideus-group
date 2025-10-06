import asyncio
import json
from types import SimpleNamespace

from fastapi import FastAPI

from server.helpers.discord_signing import compute_signature
from server.modules.discord_bot_module import DiscordBotModule


def test_call_rpc_builds_headers(monkeypatch):
  app = FastAPI()
  module = DiscordBotModule(app)
  module.rpc_base_url = "https://example.test/api"
  module.rpc_token = "super-secret"
  module.rpc_signing_secret = "signing-secret"

  captured = {}

  class DummyResponse:
    status = 200

    async def __aenter__(self):
      return self

    async def __aexit__(self, exc_type, exc, tb):
      return False

    async def text(self):
      return json.dumps({"op": "urn:test:ops:trigger:1", "payload": {"ok": True}, "version": 1})

  class DummySession:
    def __init__(self, *args, **kwargs):
      captured["session_args"] = (args, kwargs)

    async def __aenter__(self):
      return self

    async def __aexit__(self, exc_type, exc, tb):
      return False

    def post(self, url, *, json=None, headers=None):
      captured["url"] = url
      captured["json"] = json
      captured["headers"] = headers
      return DummyResponse()

  import server.modules.discord_bot_module as discord_bot_module

  monkeypatch.setattr(discord_bot_module, "aiohttp", SimpleNamespace(ClientSession=DummySession))
  monkeypatch.setattr(discord_bot_module.time, "time", lambda: 1700000000)

  response = asyncio.run(
    module.call_rpc(
      "urn:test:ops:trigger:1",
      {"foo": "bar"},
      metadata={"user_id": 7, "guild_id": 9, "channel_id": 11},
    )
  )

  assert hasattr(response, "payload")
  assert response.payload["ok"] is True
  assert captured["url"] == "https://example.test/api/rpc"
  assert captured["json"] == {
    "op": "urn:test:ops:trigger:1",
    "payload": {"foo": "bar"},
    "version": 1,
  }
  headers = captured["headers"]
  assert headers["Authorization"] == "Bearer super-secret"
  assert headers["Content-Type"] == "application/json"
  assert headers["X-Discord-Id"] == "7"
  assert headers["X-Discord-Guild-Id"] == "9"
  assert headers["X-Discord-Channel-Id"] == "11"
  assert headers["X-Discord-Signature-Timestamp"] == str(1700000000)
  expected_signature = compute_signature(
    "signing-secret",
    body=captured["json"],
    timestamp=headers["X-Discord-Signature-Timestamp"],
    user_id="7",
    guild_id="9",
    channel_id="11",
  )
  assert headers["X-Discord-Signature"] == expected_signature
