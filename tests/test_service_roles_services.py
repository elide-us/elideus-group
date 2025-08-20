import asyncio
import importlib.util
import pathlib
import types
from types import SimpleNamespace
import sys

import pytest

# stub rpc package and load required modules
root_path = pathlib.Path(__file__).resolve().parent.parent
rpc_pkg = types.ModuleType("rpc")
rpc_pkg.__path__ = [str(root_path / "rpc")]
rpc_pkg.HANDLERS = {}
sys.modules["rpc"] = rpc_pkg

spec_models = importlib.util.spec_from_file_location(
  "rpc.models", root_path / "rpc/models.py"
)
models_mod = importlib.util.module_from_spec(spec_models)
spec_models.loader.exec_module(models_mod)
RPCRequest = models_mod.RPCRequest
RPCResponse = models_mod.RPCResponse
sys.modules["rpc.models"] = models_mod

spec_helpers = importlib.util.spec_from_file_location(
  "rpc.helpers", root_path / "rpc/helpers.py"
)
helpers = importlib.util.module_from_spec(spec_helpers)
spec_helpers.loader.exec_module(helpers)
sys.modules["rpc.helpers"] = helpers

service_pkg = types.ModuleType("rpc.service")
service_pkg.__path__ = [str(root_path / "rpc/service")]
service_pkg.HANDLERS = {}
service_pkg.DISPATCHERS = {}
sys.modules["rpc.service"] = service_pkg

spec_service_handler = importlib.util.spec_from_file_location(
  "rpc.service.handler", root_path / "rpc/service/handler.py"
)
service_handler = importlib.util.module_from_spec(spec_service_handler)
sys.modules["rpc.service.handler"] = service_handler
spec_service_handler.loader.exec_module(service_handler)
rpc_pkg.HANDLERS["service"] = service_handler.handle_service_request

spec_rpc_handler = importlib.util.spec_from_file_location(
  "rpc.handler", root_path / "rpc/handler.py"
)
handler_mod = importlib.util.module_from_spec(spec_rpc_handler)
sys.modules["rpc.handler"] = handler_mod
spec_rpc_handler.loader.exec_module(handler_mod)
handle_rpc_request = handler_mod.handle_rpc_request

# stub server modules needed by service handler
server_pkg = types.ModuleType("server")
sys.modules.setdefault("server", server_pkg)
modules_stub = types.ModuleType("server.modules")
sys.modules.setdefault("server.modules", modules_stub)
auth_module_stub = types.ModuleType("server.modules.auth_module")
class AuthModule: ...
auth_module_stub.AuthModule = AuthModule
modules_stub.auth_module = auth_module_stub
sys.modules["server.modules.auth_module"] = auth_module_stub


class DBRes:
  def __init__(self, rows=None, rowcount=0):
    self.rows = rows or []
    self.rowcount = rowcount


class DummyDb:
  def __init__(self, members=None, non_members=None):
    self.calls = []
    self.members = members or []
    self.non_members = non_members or []

  async def run(self, op, args):
    self.calls.append((op, args))
    if op == "db:security:roles:get_role_members:1":
      return DBRes(self.members, len(self.members))
    if op == "db:security:roles:get_role_non_members:1":
      return DBRes(self.non_members, len(self.non_members))
    return DBRes()


class DummyAuth:
  def __init__(self):
    self.loaded = False
    self.roles = {"ROLE_ACCOUNT_ADMIN": 1, "ROLE_SYSTEM_ADMIN": 2}
    self.user_roles: dict[str, int] = {}

  async def refresh_role_cache(self):
    self.loaded = True

  def get_role_names(self, exclude_registered=False):
    return ["ROLE_ACCOUNT_ADMIN"]

  def names_to_mask(self, names):
    mask = 0
    for n in names:
      mask |= self.roles.get(n, 0)
    return mask

  async def user_has_role(self, guid: str, mask: int) -> bool:
    return bool(self.user_roles.get(guid, 0) & mask)


class DummyState:
  def __init__(self, db, auth):
    self.db = db
    self.auth = auth


class DummyApp:
  def __init__(self, state):
    self.state = state


class DummyRequest:
  def __init__(self, state):
    self.app = DummyApp(state)
    self.headers = {}


# Stub server modules for services
modules_pkg = sys.modules["server.modules"]
auth_module_pkg = sys.modules["server.modules.auth_module"]

