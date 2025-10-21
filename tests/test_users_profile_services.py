import asyncio
import importlib.util
import pathlib
import sys
import types
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

# stub rpc package
root_path = pathlib.Path(__file__).resolve().parent.parent
pkg = types.ModuleType("rpc")
pkg.__path__ = [str(root_path / "rpc")]
sys.modules.setdefault("rpc", pkg)

spec = importlib.util.spec_from_file_location("server.models", "server/models.py")
models = importlib.util.module_from_spec(spec)
spec.loader.exec_module(models)
RPCRequest = models.RPCRequest
RPCResponse = models.RPCResponse
sys.modules["server.models"] = models

# stub server packages for loading real helpers
server_pkg = types.ModuleType("server")
server_pkg.__path__ = [str(root_path / "server")]
modules_pkg = types.ModuleType("server.modules")
modules_pkg.__path__ = [str(root_path / "server/modules")]
class BaseModule:
  async def startup(self): ...
  async def shutdown(self): ...
modules_pkg.BaseModule = BaseModule
db_module_pkg = types.ModuleType("server.modules.db_module")
class DbModule: ...
db_module_pkg.DbModule = DbModule
modules_pkg.db_module = db_module_pkg
server_pkg.modules = modules_pkg
models_pkg = types.ModuleType("server.models")
class AuthContext:
  def __init__(self, **data):
    self.role_mask = 0
    self.__dict__.update(data)
models_pkg.AuthContext = AuthContext
server_pkg.models = models_pkg

sys.modules.setdefault("server", server_pkg)
sys.modules.setdefault("server.modules", modules_pkg)
sys.modules.setdefault("server.modules.db_module", db_module_pkg)
sys.modules.setdefault("server.models", models_pkg)

registry_pkg = types.ModuleType("server.registry")
registry_pkg.__path__ = [str(root_path / "server/registry")]
registry_types_pkg = types.ModuleType("server.registry.types")
registry_types_pkg.__path__ = [str(root_path / "server/registry")]

class DBRequest:
  def __init__(self, *, op, payload=None, params=None):
    source = payload if payload is not None else params or {}
    self.op = op
    self.payload = dict(source)

class DBResponse:
  def __init__(self, *, op="", payload=None, rows=None, rowcount=None):
    if rows is not None:
      payload = [dict(row) for row in rows]
      if rowcount is None:
        rowcount = len(payload)
    self.op = op
    self.payload = [] if payload is None else payload
    if rowcount is None:
      rowcount = 0
    self.rowcount = rowcount

  @property
  def rows(self):
    data = self.payload
    if data is None:
      return []
    if isinstance(data, list):
      return data
    if isinstance(data, (tuple, set)):
      return list(data)
    return [data]

registry_types_pkg.DBRequest = DBRequest
registry_types_pkg.DBResponse = DBResponse
registry_pkg.types = registry_types_pkg
sys.modules.setdefault("server.registry", registry_pkg)
sys.modules.setdefault("server.registry.types", registry_types_pkg)

auth_module_pkg = types.ModuleType("server.modules.auth_module")
class AuthModule: ...
auth_module_pkg.AuthModule = AuthModule
modules_pkg.auth_module = auth_module_pkg
sys.modules.setdefault("server.modules.auth_module", auth_module_pkg)

# load real helpers then override for service import
real_helpers_spec = importlib.util.spec_from_file_location("rpc.helpers", "rpc/helpers.py")
real_helpers = importlib.util.module_from_spec(real_helpers_spec)
real_helpers_spec.loader.exec_module(real_helpers)

helpers_stub = types.ModuleType("rpc.helpers")
async def _stub(request):
  raise NotImplementedError
helpers_stub.unbox_request = _stub
sys.modules["rpc.helpers"] = helpers_stub

# import services with stubbed helpers
svc_spec = importlib.util.spec_from_file_location("rpc.users.profile.services", "rpc/users/profile/services.py")
svc_mod = importlib.util.module_from_spec(svc_spec)
svc_spec.loader.exec_module(svc_mod)

# restore real helpers for other tests
sys.modules["rpc.helpers"] = real_helpers

users_profile_get_profile_v1 = svc_mod.users_profile_get_profile_v1
users_profile_get_roles_v1 = svc_mod.users_profile_get_roles_v1
users_profile_set_profile_image_v1 = svc_mod.users_profile_set_profile_image_v1

class DBRes:
  def __init__(self, rows=None, rowcount=0):
    self.rows = rows or []
    self.rowcount = rowcount

_DEFAULT_PROVIDERS = object()


