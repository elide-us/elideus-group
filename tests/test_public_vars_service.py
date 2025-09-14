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

from rpc.public.vars.services import (
  public_vars_get_hostname_v1,
  public_vars_get_version_v1,
  public_vars_get_versions_v1,
)


class DummyVarsHostnameModule:
  async def get_hostname(self):
    return "example.com"


class DummyVarsVersionModule:
  async def get_version(self):
    return "1.2.3"


class DummyVarsVersionsModule:
  async def get_versions(self, role_mask):
    res = {"hostname": "example.com", "version": "1.2.3", "repo": "https://repo"}
    if role_mask:
      res["ffmpeg_version"] = "ffmpeg 1"
      res["odbc_version"] = "odbc 1"
    return res


app = FastAPI()
app.state.public_vars = DummyVarsHostnameModule()


@app.post("/rpc")
async def rpc_endpoint(request: Request):
  return await public_vars_get_hostname_v1(request)


client = TestClient(app)


def test_get_hostname_service():
  resp = client.post("/rpc", json={"op": "urn:public:vars:get_hostname:1"})
  assert resp.status_code == 200
  data = resp.json()
  assert data["op"] == "urn:public:vars:get_hostname:1"
  assert data["payload"] == {"hostname": "example.com"}


app_version = FastAPI()
app_version.state.public_vars = DummyVarsVersionModule()


@app_version.post("/rpc")
async def rpc_endpoint_version(request: Request):
  return await public_vars_get_version_v1(request)


client_version = TestClient(app_version)


def test_get_version_service():
  resp = client_version.post("/rpc", json={"op": "urn:public:vars:get_version:1"})
  assert resp.status_code == 200
  data = resp.json()
  assert data["op"] == "urn:public:vars:get_version:1"
  assert data["payload"] == {"version": "1.2.3"}


app_versions = FastAPI()
app_versions.state.public_vars = DummyVarsVersionsModule()


@app_versions.post("/rpc")
async def rpc_endpoint_versions(request: Request):
  request.state.rpc_request = RPCRequest(op="urn:public:vars:get_versions:1")
  request.state.auth_ctx = AuthContext(role_mask=0)
  return await public_vars_get_versions_v1(request)


client_versions = TestClient(app_versions)


def test_get_versions_public():
  resp = client_versions.post("/rpc", json={})
  assert resp.status_code == 200
  data = resp.json()
  assert data["op"] == "urn:public:vars:get_versions:1"
  assert data["payload"] == {"hostname": "example.com", "version": "1.2.3", "repo": "https://repo"}


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

