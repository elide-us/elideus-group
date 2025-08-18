import asyncio
import importlib.util
import sys
import types
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

spec = importlib.util.spec_from_file_location("rpc.models", "rpc/models.py")
models = importlib.util.module_from_spec(spec)
spec.loader.exec_module(models)
RPCRequest = models.RPCRequest
RPCResponse = models.RPCResponse
sys.modules["rpc.models"] = models

helpers = types.ModuleType("rpc.helpers")
async def _stub(request):
  raise NotImplementedError
helpers.get_rpcrequest_from_request = _stub
helpers.bit_to_mask = lambda b: 1 << b
sys.modules["rpc.helpers"] = helpers


def _load_module(path, name):
  orig_server = sys.modules.get("server.modules")
  modules_pkg = types.ModuleType("server.modules")
  db_module_pkg = types.ModuleType("server.modules.db_module")
  class DbModule: ...
  db_module_pkg.DbModule = DbModule
  modules_pkg.db_module = db_module_pkg
  sys.modules["server.modules"] = modules_pkg
  sys.modules["server.modules.db_module"] = db_module_pkg
  spec = importlib.util.spec_from_file_location(name, path)
  mod = importlib.util.module_from_spec(spec)
  spec.loader.exec_module(mod)
  if orig_server is not None:
    sys.modules["server.modules"] = orig_server
  else:
    del sys.modules["server.modules"]
  del sys.modules["server.modules.db_module"]
  return mod


class DBRes:
  def __init__(self, rows=None, rowcount=0):
    self.rows = rows or []
    self.rowcount = rowcount


class DummyDb:
  def __init__(self, members=None, non_members=None, profile=None):
    self.calls = []
    self.members = members or []
    self.non_members = non_members or []
    self.profile = profile or {}

  async def run(self, op, args):
    self.calls.append((op, args))
    if op == "db:security:roles:get_role_members:1":
      return DBRes(self.members, len(self.members))
    if op == "db:security:roles:get_role_non_members:1":
      return DBRes(self.non_members, len(self.non_members))
    if op == "db:security:roles:add_role_member:1":
      guid = args.get("user_guid")
      for r in list(self.non_members):
        if r.get("guid") == guid:
          self.non_members.remove(r)
          self.members.append(r)
      return DBRes()
    if op == "db:security:roles:remove_role_member:1":
      guid = args.get("user_guid")
      for r in list(self.members):
        if r.get("guid") == guid:
          self.members.remove(r)
          self.non_members.append(r)
      return DBRes()
    if op == "db:users:profile:get_profile:1":
      return DBRes([self.profile], 1 if self.profile else 0)
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


def test_admin_roles_permission_required():
  roles_mod = _load_module("rpc/admin/roles/services.py", "admin_roles_services")

  async def fake_get(request):
    rpc = RPCRequest(op="urn:admin:roles:add_member:1", payload={"role": "ROLE_X", "userGuid": "u1"}, version=1)
    return rpc, SimpleNamespace(roles=[]), None

  orig = helpers.get_rpcrequest_from_request
  helpers.get_rpcrequest_from_request = fake_get
  roles_mod.get_rpcrequest_from_request = fake_get
  req = DummyRequest(DummyState(DummyDb()))
  with pytest.raises(HTTPException):
    asyncio.run(roles_mod.admin_roles_add_member_v1(req))
  helpers.get_rpcrequest_from_request = orig
  roles_mod.get_rpcrequest_from_request = orig


