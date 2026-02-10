from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
import pathlib, sys, types

# Stub rpc package to avoid side effects from rpc.__init__
pkg = types.ModuleType('rpc')
pkg.__path__ = [str(pathlib.Path(__file__).resolve().parent.parent / 'rpc')]
sys.modules.setdefault('rpc', pkg)

# Stub server package with minimal models
server_pkg = types.ModuleType('server')
models_pkg = types.ModuleType('server.models')
from pydantic import BaseModel

class RPCRequest(BaseModel):
  op: str
  payload: dict | None = None
  version: int = 1

class RPCResponse(BaseModel):
  op: str
  payload: dict
  version: int = 1

class AuthContext(BaseModel):
  role_mask: int = 0

models_pkg.RPCRequest = RPCRequest
models_pkg.RPCResponse = RPCResponse
models_pkg.AuthContext = AuthContext
server_pkg.models = models_pkg
sys.modules.setdefault('server', server_pkg)
sys.modules.setdefault('server.models', models_pkg)

from rpc.public.vars.services import public_vars_get_versions_v1

class DummyVarsVersionsModule:
  def __init__(self):
    self.masks: list[int] = []

  async def get_versions(self, role_mask):
    self.masks.append(role_mask)
    res = {"hostname": "example.com", "version": "1.2.3", "repo": "https://repo"}
    if role_mask:
      res["ffmpeg_version"] = "ffmpeg 1"
      res["odbc_version"] = "odbc 1"
    return res


app_versions = FastAPI()
app_versions.state.public_vars = DummyVarsVersionsModule()


@app_versions.post("/rpc")
async def rpc_endpoint_versions(request: Request):
  return await public_vars_get_versions_v1(request)


client_versions = TestClient(app_versions)


def test_get_versions_public():
  resp = client_versions.post("/rpc", json={"op": "urn:public:vars:get_versions:1"})
  assert resp.status_code == 200
  data = resp.json()
  assert data["op"] == "urn:public:vars:get_versions:1"
  assert data["payload"] == {"hostname": "example.com", "version": "1.2.3", "repo": "https://repo"}
  assert app_versions.state.public_vars.masks == [0]


app_versions_admin = FastAPI()
app_versions_admin.state.public_vars = DummyVarsVersionsModule()


@app_versions_admin.post("/rpc")
async def rpc_endpoint_versions_admin(request: Request):
  request.state.rpc_request = RPCRequest(op="urn:public:vars:get_versions:1")
  request.state.auth_ctx = AuthContext(role_mask=1)
  return await public_vars_get_versions_v1(request)


client_versions_admin = TestClient(app_versions_admin)


def test_get_versions_admin():
  resp = client_versions_admin.post("/rpc", json={})
  assert resp.status_code == 200
  data = resp.json()
  assert data["op"] == "urn:public:vars:get_versions:1"
  assert data["payload"] == {
    "hostname": "example.com",
    "version": "1.2.3",
    "repo": "https://repo",
    "ffmpeg_version": "ffmpeg 1",
    "odbc_version": "odbc 1",
  }
  assert app_versions_admin.state.public_vars.masks == [1]

