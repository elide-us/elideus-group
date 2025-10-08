import importlib
import importlib.util
import logging
import pathlib
import sys
import time
import types
import uuid

from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from server.helpers.discord_signing import compute_signature
from server.errors import RPCServiceError, as_http_exception
from server.registry.types import DBRequest

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
SIGNING_SECRET = "discord-signing-secret"


class AuthModule:
  def __init__(self, roles: dict[str, int] | None = None):
    self.roles = dict({"ROLE_REGISTERED": 0x1} if roles is None else roles)
    self.role_registered = self.roles.get("ROLE_REGISTERED", 0)

  async def decode_session_token(self, token: str) -> dict:
    if token != "valid":
      raise ValueError("invalid token")
    return {"sub": "service-guid", "provider": "discord"}

  async def get_user_roles(self, guid: str):
    if self.role_registered:
      return (["ROLE_REGISTERED"], self.role_registered)
    return ([], self.role_registered)

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


class ConfigDb:
  def __init__(self, secret: str = SIGNING_SECRET):
    self.secret = secret

  async def on_ready(self):
    return None

  async def run(self, request):
    if isinstance(request, DBRequest):
      key = request.params.get("key")
      op = request.op
    else:
      key = request.get("key") if isinstance(request, dict) else None
      op = request
    class Result:
      def __init__(self, rows):
        self.rows = rows
    if op == "db:system:config:get_config:1" and key == "DiscordRpcSigningSecret":
      return Result([{ "value": self.secret }])
    return Result([])


def _create_app(auth_module: AuthModule, *, secret: str = SIGNING_SECRET) -> FastAPI:
  app = FastAPI()
  app.state.auth = auth_module
  app.state.db = ConfigDb(secret)

  @app.exception_handler(RPCServiceError)
  async def _handle_rpc_error(request: Request, exc: RPCServiceError):
    raise as_http_exception(exc)

  return app


def _signed_headers(
  body: dict,
  *,
  token: bool = True,
  user_id: str | None = None,
  guild_id: str | None = None,
  channel_id: str | None = None,
  timestamp: int | None = None,
  secret: str = SIGNING_SECRET,
) -> dict[str, str]:
  headers: dict[str, str] = {}
  if token:
    headers["Authorization"] = "Bearer valid"
  if user_id is not None:
    headers["X-Discord-Id"] = str(user_id)
  if guild_id is not None:
    headers["X-Discord-Guild-Id"] = str(guild_id)
  if channel_id is not None:
    headers["X-Discord-Channel-Id"] = str(channel_id)
  ts_value = str(timestamp if timestamp is not None else int(time.time()))
  signature = compute_signature(
    secret,
    body=dict(body),
    timestamp=ts_value,
    user_id=headers.get("X-Discord-Id"),
    guild_id=headers.get("X-Discord-Guild-Id"),
    channel_id=headers.get("X-Discord-Channel-Id"),
  )
  headers["X-Discord-Signature"] = signature
  headers["X-Discord-Signature-Timestamp"] = ts_value
  return headers


def test_unbox_request_requires_token_for_discord():
  if 'rpc.helpers' in sys.modules:
    del sys.modules['rpc.helpers']
  helpers = importlib.import_module('rpc.helpers')

  app = _create_app(AuthModule())

  @app.post('/rpc')
  async def endpoint(request: Request):
    await helpers.unbox_request(request)
    return {}

  client = TestClient(app)
  body = {'op': 'urn:discord:command:get_roles:1', 'version': 1}
  resp = client.post('/rpc', json=body)
  assert resp.status_code == 401


def test_unbox_request_with_discord_header_and_token():
  if 'rpc.helpers' in sys.modules:
    del sys.modules['rpc.helpers']
  helpers = importlib.import_module('rpc.helpers')

  app = _create_app(AuthModule())

  @app.post('/rpc')
  async def endpoint(request: Request):
    rpc_request, auth_ctx, _ = await helpers.unbox_request(request)
    return {'user_guid': rpc_request.user_guid, 'roles': auth_ctx.roles}

  client = TestClient(app)
  body = {'op': 'urn:discord:command:get_roles:1', 'version': 1}
  resp = client.post(
    '/rpc',
    json=body,
    headers=_signed_headers(body, user_id='42'),
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
  resp = client.post(
    '/rpc',
    json=body,
    headers=_signed_headers(body),
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

  app = _create_app(AuthModule())

  @app.post('/rpc')
  async def endpoint(request: Request):
    rpc_request, auth_ctx, _ = await helpers.unbox_request(request)
    return {'user_guid': rpc_request.user_guid, 'roles': auth_ctx.roles}

  client = TestClient(app)
  body = {'op': 'urn:discord:command:get_roles:1', 'payload': {'discord_id': '123'}, 'version': 1}
  resp = client.post(
    '/rpc',
    json=body,
    headers=_signed_headers(body),
  )
  assert resp.status_code == 401


def test_unbox_request_rejects_spoofed_discord_id(caplog):
  if 'rpc.helpers' in sys.modules:
    del sys.modules['rpc.helpers']
  helpers = importlib.import_module('rpc.helpers')

  app = _create_app(AuthModule())

  @app.post('/rpc')
  async def endpoint(request: Request):
    rpc_request, auth_ctx, _ = await helpers.unbox_request(request)
    return {'user_guid': rpc_request.user_guid, 'roles': auth_ctx.roles}

  client = TestClient(app)
  body = {'op': 'urn:discord:command:get_roles:1', 'version': 1}
  headers = _signed_headers(body, user_id='42')
  headers['X-Discord-Id'] = '999'
  with caplog.at_level(logging.ERROR, logger='security.audit'):
    resp = client.post('/rpc', json=body, headers=headers)
  assert resp.status_code == 401
  failures = [record for record in caplog.records if record.getMessage() == 'rpc.discord.signature.failure']
  assert failures, 'expected audit log for signature failure'
  assert any(getattr(record, 'reason', '') == 'mismatch' for record in failures)


def test_unbox_request_missing_registered_role_logs_and_denies(caplog):
  if 'rpc.helpers' in sys.modules:
    del sys.modules['rpc.helpers']
  helpers = importlib.import_module('rpc.helpers')

  app = _create_app(AuthModule(roles={}))

  @app.post('/rpc')
  async def endpoint(request: Request):
    rpc_request, auth_ctx, _ = await helpers.unbox_request(request)
    return {'user_guid': rpc_request.user_guid, 'roles': auth_ctx.roles}

  client = TestClient(app)
  body = {'op': 'urn:discord:command:get_roles:1', 'version': 1}
  headers = _signed_headers(body, user_id='42')
  with caplog.at_level(logging.ERROR, logger='security.audit'):
    resp = client.post('/rpc', json=body, headers=headers)
  assert resp.status_code == 403
  records = [record for record in caplog.records if record.getMessage() == 'rpc.role.undefined']
  assert records, 'expected audit log for missing role definition'
  assert any(getattr(record, 'context', '') == 'discord.identity' for record in records)
