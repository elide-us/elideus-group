import asyncio
from fastapi import FastAPI, Request
from server.providers.env_provider import EnvironmentProvider

from rpc.handler import handle_rpc_request
from rpc.models import RPCRequest

def test_get_version(monkeypatch):
  monkeypatch.setenv("VERSION", "9.9.9")
  monkeypatch.setenv("HOSTNAME", "unit-host")
  monkeypatch.setenv("REPO", "https://repo")
  monkeypatch.setenv("DISCORD_SECRET", "token")
  env = EnvironmentProvider(app := FastAPI())
  app.state.env_provider = env
  asyncio.run(env.startup())
  request = Request({"type": "http", "app": app})

  rpc_request = RPCRequest(op="urn:admin:vars:get_version:1")
  response = asyncio.run(handle_rpc_request(rpc_request, request))

  assert response.op == "urn:admin:vars:version:1"
  assert response.payload.version == "9.9.9"

def test_get_hostname(monkeypatch):
  monkeypatch.setenv("VERSION", "9.9.9")
  monkeypatch.setenv("HOSTNAME", "unit-host")
  monkeypatch.setenv("REPO", "https://repo")
  monkeypatch.setenv("DISCORD_SECRET", "token")
  env = EnvironmentProvider(app := FastAPI())
  app.state.env_provider = env
  asyncio.run(env.startup())
  request = Request({"type": "http", "app": app})

  rpc_request = RPCRequest(op="urn:admin:vars:get_hostname:1")
  response = asyncio.run(handle_rpc_request(rpc_request, request))

  assert response.op == "urn:admin:vars:hostname:1"
  assert response.payload.hostname == "unit-host"

def test_get_repo(monkeypatch):
  monkeypatch.setenv("VERSION", "9.9.9")
  monkeypatch.setenv("HOSTNAME", "unit-host")
  monkeypatch.setenv("REPO", "https://repo")
  monkeypatch.setenv("DISCORD_SECRET", "token")
  env = EnvironmentProvider(app := FastAPI())
  app.state.env_provider = env
  asyncio.run(env.startup())
  request = Request({"type": "http", "app": app})

  rpc_request = RPCRequest(op="urn:admin:vars:get_repo:1")
  response = asyncio.run(handle_rpc_request(rpc_request, request))

  assert response.op == "urn:admin:vars:repo:1"
  assert response.payload.repo == "https://repo"

def test_get_ffmpeg_version(monkeypatch):
  monkeypatch.setenv("VERSION", "9.9.9")
  monkeypatch.setenv("HOSTNAME", "unit-host")
  monkeypatch.setenv("REPO", "https://repo")
  monkeypatch.setenv("DISCORD_SECRET", "token")
  env = EnvironmentProvider(app := FastAPI())
  app.state.env_provider = env
  asyncio.run(env.startup())
  request = Request({"type": "http", "app": app})

  async def fake_exec(*args, **kwargs):
    class Proc:
      async def communicate(self):
        return (b"ffmpeg version 6.0", b"")
    return Proc()

  import rpc.admin.vars.services as services
  monkeypatch.setattr(services.asyncio, "create_subprocess_exec", fake_exec)

  rpc_request = RPCRequest(op="urn:admin:vars:get_ffmpeg_version:1")
  response = asyncio.run(handle_rpc_request(rpc_request, request))

  assert response.op == "urn:admin:vars:ffmpeg_version:1"
  assert response.payload.ffmpeg_version == "ffmpeg version 6.0"


def test_get_home_links():
  app = FastAPI()
  request = Request({"type": "http", "app": app})

  rpc_request = RPCRequest(op="urn:admin:links:get_home:1")
  response = asyncio.run(handle_rpc_request(rpc_request, request))

  assert response.op == "urn:admin:links:home:1"
  assert len(response.payload.links) == 6
  assert response.payload.links[0].title == "Discord"


def test_get_routes():
  app = FastAPI()
  request = Request({"type": "http", "app": app})

  rpc_request = RPCRequest(op="urn:admin:links:get_routes:1")
  response = asyncio.run(handle_rpc_request(rpc_request, request))

  assert response.op == "urn:admin:links:routes:1"
  assert len(response.payload.routes) == 7
  assert response.payload.routes[0].path == "/"
