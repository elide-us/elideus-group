import asyncio
import pytest
from fastapi import FastAPI, Request

from server.modules.env_module import EnvironmentModule
from rpc.handler import handle_rpc_request
from rpc.models import RPCRequest


@pytest.fixture(autouse=True)
def set_env(monkeypatch):
  monkeypatch.setenv("HOSTNAME", "unit-host")


@pytest.fixture
def app():
  app = FastAPI()
  env_module = EnvironmentModule(app)
  app.state.env = env_module
  return app


def test_hostname_discord_view(app):
  request = Request({"type": "http", "app": app})
  urn = "urn:admin:vars:get_hostname:1:view:discord:1"
  rpc_request = RPCRequest(op=urn)
  resp = asyncio.run(handle_rpc_request(rpc_request, request))
  assert resp.op == urn
  assert resp.payload.content == "Hostname: unit-host"
