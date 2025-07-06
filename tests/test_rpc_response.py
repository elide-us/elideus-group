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

  # reload config after setting env vars
  import server.config as config
  reload(config)
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
    assert res.json()["payload"]["build"] == "https://repo/actions"
