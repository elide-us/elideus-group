import asyncio
import importlib
import pathlib
import sys
import types

import pytest
from fastapi import HTTPException

root_path = pathlib.Path(__file__).resolve().parent.parent

rpc_pkg = types.ModuleType("rpc")
rpc_pkg.__path__ = [str(root_path / "rpc")]
rpc_pkg.HANDLERS = {}
sys.modules["rpc"] = rpc_pkg

role_admin_stub = types.ModuleType("server.modules.role_admin_module")


class RoleAdminModule:
  def __init__(self):
    self.roles = {}
    self.members = []
    self.non_members = []
    self.add_calls = []
    self.remove_calls = []

  def _max_mask(self, mask: int) -> int:
    if mask == 0:
      return 0
    return 1 << (mask.bit_length() - 1)

  def _ensure_can_manage(self, actor_mask: int, target_mask: int) -> None:
    if target_mask > self._max_mask(actor_mask):
      raise HTTPException(status_code=403, detail="Forbidden")

  async def add_role_member(self, role, user_guid, actor_mask=None):
    if actor_mask is not None:
      role_mask = self.roles.get(role, 0)
      self._ensure_can_manage(actor_mask, role_mask)
    self.add_calls.append((role, user_guid, actor_mask))
    return self.members, self.non_members

  async def remove_role_member(self, role, user_guid, actor_mask=None):
    if actor_mask is not None:
      role_mask = self.roles.get(role, 0)
      self._ensure_can_manage(actor_mask, role_mask)
    self.remove_calls.append((role, user_guid, actor_mask))
    return self.members, self.non_members


role_admin_stub.RoleAdminModule = RoleAdminModule
sys.modules["server.modules.role_admin_module"] = role_admin_stub

sys.path.insert(0, str(root_path))
models_mod = importlib.import_module("server.models")
helpers = importlib.import_module("rpc.helpers")
svc_mod = importlib.import_module("rpc.support.roles.services")

RPCRequest = models_mod.RPCRequest
AuthContext = models_mod.AuthContext
RPCResponse = svc_mod.RPCResponse


class DummyApp:
  def __init__(self, role_admin):
    self.state = types.SimpleNamespace(role_admin=role_admin)


class DummyRequest:
  def __init__(self, role_admin):
    self.app = DummyApp(role_admin)
    self.headers = {}


def test_support_roles_add_member_passes_actor_mask():
  role_admin = RoleAdminModule()
  role_admin.roles = {"ROLE_LOW": 4}
  role_admin.members = [{"guid": "u1", "displayName": "User 1"}]
  role_admin.non_members = [{"guid": "u2", "displayName": "User 2"}]
  req = DummyRequest(role_admin)

  async def fake_unbox(request):
    rpc = RPCRequest(
      op="urn:support:roles:add_member:1",
      payload={"role": "ROLE_LOW", "userGuid": "u1"},
      version=1,
    )
    auth_ctx = AuthContext(role_mask=4)
    return rpc, auth_ctx, None

  helpers.unbox_request = fake_unbox
  svc_mod.unbox_request = fake_unbox

  resp = asyncio.run(svc_mod.support_roles_add_member_v1(req))

  assert role_admin.add_calls == [("ROLE_LOW", "u1", 4)]
  assert resp.payload["members"] == [{"guid": "u1", "displayName": "User 1"}]
  assert resp.payload["nonMembers"] == [{"guid": "u2", "displayName": "User 2"}]
  assert isinstance(resp, RPCResponse)


def test_support_roles_remove_member_passes_actor_mask():
  role_admin = RoleAdminModule()
  role_admin.roles = {"ROLE_LOW": 4}
  role_admin.members = []
  role_admin.non_members = [{"guid": "u2", "displayName": "User 2"}]
  req = DummyRequest(role_admin)

  async def fake_unbox(request):
    rpc = RPCRequest(
      op="urn:support:roles:remove_member:1",
      payload={"role": "ROLE_LOW", "userGuid": "u2"},
      version=1,
    )
    auth_ctx = AuthContext(role_mask=4)
    return rpc, auth_ctx, None

  helpers.unbox_request = fake_unbox
  svc_mod.unbox_request = fake_unbox

  resp = asyncio.run(svc_mod.support_roles_remove_member_v1(req))

  assert role_admin.remove_calls == [("ROLE_LOW", "u2", 4)]
  assert resp.payload["members"] == []
  assert resp.payload["nonMembers"] == [{"guid": "u2", "displayName": "User 2"}]
  assert isinstance(resp, RPCResponse)


def test_support_roles_cannot_manage_above_mask():
  role_admin = RoleAdminModule()
  role_admin.roles = {"ROLE_HIGH": 8}
  req = DummyRequest(role_admin)

  async def fake_unbox(request):
    rpc = RPCRequest(
      op="urn:support:roles:add_member:1",
      payload={"role": "ROLE_HIGH", "userGuid": "u3"},
      version=1,
    )
    auth_ctx = AuthContext(role_mask=4)
    return rpc, auth_ctx, None

  helpers.unbox_request = fake_unbox
  svc_mod.unbox_request = fake_unbox

  with pytest.raises(HTTPException) as exc:
    asyncio.run(svc_mod.support_roles_add_member_v1(req))

  assert exc.value.status_code == 403
  assert role_admin.add_calls == []
