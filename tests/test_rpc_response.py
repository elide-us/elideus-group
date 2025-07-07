from importlib import reload
from fastapi import FastAPI
from fastapi.testclient import TestClient
from server import rpc_router, lifespan

def create_app():
  from main import app
  return app


def test_rpc_environment_flow(monkeypatch):
  monkeypatch.setenv("VERSION", "9.9.9")
  monkeypatch.setenv("HOSTNAME", "unit-host")
  monkeypatch.setenv("REPO", "https://repo")
  monkeypatch.setenv("DISCORD_SECRET", "token")
  reload(lifespan)

  app = FastAPI(lifespan=lifespan.lifespan)
  app.include_router(rpc_router.router, prefix="/rpc")

  with TestClient(app) as client:
    req = { "op": "urn:admin:vars:get_version:1" }
    res = client.post("/rpc", json=req)
    assert res.status_code == 200
    assert res.json()["payload"]["version"] == "9.9.9"

    req["op"] = "urn:admin:vars:get_hostname:1"
    res = client.post("/rpc", json=req)
    assert res.status_code == 200
    assert res.json()["payload"]["hostname"] == "unit-host"

    req["op"] = "urn:admin:vars:get_repo:1"
    res = client.post("/rpc", json=req)
    assert res.status_code == 200
    assert res.json()["payload"]["repo"] == "https://repo"

    import rpc.admin.vars.services as services

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
