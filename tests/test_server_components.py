import asyncio, pytest
from importlib import reload
from fastapi import FastAPI, HTTPException, Request
from fastapi.testclient import TestClient
from server import lifespan
from server.modules import ModuleRegistry, BaseModule
from server.modules.env_module import EnvironmentModule
from rpc.handler import handle_rpc_request
from rpc.admin.vars.handler import handle_vars_request
from rpc.admin.vars.services import get_version_v1, get_hostname_v1, get_repo_v1, get_ffmpeg_version_v1


class DummyModule(BaseModule):
  async def startup(self):
    pass

  async def shutdown(self):
    pass


def setup_modules(app: FastAPI) -> ModuleRegistry:
  app.state.env = EnvironmentModule(app)
  app.state.discord = DummyModule(app)
  app.state.database = DummyModule(app)
  app.state.auth = DummyModule(app)
  modules = ModuleRegistry(app)
  app.state.modules = modules
  return modules
from rpc.models import RPCRequest

def test_get_missing_environment_variable(monkeypatch):
  monkeypatch.delenv("MISSING_VAR", raising=False)
  env = EnvironmentModule(app := FastAPI())
  with pytest.raises(RuntimeError):
    env._load_required("MISSING_VAR")

def test_lifespan_sets_state(monkeypatch):
  monkeypatch.setenv("VERSION", "v9.9.9")
  monkeypatch.setenv("HOSTNAME", "unit-host")
  monkeypatch.setenv("REPO", "https://repo")
  reload(lifespan)

  def sync_env_startup(self):
    self._load_required("VERSION", "MISSING_ENV_VERSION")
    self._load_required("HOSTNAME", "MISSING_ENV_HOSTNAME")
    self._load_required("REPO", "MISSING_ENV_REPO")
    self._load_required("DISCORD_SECRET", "MISSING_ENV_DISCORD_SECRET")
    self._load_required("DISCORD_SYSCHAN", 0)
    self._load_optional("JWT_SECRET")
    self._load_optional("MS_API_ID")
    self._load_optional("POSTGRES_CONNECTION_STRING")

  monkeypatch.setattr(lifespan.EnvironmentModule, "startup", sync_env_startup)
  monkeypatch.setattr(lifespan, "DiscordModule", DummyModule)
  monkeypatch.setattr(lifespan, "DatabaseModule", DummyModule)
  monkeypatch.setattr(lifespan, "AuthModule", DummyModule)
  app = FastAPI(lifespan=lifespan.lifespan)
  with TestClient(app) as client:
    env = client.app.state.modules.get_module("env")
    assert env.get("VERSION") == "v9.9.9"
    assert env.get("HOSTNAME") == "unit-host"
    assert env.get("REPO") == "https://repo"

def test_services_read_from_state(monkeypatch):
  monkeypatch.setenv("VERSION", "v9.9.9")
  monkeypatch.setenv("HOSTNAME", "unit-host")
  monkeypatch.setenv("REPO", "https://repo")
  app = FastAPI()
  modules = setup_modules(app)
  asyncio.run(modules.startup())
  request = Request({'type': 'http', 'app': app})
  version_res = asyncio.run(get_version_v1(request))
  assert version_res.payload.version == "v9.9.9"
  host_res = asyncio.run(get_hostname_v1(request))
  assert host_res.payload.hostname == "unit-host"
  repo_res = asyncio.run(get_repo_v1(request))
  assert repo_res.payload.repo == "https://repo"
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
