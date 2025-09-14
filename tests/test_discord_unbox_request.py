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
  async def get_user_roles(self, guid: str):
    return (["ROLE_REGISTERED"], 0x1)
auth_module_pkg.AuthModule = AuthModule
modules_pkg.auth_module = auth_module_pkg
sys.modules['server.modules.auth_module'] = auth_module_pkg


def test_unbox_request_with_discord_id():
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
    headers={'x-discord-id': '42'}
  )
  assert resp.status_code == 200
  data = resp.json()
  expected_guid = str(uuid.uuid5(uuid.NAMESPACE_URL, 'discord:42'))
  assert data['user_guid'] == expected_guid
  assert data['roles'] == ['ROLE_REGISTERED']


def test_unbox_request_with_discord_user_id():
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
    headers={'x-discord-user-id': '99'}
  )
  assert resp.status_code == 200
  data = resp.json()
  expected_guid = str(uuid.uuid5(uuid.NAMESPACE_URL, 'discord:99'))
  assert data['user_guid'] == expected_guid
  assert data['roles'] == ['ROLE_REGISTERED']


def test_unbox_request_with_payload_discord_id():
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
  )
  assert resp.status_code == 200
  data = resp.json()
  expected_guid = str(uuid.uuid5(uuid.NAMESPACE_URL, 'discord:123'))
  assert data['user_guid'] == expected_guid
  assert data['roles'] == ['ROLE_REGISTERED']
