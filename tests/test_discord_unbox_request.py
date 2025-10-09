import importlib
import logging
import sys
import types
import uuid

from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from server.errors import RPCServiceError, as_http_exception


modules_pkg = types.ModuleType('server.modules')
sys.modules.setdefault('server.modules', modules_pkg)
auth_module_pkg = types.ModuleType('server.modules.auth_module')


class AuthModule:
  def __init__(self, roles: dict[str, int] | None = None):
    self.roles = dict({"ROLE_REGISTERED": 0x1} if roles is None else roles)

  async def decode_session_token(self, token: str) -> dict:
    if token != "valid":
      raise ValueError("invalid token")
    return {"sub": "service-guid", "provider": "discord"}

  async def get_user_roles(self, guid: str):
    mask = self.roles.get("ROLE_REGISTERED", 0)
    if mask:
      return (["ROLE_REGISTERED"], mask)
    return ([], mask)

  def require_role_mask(self, name: str) -> int:
    if name not in self.roles:
      raise KeyError(f"Role {name} is not defined")
    return self.roles[name]

  async def get_discord_user_security(self, discord_id: str):
    guid = str(uuid.uuid5(uuid.NAMESPACE_URL, f"discord:{discord_id}"))
    mask = self.roles.get("ROLE_REGISTERED", 0)
    roles = ["ROLE_REGISTERED"] if mask else []
    return (guid, roles, mask)

auth_module_pkg.AuthModule = AuthModule
modules_pkg.auth_module = auth_module_pkg
sys.modules['server.modules.auth_module'] = auth_module_pkg


def _load_helpers():
  sys.modules.pop('rpc.helpers', None)
  return importlib.import_module('rpc.helpers')


def _create_app(auth_module: AuthModule) -> FastAPI:
  app = FastAPI()
  app.state.auth = auth_module

  @app.exception_handler(RPCServiceError)
  async def _handle_rpc_error(request: Request, exc: RPCServiceError):
    raise as_http_exception(exc)

  return app


def test_unbox_request_requires_metadata_for_discord():
  helpers = _load_helpers()
  app = _create_app(AuthModule())

  @app.post('/rpc')
  async def endpoint(request: Request):
    await helpers.unbox_request(request)
    return {}

  client = TestClient(app)
  body = {'op': 'urn:discord:command:get_roles:1', 'version': 1}
  resp = client.post('/rpc', json=body)
  assert resp.status_code == 401


def test_unbox_request_accepts_discord_metadata_without_token():
  helpers = _load_helpers()
  app = _create_app(AuthModule())

  @app.post('/rpc')
  async def endpoint(request: Request):
    request.state.discord_metadata = {'user_id': '42'}
    rpc_request, auth_ctx, _ = await helpers.unbox_request(request)
    return {'user_guid': rpc_request.user_guid, 'roles': auth_ctx.roles}

  client = TestClient(app)
  body = {'op': 'urn:discord:command:get_roles:1', 'version': 1}
  resp = client.post('/rpc', json=body)
  assert resp.status_code == 200
  data = resp.json()
  expected_guid = str(uuid.uuid5(uuid.NAMESPACE_URL, 'discord:42'))
  assert data['user_guid'] == expected_guid
  assert data['roles'] == ['ROLE_REGISTERED']


def test_unbox_request_with_context_discord_id():
  helpers = _load_helpers()
  app = _create_app(AuthModule())

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
  body = {'op': 'urn:discord:command:get_roles:1', 'version': 1}
  resp = client.post('/rpc', json=body)
  assert resp.status_code == 200
  data = resp.json()
  expected_guid = str(uuid.uuid5(uuid.NAMESPACE_URL, 'discord:555'))
  assert data['user_guid'] == expected_guid
  assert data['roles'] == ['ROLE_REGISTERED']


def test_unbox_request_rejects_payload_discord_id():
  helpers = _load_helpers()
  app = _create_app(AuthModule())

  @app.post('/rpc')
  async def endpoint(request: Request):
    rpc_request, auth_ctx, _ = await helpers.unbox_request(request)
    return {'user_guid': rpc_request.user_guid, 'roles': auth_ctx.roles}

  client = TestClient(app)
  body = {
    'op': 'urn:discord:command:get_roles:1',
    'payload': {'discord_id': '123'},
    'version': 1,
  }
  resp = client.post('/rpc', json=body)
  assert resp.status_code == 401


def test_unbox_request_prefers_structured_metadata_over_headers():
  helpers = _load_helpers()
  app = _create_app(AuthModule())

  @app.post('/rpc')
  async def endpoint(request: Request):
    request.state.discord_metadata = {'user_id': '42'}
    rpc_request, auth_ctx, _ = await helpers.unbox_request(request)
    return {'user_guid': rpc_request.user_guid, 'roles': auth_ctx.roles}

  client = TestClient(app)
  body = {'op': 'urn:discord:command:get_roles:1', 'version': 1}
  headers = {'X-Discord-Id': '999'}
  resp = client.post('/rpc', json=body, headers=headers)
  assert resp.status_code == 200
  data = resp.json()
  expected_guid = str(uuid.uuid5(uuid.NAMESPACE_URL, 'discord:42'))
  assert data['user_guid'] == expected_guid
  assert data['roles'] == ['ROLE_REGISTERED']


def test_unbox_request_missing_registered_role_logs_and_denies(caplog):
  helpers = _load_helpers()
  app = _create_app(AuthModule(roles={}))

  @app.post('/rpc')
  async def endpoint(request: Request):
    request.state.discord_metadata = {'user_id': '42'}
    rpc_request, auth_ctx, _ = await helpers.unbox_request(request)
    return {'user_guid': rpc_request.user_guid, 'roles': auth_ctx.roles}

  client = TestClient(app)
  body = {'op': 'urn:discord:command:get_roles:1', 'version': 1}
  with caplog.at_level(logging.ERROR, logger='security.audit'):
    resp = client.post('/rpc', json=body)
  assert resp.status_code == 403
  records = [record for record in caplog.records if record.getMessage() == 'rpc.role.undefined']
  assert records, 'expected audit log for missing role definition'
  assert any(getattr(record, 'context', '') == 'discord.identity' for record in records)
