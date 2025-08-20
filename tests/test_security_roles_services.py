import asyncio
import importlib.util
import types
from types import SimpleNamespace
import sys

import pytest

from rpc.models import RPCRequest, RPCResponse
import rpc.handler as handler_mod
import rpc.security as security_pkg
import rpc.security.handler as security_handler
import rpc.helpers as helpers

handle_rpc_request = handler_mod.handle_rpc_request


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
    self.roles = {"ROLE_SECURITY_ADMIN": 1, "ROLE_SYSTEM_ADMIN": 2}
    self.user_roles: dict[str, int] = {}

  async def refresh_role_cache(self):
    self.loaded = True

  def get_role_names(self, exclude_registered=False):
    return ["ROLE_SECURITY_ADMIN"]

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
auth_module_pkg = types.ModuleType("server.modules.auth_module")
class AuthModule: ...
auth_module_pkg.AuthModule = AuthModule
modules_pkg = types.ModuleType("server.modules")
modules_pkg.auth_module = auth_module_pkg
sys_modules = sys.modules
sys_modules.setdefault("server.modules", modules_pkg)
sys_modules["server.modules.auth_module"] = auth_module_pkg

db_module_pkg = types.ModuleType("server.modules.db_module")
class DbModule: ...
db_module_pkg.DbModule = DbModule
modules_pkg.db_module = db_module_pkg
sys_modules["server.modules.db_module"] = db_module_pkg

# Import services after stubbing
svc_spec = importlib.util.spec_from_file_location(
  "rpc.security.roles.services", "rpc/security/roles/services.py"
)
svc_mod = importlib.util.module_from_spec(svc_spec)
svc_spec.loader.exec_module(svc_mod)

security_roles_upsert_role_v1 = svc_mod.security_roles_upsert_role_v1
security_roles_add_role_member_v1 = svc_mod.security_roles_add_role_member_v1
security_roles_remove_role_member_v1 = svc_mod.security_roles_remove_role_member_v1


def test_get_roles_allows_system_admin():
  async def fake_get(request):
    rpc = RPCRequest(op="urn:security:roles:get_roles:1", payload=None, version=1)
    auth = SimpleNamespace(user_guid="u1")
    request.app.state.auth.user_roles["u1"] = 0x2000000000000000
    parts = rpc.op.split(":")
    return rpc, auth, parts

  handler_mod.get_rpcrequest_from_request = fake_get
  security_handler.get_rpcrequest_from_request = fake_get

  called = False

  async def stub(parts, request):
    nonlocal called
    called = True
    return RPCResponse(op="ok", payload=None, version=1)

  security_pkg.HANDLERS["roles"] = stub
  req = DummyRequest(DummyState(DummyDb(), DummyAuth()))
  resp = asyncio.run(handle_rpc_request(req))
  assert isinstance(resp, RPCResponse)
  assert called


def test_upsert_role_calls_db_and_loads_roles():
  async def fake_get(request):
    rpc = RPCRequest(
      op="urn:security:roles:upsert_role:1",
      payload={"name": "ROLE_NEW", "bit": 2, "display": "New"},
      version=1,
    )
    return rpc, None, None

  helpers.get_rpcrequest_from_request = fake_get
  svc_mod.get_rpcrequest_from_request = fake_get
  db = DummyDb()
  auth = DummyAuth()
  req = DummyRequest(DummyState(db, auth))
  resp = asyncio.run(security_roles_upsert_role_v1(req))
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
      op="urn:security:roles:add_role_member:1",
      payload={"role": "ROLE_X", "userGuid": "u1"},
      version=1,
    )
    return rpc, None, None

  helpers.get_rpcrequest_from_request = fake_get_add
  svc_mod.get_rpcrequest_from_request = fake_get_add
  resp = asyncio.run(security_roles_add_role_member_v1(req))
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
      op="urn:security:roles:remove_role_member:1",
      payload={"role": "ROLE_X", "userGuid": "u1"},
      version=1,
    )
    return rpc, None, None

  helpers.get_rpcrequest_from_request = fake_get_remove
  svc_mod.get_rpcrequest_from_request = fake_get_remove
  resp2 = asyncio.run(security_roles_remove_role_member_v1(req))
  assert any(op == "db:security:roles:remove_role_member:1" for op, _ in db.calls)
  assert resp2.payload["members"] == []
  assert resp2.payload["nonMembers"] == [
    {"guid": "u1", "displayName": "User 1"},
    {"guid": "u2", "displayName": "User 2"},
  ]