class DummyDb:
  def __init__(self, roles=0, auth_providers=_DEFAULT_PROVIDERS):
    self.calls = []
    self.roles = roles
    if auth_providers is _DEFAULT_PROVIDERS:
      auth_providers = [
        {"name": "microsoft", "display": "Microsoft"},
        {"name": "google", "display": "Google"},
      ]
    self.auth_providers = auth_providers
  async def run(self, op, args=None):
    if not isinstance(op, str):
      args = op.payload
      op = op.op
    elif args is None:
      args = {}
    self.calls.append((op, args))
    if op == "db:account:profile:get_profile:1":
      return DBRes([
        {
          "guid": args.get("guid"),
          "display_name": "Test User",
          "email": "user@example.com",
          "display_email": True,
          "credits": 10,
          "profile_image": None,
          "default_provider": "microsoft",
          "auth_providers": self.auth_providers,
        }
      ], 1)
    if op == "db:account:profile:get_roles:1":
      return DBRes([{"element_roles": self.roles}], 1)
    if op == "db:account:profile:set_profile_image:1":
      return DBRes([], 1)
    return DBRes()

class DummyState:
  def __init__(self, db):
    self.db = db

class DummyApp:
  def __init__(self, state):
    self.state = state

class DummyRequest:
  def __init__(self, state):
    self.app = DummyApp(state)
    self.headers = {}

def test_get_roles_service_returns_mask():
  async def fake_get(request):
    rpc = RPCRequest(op="urn:users:profile:get_roles:1", payload=None, version=1)
    return rpc, SimpleNamespace(user_guid="u1"), None
  svc_mod.unbox_request = fake_get
  db = DummyDb(roles=5)
  req = DummyRequest(DummyState(db))
  resp = asyncio.run(users_profile_get_roles_v1(req))
  assert isinstance(resp, RPCResponse)
  assert resp.payload["roles"] == 5
  assert ("db:account:profile:get_roles:1", {"guid": "u1"}) in db.calls


def test_get_profile_returns_structured_auth_providers():
  async def fake_get(request):
    rpc = RPCRequest(op="urn:users:profile:get_profile:1", payload=None, version=1)
    return rpc, SimpleNamespace(user_guid="user-guid"), None
  svc_mod.unbox_request = fake_get
  db = DummyDb()
  req = DummyRequest(DummyState(db))
  resp = asyncio.run(users_profile_get_profile_v1(req))
  assert isinstance(resp, RPCResponse)
  assert resp.payload["guid"] == "user-guid"
  providers = resp.payload["auth_providers"]
  assert isinstance(providers, list)
  assert providers[0]["name"] == "microsoft"
  assert providers[1]["display"] == "Google"
  assert ("db:account:profile:get_profile:1", {"guid": "user-guid"}) in db.calls


def test_get_profile_defaults_auth_providers_to_empty_list():
  async def fake_get(request):
    rpc = RPCRequest(op="urn:users:profile:get_profile:1", payload=None, version=1)
    return rpc, SimpleNamespace(user_guid="user-guid"), None
  svc_mod.unbox_request = fake_get
  db = DummyDb(auth_providers=None)
  req = DummyRequest(DummyState(db))
  resp = asyncio.run(users_profile_get_profile_v1(req))
  assert isinstance(resp, RPCResponse)
  assert resp.payload["auth_providers"] == []


def test_get_profile_raises_on_invalid_auth_providers_shape():
  async def fake_get(request):
    rpc = RPCRequest(op="urn:users:profile:get_profile:1", payload=None, version=1)
    return rpc, SimpleNamespace(user_guid="user-guid"), None
  svc_mod.unbox_request = fake_get
  db = DummyDb(auth_providers="not-json")
  req = DummyRequest(DummyState(db))
  with pytest.raises(HTTPException) as exc:
    asyncio.run(users_profile_get_profile_v1(req))
  assert exc.value.status_code == 500

def test_set_profile_image_calls_db():
  async def fake_img(request):
    rpc = RPCRequest(op="urn:users:profile:set_profile_image:1", payload={"image_b64": "abc", "provider": "microsoft"}, version=1)
    return rpc, SimpleNamespace(user_guid="u1"), None
  svc_mod.unbox_request = fake_img
  db = DummyDb()
  req = DummyRequest(DummyState(db))
  resp = asyncio.run(users_profile_set_profile_image_v1(req))
  assert ("db:account:profile:set_profile_image:1", {"guid": "u1", "image_b64": "abc", "provider": "microsoft"}) in db.calls
  assert resp.payload["image_b64"] == "abc"


def test_missing_user_guid_raises():
  async def fake_get(request):
    rpc = RPCRequest(op="urn:users:profile:get_roles:1", payload=None, version=1)
    return rpc, SimpleNamespace(user_guid=None), None
  svc_mod.unbox_request = fake_get
  db = DummyDb()
  req = DummyRequest(DummyState(db))
  with pytest.raises(HTTPException) as exc:
    asyncio.run(users_profile_get_roles_v1(req))
  assert exc.value.status_code == 400