def test_admin_roles_add_and_remove_member():
  roles_mod = _load_module("rpc/admin/roles/services.py", "admin_roles_services")

  members = [{"guid": "u1", "display_name": "User 1"}]
  non_members = [{"guid": "u2", "display_name": "User 2"}]
  db = DummyDb(members, non_members)
  req = DummyRequest(DummyState(db))

  async def fake_get_add(request):
    rpc = RPCRequest(op="urn:admin:roles:add_member:1", payload={"role": "ROLE_X", "userGuid": "u2"}, version=1)
    return rpc, SimpleNamespace(roles=["ROLE_ADMIN_SUPPORT"]), None

  orig = helpers.get_rpcrequest_from_request
  helpers.get_rpcrequest_from_request = fake_get_add
  roles_mod.get_rpcrequest_from_request = fake_get_add
  resp = asyncio.run(roles_mod.admin_roles_add_member_v1(req))
  assert any(op == "db:security:roles:add_role_member:1" for op, _ in db.calls)
  assert resp.payload["members"] == [
    {"guid": "u1", "displayName": "User 1"},
    {"guid": "u2", "displayName": "User 2"},
  ]

  db.calls.clear()

  async def fake_get_remove(request):
    rpc = RPCRequest(op="urn:admin:roles:remove_member:1", payload={"role": "ROLE_X", "userGuid": "u1"}, version=1)
    return rpc, SimpleNamespace(roles=["ROLE_ADMIN_SUPPORT"]), None

  helpers.get_rpcrequest_from_request = fake_get_remove
  roles_mod.get_rpcrequest_from_request = fake_get_remove
  resp2 = asyncio.run(roles_mod.admin_roles_remove_member_v1(req))
  assert any(op == "db:security:roles:remove_role_member:1" for op, _ in db.calls)
  assert resp2.payload["nonMembers"] == [
    {"guid": "u1", "displayName": "User 1"},
    {"guid": "u2", "displayName": "User 2"},
  ]
  helpers.get_rpcrequest_from_request = orig
  roles_mod.get_rpcrequest_from_request = orig


def test_admin_users_permission_required():
  users_mod = _load_module("rpc/admin/users/services.py", "admin_users_services")

  async def fake_get(request):
    rpc = RPCRequest(op="urn:admin:users:set_credits:1", payload={"userGuid": "u1", "credits": 5}, version=1)
    return rpc, SimpleNamespace(roles=[]), None

  orig = helpers.get_rpcrequest_from_request
  helpers.get_rpcrequest_from_request = fake_get
  users_mod.get_rpcrequest_from_request = fake_get
  req = DummyRequest(DummyState(DummyDb()))
  with pytest.raises(HTTPException):
    asyncio.run(users_mod.admin_users_set_credits_v1(req))
  helpers.get_rpcrequest_from_request = orig
  users_mod.get_rpcrequest_from_request = orig


def test_admin_users_calls_db():
  users_mod = _load_module("rpc/admin/users/services.py", "admin_users_services")

  profile = {
    "guid": "u1",
    "display_name": "User 1",
    "email": "u1@example.com",
    "display_email": True,
    "credits": 10,
    "profile_image": None,
    "default_provider": "microsoft",
    "auth_providers": "[]",
  }
  db = DummyDb(profile=profile)
  req = DummyRequest(DummyState(db))

  async def fake_get_set(request):
    rpc = RPCRequest(op="urn:admin:users:set_credits:1", payload={"userGuid": "u1", "credits": 20}, version=1)
    return rpc, SimpleNamespace(roles=["ROLE_ADMIN_SUPPORT"]), None

  orig = helpers.get_rpcrequest_from_request
  helpers.get_rpcrequest_from_request = fake_get_set
  users_mod.get_rpcrequest_from_request = fake_get_set
  resp = asyncio.run(users_mod.admin_users_set_credits_v1(req))
  assert ("db:admin:users:set_credits:1", {"guid": "u1", "credits": 20}) in db.calls
  assert isinstance(resp, RPCResponse)

  db.calls.clear()

  async def fake_get_profile(request):
    rpc = RPCRequest(op="urn:admin:users:get_profile:1", payload={"userGuid": "u1"}, version=1)
    return rpc, SimpleNamespace(roles=["ROLE_ADMIN_SUPPORT"]), None

  helpers.get_rpcrequest_from_request = fake_get_profile
  users_mod.get_rpcrequest_from_request = fake_get_profile
  resp2 = asyncio.run(users_mod.admin_users_get_profile_v1(req))
  assert any(op == "db:users:profile:get_profile:1" for op, _ in db.calls)
  assert resp2.payload["guid"] == "u1"
  helpers.get_rpcrequest_from_request = orig
  users_mod.get_rpcrequest_from_request = orig

