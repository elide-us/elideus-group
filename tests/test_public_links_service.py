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
  version: int
  request_id: str = "test-request-id"

class RPCResponse(BaseModel):
  op: str
  payload: dict
  version: int
  error: dict | None = None

class AuthContext(BaseModel):
  role_mask: int = 0

def ensure_json_serializable(value, *, field_name):
  return value

models_pkg.RPCRequest = RPCRequest
models_pkg.RPCResponse = RPCResponse
models_pkg.AuthContext = AuthContext
models_pkg.ensure_json_serializable = ensure_json_serializable
server_pkg.models = models_pkg
errors_pkg = types.ModuleType('server.errors')

class RPCServiceError(Exception):
  def __init__(self, message, *, code='rpc.test', status_code=500, public_details=None, diagnostic=None):
    super().__init__(message)
    self.detail = types.SimpleNamespace(
      code=code,
      status_code=status_code,
      message=message,
      public_details=public_details,
      diagnostic=diagnostic or message,
    )


def _factory(status_code: int, default_code: str):
  def _build(message: str, *, code: str = default_code, public_details=None, diagnostic=None):
    return RPCServiceError(
      message,
      code=code,
      status_code=status_code,
      public_details=public_details,
      diagnostic=diagnostic,
    )
  return _build


errors_pkg.RPCServiceError = RPCServiceError
errors_pkg.bad_request = _factory(400, 'rpc.bad_request')
errors_pkg.unauthorized = _factory(401, 'rpc.unauthorized')
errors_pkg.forbidden = _factory(403, 'rpc.forbidden')
errors_pkg.not_found = _factory(404, 'rpc.not_found')
errors_pkg.conflict = _factory(409, 'rpc.conflict')
errors_pkg.internal_error = _factory(500, 'rpc.internal')
errors_pkg.service_unavailable = _factory(503, 'rpc.unavailable')
errors_pkg.as_http_exception = lambda exc: exc
server_pkg.errors = errors_pkg
sys.modules.setdefault('server', server_pkg)
sys.modules.setdefault('server.models', models_pkg)
sys.modules.setdefault('server.errors', errors_pkg)

from rpc.public.links.services import public_links_get_home_links_v1, public_links_get_navbar_routes_v1


class DummyLinksModule:
  async def get_home_links(self):
    return [{"title": "GitHub", "url": "https://github.com"}]
  async def get_navbar_routes(self, role_mask):
    assert role_mask == 0
    return [
      {"path": "/", "name": "Home", "icon": "home", "sequence": 0},
      {"path": "/gallery", "name": "Gallery", "icon": "gallery", "sequence": 50},
    ]


app = FastAPI()
app.state.public_links = DummyLinksModule()


@app.post("/rpc")
async def rpc_endpoint(request: Request):
  body = await request.json()
  if body["op"] == "urn:public:links:get_home_links:1":
    return await public_links_get_home_links_v1(request)
  if body["op"] == "urn:public:links:get_navbar_routes:1":
    return await public_links_get_navbar_routes_v1(request)
  raise AssertionError("unexpected op")


client = TestClient(app)


def test_get_home_links_service():
  resp = client.post("/rpc", json={"op": "urn:public:links:get_home_links:1", "version": 1})
  assert resp.status_code == 200
  data = resp.json()
  assert data["op"] == "urn:public:links:get_home_links:1"
  assert data["payload"] == {
    "links": [{"title": "GitHub", "url": "https://github.com"}]
  }


def test_get_navbar_routes_service():
  resp = client.post("/rpc", json={"op": "urn:public:links:get_navbar_routes:1", "version": 1})
  assert resp.status_code == 200
  data = resp.json()
  assert data["op"] == "urn:public:links:get_navbar_routes:1"
  assert data["payload"] == {
    "routes": [
      {"path": "/", "name": "Home", "icon": "home", "sequence": 0},
      {"path": "/gallery", "name": "Gallery", "icon": "gallery", "sequence": 50},
    ]
  }

