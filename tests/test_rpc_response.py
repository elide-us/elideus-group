from importlib import reload
from fastapi import FastAPI
from fastapi.testclient import TestClient
from server import rpc_router, lifespan
from server.modules import BaseModule


class DummyModule(BaseModule):
  async def startup(self):
    pass

  async def shutdown(self):
    pass

def create_app():
  from main import app
  return app


def test_rpc_environment_flow(monkeypatch):
  monkeypatch.setenv("VERSION", "v0.0.0")
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
  app.include_router(rpc_router.router, prefix="/rpc")

  with TestClient(app) as client:
    req = { "op": "urn:admin:vars:get_version:1" }
    res = client.post("/rpc", json=req)
    assert res.status_code == 200
    assert res.json()["payload"]["version"] == "v0.0.0"

    req["op"] = "urn:admin:vars:get_hostname:1"
    res = client.post("/rpc", json=req)
    assert res.status_code == 200
    assert res.json()["payload"]["hostname"] == "unit-host"

    req["op"] = "urn:admin:vars:get_repo:1"
    res = client.post("/rpc", json=req)
    assert res.status_code == 200
    assert res.json()["payload"]["repo"] == "https://repo"

    from rpc.admin.vars import services

    async def fake_exec(*args, **kwargs):
      class Proc:
        async def communicate(self):
          return (b"ffmpeg version 6.0", b"")
      return Proc()

    monkeypatch.setattr(services.asyncio, "create_subprocess_exec", fake_exec)
    req["op"] = "urn:admin:vars:get_ffmpeg_version:1"
    res = client.post("/rpc", json=req)
    assert res.status_code == 200
    assert res.json()["payload"]["ffmpeg_version"] == "ffmpeg version 6.0"

    req["op"] = "urn:admin:links:get_home:1"
    res = client.post("/rpc", json=req)
    assert res.status_code == 200
    assert isinstance(res.json()["payload"], dict)
    assert len(res.json()["payload"]["links"]) == 6
    
    req["op"] = "urn:admin:links:get_routes:1"
    res = client.post("/rpc", json=req)
    assert res.status_code == 200
    assert isinstance(res.json()["payload"], dict)
    assert len(res.json()["payload"]["routes"]) == 1
