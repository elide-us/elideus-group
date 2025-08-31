import asyncio
import importlib.util
import pathlib
import sys
import types
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

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

class DBRes:
  def __init__(self, rows=None, rowcount=0):
    self.rows = rows or []
    self.rowcount = rowcount

class DummyDb:
  def __init__(self, roles=0):
    self.calls = []
    self.roles = roles
  async def run(self, op, args):
    self.calls.append((op, args))
    if op == "urn:users:profile:get_roles:1":
      return DBRes([{"element_roles": self.roles}], 1)
    if op == "urn:users:profile:set_profile_image:1":
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
  assert ("urn:users:profile:get_roles:1", {"guid": "u1"}) in db.calls

def test_set_profile_image_calls_db():
  async def fake_img(request):
    rpc = RPCRequest(op="urn:users:profile:set_profile_image:1", payload={"image_b64": "abc", "provider": "microsoft"}, version=1)
    return rpc, SimpleNamespace(user_guid="u1"), None
  svc_mod.unbox_request = fake_img
  db = DummyDb()
  req = DummyRequest(DummyState(db))
  resp = asyncio.run(users_profile_set_profile_image_v1(req))
  assert ("urn:users:profile:set_profile_image:1", {"guid": "u1", "image_b64": "abc", "provider": "microsoft"}) in db.calls
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
