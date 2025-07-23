import asyncio
import pytest
from fastapi import FastAPI, Request

from server.modules.env_module import EnvironmentModule
from rpc.handler import handle_rpc_request
from rpc.models import RPCRequest


@pytest.fixture(autouse=True)
def set_env(monkeypatch):
  monkeypatch.setenv("HOSTNAME", "unit-host")
  monkeypatch.setenv("DISCORD_SECRET", "token")
  monkeypatch.setenv("JWT_SECRET", "jwt")
  monkeypatch.setenv("POSTGRES_CONNECTION_STRING", "postgres://user@host/db")
  monkeypatch.setenv("AZURE_BLOB_CONNECTION_STRING", "cs")


@pytest.fixture
def app():
  app = FastAPI()
  env_module = EnvironmentModule(app)
  app.state.env = env_module
  class DB:
    async def get_config_value(self, key):
      if key == "Hostname":
        return "unit-host"
  app.state.database = DB()
  return app


def test_hostname_discord_view(app):
  request = Request({"type": "http", "app": app, 'headers': []})
  urn = "urn:system:vars:get_hostname:1:view:discord:1"
  rpc_request = RPCRequest(op=urn)
  resp = asyncio.run(handle_rpc_request(rpc_request, request))
  assert resp.op == urn
  assert resp.payload.content == "Hostname: unit-host"
