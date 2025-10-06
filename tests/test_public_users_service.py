import sys, types, pathlib
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

# Stub rpc package
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

def ensure_json_serializable(value, *, field_name):
  return value

models_pkg.RPCRequest = RPCRequest
models_pkg.RPCResponse = RPCResponse
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

from rpc.public.users.services import (
  public_users_get_profile_v1,
  public_users_get_published_files_v1,
)

class DummyPublicUsersModule:
  async def get_profile(self, guid: str):
    assert guid == '123'
    return {'display_name': 'Alice', 'email': 'alice@example.com', 'profile_image': 'abc'}

  async def get_published_files(self, guid: str):
    assert guid == '123'
    return [{'path': '/a', 'filename': 'file.txt', 'url': 'http://example/a/file.txt', 'content_type': 'audio/mpeg'}]

app = FastAPI()
app.state.public_users = DummyPublicUsersModule()

@app.post('/rpc')
async def rpc_endpoint(request: Request):
  body = await request.json()
  if body['op'] == 'urn:public:users:get_profile:1':
    return await public_users_get_profile_v1(request)
  if body['op'] == 'urn:public:users:get_published_files:1':
    return await public_users_get_published_files_v1(request)
  raise AssertionError('unexpected op')

client = TestClient(app)

def test_get_profile_service():
  resp = client.post('/rpc', json={'op': 'urn:public:users:get_profile:1', 'payload': {'guid': '123'}, 'version': 1})
  assert resp.status_code == 200
  data = resp.json()
  assert data['payload'] == {
    'display_name': 'Alice',
    'email': 'alice@example.com',
    'profile_image': 'abc',
  }

def test_get_published_files_service():
  resp = client.post('/rpc', json={'op': 'urn:public:users:get_published_files:1', 'payload': {'guid': '123'}, 'version': 1})
  assert resp.status_code == 200
  data = resp.json()
  assert data['payload'] == {
    'files': [{'path': '/a', 'filename': 'file.txt', 'url': 'http://example/a/file.txt', 'content_type': 'audio/mpeg'}]
  }
