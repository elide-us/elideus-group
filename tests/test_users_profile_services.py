import asyncio
import importlib.util
import pathlib
import sys
import types
from types import SimpleNamespace
import pytest
from fastapi import HTTPException
from rpc.users.profile.models import (
  UsersProfileProfile1,
  UsersProfileRoles1,
)

# stub rpc package
pkg = types.ModuleType("rpc")
pkg.__path__ = [str(pathlib.Path(__file__).resolve().parent.parent / "rpc")]
sys.modules.setdefault("rpc", pkg)

spec = importlib.util.spec_from_file_location("server.models", "server/models.py")
models = importlib.util.module_from_spec(spec)
spec.loader.exec_module(models)
RPCRequest = models.RPCRequest
RPCResponse = models.RPCResponse
sys.modules["server.models"] = models

# stub server packages for loading real helpers
server_pkg = types.ModuleType("server")
modules_pkg = types.ModuleType("server.modules")
user_profile_pkg = types.ModuleType("server.modules.user_profile_module")
class UserProfileModule: ...
user_profile_pkg.UserProfileModule = UserProfileModule
modules_pkg.user_profile_module = user_profile_pkg
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
sys.modules.setdefault("server.modules.user_profile_module", user_profile_pkg)
sys.modules.setdefault("server.models", models_pkg)

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

users_profile_get_roles_v1 = svc_mod.users_profile_get_roles_v1
users_profile_set_profile_image_v1 = svc_mod.users_profile_set_profile_image_v1


class DummyProfileModule:
  def __init__(self, roles=0):
    self.calls = []
    self.roles = roles
  async def get_roles(self, guid):
    self.calls.append(("get_roles", guid))
    return UsersProfileRoles1(roles=self.roles)

  async def set_profile_image(self, guid, image_b64, provider):
    self.calls.append(("set_profile_image", guid, image_b64, provider))

  async def get_profile(self, guid):
    self.calls.append(("get_profile", guid))
    return UsersProfileProfile1(
      guid=guid,
      display_name="User",
      email="user@example.com",
      display_email=True,
      credits=0,
      profile_image=None,
      default_provider="microsoft",
      auth_providers=[],
    )

  async def set_display(self, guid, display_name):
    self.calls.append(("set_display", guid, display_name))

  async def set_optin(self, guid, display_email):
    self.calls.append(("set_optin", guid, display_email))

class DummyState:
  def __init__(self, user_profile):
    self.user_profile = user_profile

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
  module = DummyProfileModule(roles=5)
  req = DummyRequest(DummyState(module))
  resp = asyncio.run(users_profile_get_roles_v1(req))
  assert isinstance(resp, RPCResponse)
  assert resp.payload["roles"] == 5
  assert ("get_roles", "u1") in module.calls

def test_set_profile_image_calls_db():
  async def fake_img(request):
    rpc = RPCRequest(op="urn:users:profile:set_profile_image:1", payload={"image_b64": "abc", "provider": "microsoft"}, version=1)
    return rpc, SimpleNamespace(user_guid="u1"), None
  svc_mod.unbox_request = fake_img
  module = DummyProfileModule()
  req = DummyRequest(DummyState(module))
  resp = asyncio.run(users_profile_set_profile_image_v1(req))
  assert ("set_profile_image", "u1", "abc", "microsoft") in module.calls
  assert resp.payload["image_b64"] == "abc"


def test_missing_user_guid_raises():
  async def fake_get(request):
    rpc = RPCRequest(op="urn:users:profile:get_roles:1", payload=None, version=1)
    return rpc, SimpleNamespace(user_guid=None), None
  svc_mod.unbox_request = fake_get
  module = DummyProfileModule()
  req = DummyRequest(DummyState(module))
  with pytest.raises(HTTPException) as exc:
    asyncio.run(users_profile_get_roles_v1(req))
  assert exc.value.status_code == 400
