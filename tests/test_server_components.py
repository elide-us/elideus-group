import asyncio, pytest
from importlib import reload
from fastapi import FastAPI, HTTPException, Request
from fastapi.testclient import TestClient
from server import lifespan, config
from rpc.handler import handle_rpc_request
from rpc.admin.vars.handler import handle_vars_request
from rpc.admin.vars.services import get_version_v1, get_hostname_v1, get_repo_v1, get_ffmpeg_version_v1
from rpc.models import RPCRequest

def test_get_missing_environment_variable(monkeypatch):
  monkeypatch.delenv("MISSING_VAR", raising=False)
  with pytest.raises(RuntimeError):
    config.get_environment_variable("MISSING_VAR")

def test_lifespan_sets_state(monkeypatch):
  monkeypatch.setenv("VERSION", "9.9.9")
  monkeypatch.setenv("HOSTNAME", "unit-host")
  monkeypatch.setenv("REPO", "https://repo")
  reload(config)
  reload(lifespan)
  app = FastAPI(lifespan=lifespan.lifespan)
  with TestClient(app) as client:
    assert client.app.state.version == "9.9.9"
    assert client.app.state.hostname == "unit-host"
    assert client.app.state.repo == "https://repo"

def test_services_read_from_state(monkeypatch):
  app = FastAPI()
  app.state.version = "9.9.9"
  app.state.hostname = "unit-host"
  app.state.repo = "https://repo"
  request = Request({'type': 'http', 'app': app})
  version_res = asyncio.run(get_version_v1(request))
  assert version_res.payload.version == "9.9.9"
  host_res = asyncio.run(get_hostname_v1(request))
  assert host_res.payload.hostname == "unit-host"
  repo_res = asyncio.run(get_repo_v1(request))
  assert repo_res.payload.repo == "https://repo"
  assert repo_res.payload.build == "https://repo/actions"
  async def fake_exec(*args, **kwargs):
    class Proc:
      async def communicate(self):
        return (b"ffmpeg version 6.0", b"")
    return Proc()
  monkeypatch.setattr('rpc.admin.vars.services.asyncio.create_subprocess_exec', fake_exec)
  ffmpeg_res = asyncio.run(get_ffmpeg_version_v1(request))
  assert ffmpeg_res.payload.ffmpeg_version == "ffmpeg version 6.0"

def test_handle_rpc_request_invalid_prefix():
  app = FastAPI()
  request = Request({'type': 'http', 'app': app})
  rpc_request = RPCRequest(op="invalid")
  with pytest.raises(HTTPException) as exc:
    asyncio.run(handle_rpc_request(rpc_request, request))
  assert exc.value.status_code == 400

def test_handle_rpc_request_unknown_domain():
  app = FastAPI()
  request = Request({'type': 'http', 'app': app})
  rpc_request = RPCRequest(op="urn:unknown:op:1")
  with pytest.raises(HTTPException) as exc:
    asyncio.run(handle_rpc_request(rpc_request, request))
  assert exc.value.status_code == 404

def test_handle_vars_request_unknown_operation():
  app = FastAPI()
  request = Request({'type': 'http', 'app': app})
  with pytest.raises(HTTPException) as exc:
    asyncio.run(handle_vars_request(["unknown", "1"], request))
  assert exc.value.status_code == 404