db_module_pkg = types.ModuleType("server.modules.db_module")
class DbModule: ...
db_module_pkg.DbModule = DbModule
modules_pkg.db_module = db_module_pkg
sys.modules["server.modules.db_module"] = db_module_pkg

# Import services after stubbing
roles_pkg = types.ModuleType("rpc.service.roles")
roles_pkg.__path__ = [str(root_path / "rpc/service/roles")]
sys.modules.setdefault("rpc.service.roles", roles_pkg)

svc_spec = importlib.util.spec_from_file_location(
  "rpc.service.roles.services", "rpc/service/roles/services.py"
)
svc_mod = importlib.util.module_from_spec(svc_spec)
sys.modules["rpc.service.roles.services"] = svc_mod
svc_spec.loader.exec_module(svc_mod)

service_roles_upsert_role_v1 = svc_mod.service_roles_upsert_role_v1
service_roles_add_role_member_v1 = svc_mod.service_roles_add_role_member_v1
service_roles_remove_role_member_v1 = svc_mod.service_roles_remove_role_member_v1


def test_get_roles_allows_system_admin():
  async def fake_get(request):
    rpc = RPCRequest(op="urn:service:roles:get_roles:1", payload=None, version=1)
    auth = SimpleNamespace(user_guid="u1")
    request.app.state.auth.user_roles["u1"] = 0x4000000000000000
    parts = rpc.op.split(":")
    return rpc, auth, parts

  handler_mod.unbox_request = fake_get
  service_handler.unbox_request = fake_get

  called = False

  async def stub(parts, request):
    nonlocal called
    called = True
    return RPCResponse(op="ok", payload=None, version=1)

  service_pkg.HANDLERS["roles"] = stub
  req = DummyRequest(DummyState(DummyDb(), DummyAuth()))
  resp = asyncio.run(handle_rpc_request(req))
  assert isinstance(resp, RPCResponse)
  assert called


def test_upsert_role_calls_db_and_loads_roles():
  async def fake_get(request):
    rpc = RPCRequest(
      op="urn:service:roles:upsert_role:1",
      payload={"name": "ROLE_NEW", "bit": 2, "display": "New"},
      version=1,
    )
    return rpc, None, None

  helpers.unbox_request = fake_get
  svc_mod.unbox_request = fake_get
  db = DummyDb()
  auth = DummyAuth()
  req = DummyRequest(DummyState(db, auth))
  resp = asyncio.run(service_roles_upsert_role_v1(req))
  assert isinstance(resp, RPCResponse)
  assert (
    "db:security:roles:upsert_role:1",
    {"name": "ROLE_NEW", "mask": 4, "display": "New"},
  ) in db.calls
  assert auth.loaded


def test_add_and_remove_member():
  members = [{"guid": "u1", "display_name": "User 1"}]
  non_members = [{"guid": "u2", "display_name": "User 2"}]
  db = DummyDb(members, non_members)
  auth = DummyAuth()
  state = DummyState(db, auth)
  req = DummyRequest(state)

  async def fake_get_add(request):
    rpc = RPCRequest(
      op="urn:service:roles:add_role_member:1",
      payload={"role": "ROLE_X", "userGuid": "u1"},
      version=1,
    )
    return rpc, None, None

  helpers.unbox_request = fake_get_add
  svc_mod.unbox_request = fake_get_add
  resp = asyncio.run(service_roles_add_role_member_v1(req))
  assert any(op == "db:security:roles:add_role_member:1" for op, _ in db.calls)
  assert resp.payload["members"] == [{"guid": "u1", "displayName": "User 1"}]
  assert resp.payload["nonMembers"] == [{"guid": "u2", "displayName": "User 2"}]

  db.calls.clear()
  db.members = []
  db.non_members = [
    {"guid": "u1", "display_name": "User 1"},
    {"guid": "u2", "display_name": "User 2"},
  ]

  async def fake_get_remove(request):
    rpc = RPCRequest(
      op="urn:service:roles:remove_role_member:1",
      payload={"role": "ROLE_X", "userGuid": "u1"},
      version=1,
    )
    return rpc, None, None

  helpers.unbox_request = fake_get_remove
  svc_mod.unbox_request = fake_get_remove
  resp2 = asyncio.run(service_roles_remove_role_member_v1(req))
  assert any(op == "db:security:roles:remove_role_member:1" for op, _ in db.calls)
  assert resp2.payload["members"] == []
  assert resp2.payload["nonMembers"] == [
    {"guid": "u1", "displayName": "User 1"},
    {"guid": "u2", "displayName": "User 2"},
  ]

