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
profile_module_pkg = types.ModuleType("server.modules.profile_module")
class ProfileModule: ...
profile_module_pkg.ProfileModule = ProfileModule
modules_pkg.profile_module = profile_module_pkg
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
sys.modules.setdefault("server.modules.profile_module", profile_module_pkg)
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

_DEFAULT_PROVIDERS = object()


class DummyProfileModule:
  def __init__(self, roles=0, auth_providers=_DEFAULT_PROVIDERS):
    self.calls = []
    self.roles = roles
    if auth_providers is _DEFAULT_PROVIDERS:
      auth_providers = [
        {"name": "microsoft", "display": "Microsoft"},
        {"name": "google", "display": "Google"},
      ]
    self.auth_providers = auth_providers

  async def get_profile(self, guid: str):
    self.calls.append(("get_profile", {"guid": guid}))
    return {
      "guid": guid,
      "display_name": "Test User",
      "email": "user@example.com",
      "display_email": True,
      "credits": 10,
      "profile_image": None,
      "default_provider": "microsoft",
      "auth_providers": self.auth_providers,
    }

  async def set_display(self, guid: str, display_name: str):
    self.calls.append(("set_display", {"guid": guid, "display_name": display_name}))

  async def set_optin(self, guid: str, display_email: bool):
    self.calls.append(("set_optin", {"guid": guid, "display_email": display_email}))

  async def get_roles(self, guid: str) -> int:
    self.calls.append(("get_roles", {"guid": guid}))
    return int(self.roles)

  async def set_profile_image(self, guid: str, provider: str, image_b64: str | None):
    self.calls.append((
      "set_profile_image",
      {"guid": guid, "provider": provider, "image_b64": image_b64},
    ))


class DummyState:
  def __init__(self, profile):
    self.profile = profile

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
  profile = DummyProfileModule(roles=5)
  req = DummyRequest(DummyState(profile))
  resp = asyncio.run(users_profile_get_roles_v1(req))
  assert isinstance(resp, RPCResponse)
  assert resp.payload["roles"] == 5
  assert ("get_roles", {"guid": "u1"}) in profile.calls


def test_get_profile_returns_structured_auth_providers():
  async def fake_get(request):
    rpc = RPCRequest(op="urn:users:profile:get_profile:1", payload=None, version=1)
    return rpc, SimpleNamespace(user_guid="user-guid"), None
  svc_mod.unbox_request = fake_get
  profile = DummyProfileModule()
  req = DummyRequest(DummyState(profile))
  resp = asyncio.run(users_profile_get_profile_v1(req))
  assert isinstance(resp, RPCResponse)
  assert resp.payload["guid"] == "user-guid"
  providers = resp.payload["auth_providers"]
  assert isinstance(providers, list)
  assert providers[0]["name"] == "microsoft"
  assert providers[1]["display"] == "Google"
  assert ("get_profile", {"guid": "user-guid"}) in profile.calls


def test_get_profile_defaults_auth_providers_to_empty_list():
  async def fake_get(request):
    rpc = RPCRequest(op="urn:users:profile:get_profile:1", payload=None, version=1)
    return rpc, SimpleNamespace(user_guid="user-guid"), None
  svc_mod.unbox_request = fake_get
  profile = DummyProfileModule(auth_providers=None)
  req = DummyRequest(DummyState(profile))
  resp = asyncio.run(users_profile_get_profile_v1(req))
  assert isinstance(resp, RPCResponse)
  assert resp.payload["auth_providers"] == []


def test_get_profile_raises_on_invalid_auth_providers_shape():
  async def fake_get(request):
    rpc = RPCRequest(op="urn:users:profile:get_profile:1", payload=None, version=1)
    return rpc, SimpleNamespace(user_guid="user-guid"), None
  svc_mod.unbox_request = fake_get
  profile = DummyProfileModule(auth_providers="not-json")
  req = DummyRequest(DummyState(profile))
  with pytest.raises(HTTPException) as exc:
    asyncio.run(users_profile_get_profile_v1(req))
  assert exc.value.status_code == 500

def test_set_profile_image_calls_db():
  async def fake_img(request):
    rpc = RPCRequest(op="urn:users:profile:set_profile_image:1", payload={"image_b64": "abc", "provider": "microsoft"}, version=1)
    return rpc, SimpleNamespace(user_guid="u1"), None
  svc_mod.unbox_request = fake_img
  profile = DummyProfileModule()
  req = DummyRequest(DummyState(profile))
  resp = asyncio.run(users_profile_set_profile_image_v1(req))
  assert (
    "set_profile_image",
    {"guid": "u1", "image_b64": "abc", "provider": "microsoft"},
  ) in profile.calls
  assert resp.payload["image_b64"] == "abc"


def test_missing_user_guid_raises():
  async def fake_get(request):
    rpc = RPCRequest(op="urn:users:profile:get_roles:1", payload=None, version=1)
    return rpc, SimpleNamespace(user_guid=None), None
  svc_mod.unbox_request = fake_get
  profile = DummyProfileModule()
  req = DummyRequest(DummyState(profile))
  with pytest.raises(HTTPException) as exc:
    asyncio.run(users_profile_get_roles_v1(req))
  assert exc.value.status_code == 400
