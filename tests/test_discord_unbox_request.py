import importlib
import importlib.util
import pathlib
import sys
import types
import uuid
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

# Stub rpc package
pkg = types.ModuleType('rpc')
pkg.__path__ = [str(pathlib.Path(__file__).resolve().parent.parent / 'rpc')]
sys.modules.setdefault('rpc', pkg)

# Load server models
spec = importlib.util.spec_from_file_location(
  'server.models', pathlib.Path(__file__).resolve().parent.parent / 'server/models.py'
)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
sys.modules['server.models'] = mod

# Stub auth module
modules_pkg = types.ModuleType('server.modules')
sys.modules.setdefault('server.modules', modules_pkg)
auth_module_pkg = types.ModuleType('server.modules.auth_module')
class AuthModule:
  def __init__(self):
    self.roles = {"ROLE_REGISTERED": 0x1}
    self.role_registered = 0x1

  async def decode_session_token(self, token: str) -> dict:
    if token != "valid":
      raise ValueError("invalid token")
    return {"sub": "service-guid", "provider": "discord"}

  async def get_user_roles(self, guid: str):
    return (["ROLE_REGISTERED"], 0x1)

  def require_role_mask(self, name: str) -> int:
    if name not in self.roles:
      raise KeyError(f"Role {name} is not defined")
    return self.roles[name]

  async def get_discord_user_security(self, discord_id: str):
    guid = str(uuid.uuid5(uuid.NAMESPACE_URL, f"discord:{discord_id}"))
    return (guid, ["ROLE_REGISTERED"], 0x1)
auth_module_pkg.AuthModule = AuthModule
modules_pkg.auth_module = auth_module_pkg
sys.modules['server.modules.auth_module'] = auth_module_pkg


def _headers_with_token(**extra):
  headers = {"Authorization": "Bearer valid"}
  headers.update({k: str(v) for k, v in extra.items()})
  return headers


def test_unbox_request_requires_token_for_discord():
  if 'rpc.helpers' in sys.modules:
    del sys.modules['rpc.helpers']
  helpers = importlib.import_module('rpc.helpers')

  app = FastAPI()
  app.state.auth = AuthModule()

  @app.post('/rpc')
  async def endpoint(request: Request):
    await helpers.unbox_request(request)
    return {}

  client = TestClient(app)
  resp = client.post(
    '/rpc',
    json={'op': 'urn:discord:command:get_roles:1'},
  )
  assert resp.status_code == 401


def test_unbox_request_with_discord_header_and_token():
  if 'rpc.helpers' in sys.modules:
    del sys.modules['rpc.helpers']
  helpers = importlib.import_module('rpc.helpers')

  app = FastAPI()
  app.state.auth = AuthModule()

  @app.post('/rpc')
  async def endpoint(request: Request):
    rpc_request, auth_ctx, _ = await helpers.unbox_request(request)
    return {'user_guid': rpc_request.user_guid, 'roles': auth_ctx.roles}

  client = TestClient(app)
  resp = client.post(
    '/rpc',
    json={'op': 'urn:discord:command:get_roles:1'},
    headers=_headers_with_token(**{'x-discord-id': '42'})
  )
  assert resp.status_code == 200
  data = resp.json()
  expected_guid = str(uuid.uuid5(uuid.NAMESPACE_URL, 'discord:42'))
  assert data['user_guid'] == expected_guid
  assert data['roles'] == ['ROLE_REGISTERED']


def test_unbox_request_with_context_discord_id():
  if 'rpc.helpers' in sys.modules:
    del sys.modules['rpc.helpers']
  helpers = importlib.import_module('rpc.helpers')

  app = FastAPI()
  app.state.auth = AuthModule()

  class DummyCtx:
    class Author:
      id = 555
    author = Author()

  @app.post('/rpc')
  async def endpoint(request: Request):
    request.state.discord_ctx = DummyCtx()
    rpc_request, auth_ctx, _ = await helpers.unbox_request(request)
    return {'user_guid': rpc_request.user_guid, 'roles': auth_ctx.roles}

  client = TestClient(app)
  resp = client.post(
    '/rpc',
    json={'op': 'urn:discord:command:get_roles:1'},
    headers=_headers_with_token()
  )
  assert resp.status_code == 200
  data = resp.json()
  expected_guid = str(uuid.uuid5(uuid.NAMESPACE_URL, 'discord:555'))
  assert data['user_guid'] == expected_guid
  assert data['roles'] == ['ROLE_REGISTERED']


def test_unbox_request_rejects_payload_discord_id():
  if 'rpc.helpers' in sys.modules:
    del sys.modules['rpc.helpers']
  helpers = importlib.import_module('rpc.helpers')

  app = FastAPI()
  app.state.auth = AuthModule()

  @app.post('/rpc')
  async def endpoint(request: Request):
    rpc_request, auth_ctx, _ = await helpers.unbox_request(request)
    return {'user_guid': rpc_request.user_guid, 'roles': auth_ctx.roles}

  client = TestClient(app)
  resp = client.post(
    '/rpc',
    json={'op': 'urn:discord:command:get_roles:1', 'payload': {'discord_id': '123'}},
    headers=_headers_with_token()
  )
  assert resp.status_code == 401
