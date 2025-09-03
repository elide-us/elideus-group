import types, sys, pathlib, asyncio, importlib

# stub rpc package and load required modules
root_path = pathlib.Path(__file__).resolve().parent.parent
rpc_pkg = types.ModuleType("rpc")
rpc_pkg.__path__ = [str(root_path / "rpc")]
rpc_pkg.HANDLERS = {}
sys.modules["rpc"] = rpc_pkg

spec_models = importlib.util.spec_from_file_location(
  "server.models", root_path / "server/models.py"
)
models_mod = importlib.util.module_from_spec(spec_models)
spec_models.loader.exec_module(models_mod)
RPCRequest = models_mod.RPCRequest
sys.modules["server.models"] = models_mod

spec_helpers = importlib.util.spec_from_file_location(
  "rpc.helpers", root_path / "rpc/helpers.py"
)
helpers = importlib.util.module_from_spec(spec_helpers)
spec_helpers.loader.exec_module(helpers)
sys.modules["rpc.helpers"] = helpers

# stub server modules
auth_module_stub = types.ModuleType("server.modules.auth_module")
class AuthModule: ...
auth_module_stub.AuthModule = AuthModule
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
  def __init__(self, db=None):
    self.db = db
    self.upsert_args = None
    self.delete_args = None
    self.loaded = False

  async def refresh_role_cache(self):
    self.loaded = True

  async def upsert_role(self, name, mask, display):
    self.upsert_args = (name, mask, display)
    if self.db:
      await self.db.run(
        "db:security:roles:upsert_role:1",
        {"name": name, "mask": mask, "display": display},
      )
    await self.refresh_role_cache()

  async def delete_role(self, name):
    self.delete_args = name
    if self.db:
      await self.db.run("db:security:roles:delete_role:1", {"name": name})
    await self.refresh_role_cache()


class DummyRoleAdmin:
  def __init__(self, db, auth):
    self.db = db
    self.auth = auth

  async def list_roles(self):
    res = await self.db.run("db:system:roles:list:1", {})
    return [
      {
        "name": r.get("name", ""),
        "mask": str(r.get("mask", "")),
        "display": r.get("display"),
      }
      for r in res.rows
      if r.get("name") != "ROLE_REGISTERED"
    ]

  async def get_role_members(self, role):
    mem_res = await self.db.run("db:security:roles:get_role_members:1", {"role": role})
    non_res = await self.db.run("db:security:roles:get_role_non_members:1", {"role": role})
    members = [
      {"guid": r.get("guid", ""), "displayName": r.get("display_name", "")}
      for r in mem_res.rows
    ]
    non = [
      {"guid": r.get("guid", ""), "displayName": r.get("display_name", "")}
      for r in non_res.rows
    ]
    return members, non

  async def add_role_member(self, role, user_guid):
    await self.db.run(
      "db:security:roles:add_role_member:1",
      {"role": role, "user_guid": user_guid},
    )
    return await self.get_role_members(role)

  async def remove_role_member(self, role, user_guid):
    await self.db.run(
      "db:security:roles:remove_role_member:1",
      {"role": role, "user_guid": user_guid},
    )
    return await self.get_role_members(role)

  async def upsert_role(self, name, mask, display):
    await self.auth.upsert_role(name, mask, display)

  async def delete_role(self, name):
    await self.auth.delete_role(name)

class DummyState:
  def __init__(self, db, auth=None):
    self.db = db
    self.auth = auth or DummyAuth(db)
    self.role_admin = DummyRoleAdmin(self.db, self.auth)

class DummyApp:
  def __init__(self, state):
    self.state = state

class DummyRequest:
  def __init__(self, state):
    self.app = DummyApp(state)
    self.headers = {}

sys.path.insert(0, str(root_path))
svc_mod = importlib.import_module("rpc.account.role.services")

account_role_get_role_members_v1 = svc_mod.account_role_get_role_members_v1
account_role_add_role_member_v1 = svc_mod.account_role_add_role_member_v1
account_role_remove_role_member_v1 = svc_mod.account_role_remove_role_member_v1
account_role_upsert_role_v1 = svc_mod.account_role_upsert_role_v1
account_role_delete_role_v1 = svc_mod.account_role_delete_role_v1


def test_add_and_remove_member():
  members = [{"guid": "u1", "display_name": "User 1"}]
  non_members = [{"guid": "u2", "display_name": "User 2"}]
  db = DummyDb(members, non_members)
  state = DummyState(db)
  req = DummyRequest(state)

  async def fake_get_add(request):
    rpc = RPCRequest(
      op="urn:account:role:add_role_member:1",
      payload={"role": "ROLE_X", "userGuid": "u1"},
      version=1,
    )
    return rpc, None, None

  helpers.unbox_request = fake_get_add
  svc_mod.unbox_request = fake_get_add
  resp = asyncio.run(account_role_add_role_member_v1(req))
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
      op="urn:account:role:remove_role_member:1",
      payload={"role": "ROLE_X", "userGuid": "u1"},
      version=1,
    )
    return rpc, None, None

  helpers.unbox_request = fake_get_remove
  svc_mod.unbox_request = fake_get_remove
  resp2 = asyncio.run(account_role_remove_role_member_v1(req))
  assert any(op == "db:security:roles:remove_role_member:1" for op, _ in db.calls)
  assert resp2.payload["members"] == []
  assert resp2.payload["nonMembers"] == [
    {"guid": "u1", "displayName": "User 1"},
    {"guid": "u2", "displayName": "User 2"},
  ]


def test_upsert_and_delete_role():
  db = DummyDb()
  auth = DummyAuth(db)
  state = DummyState(db, auth)
  req = DummyRequest(state)

  async def fake_upsert(request):
    rpc = RPCRequest(
      op="urn:account:role:upsert_role:1",
      payload={"name": "ROLE_NEW", "mask": "8", "display": "New"},
      version=1,
    )
    return rpc, None, None

  helpers.unbox_request = fake_upsert
  svc_mod.unbox_request = fake_upsert
  resp = asyncio.run(account_role_upsert_role_v1(req))
  assert auth.upsert_args == ("ROLE_NEW", 8, "New")
  assert (
    "db:security:roles:upsert_role:1",
    {"name": "ROLE_NEW", "mask": 8, "display": "New"},
  ) in db.calls
  assert isinstance(resp, models_mod.RPCResponse)

  db.calls.clear()

  async def fake_delete(request):
    rpc = RPCRequest(
      op="urn:account:role:delete_role:1",
      payload={"name": "ROLE_NEW"},
      version=1,
    )
    return rpc, None, None

  helpers.unbox_request = fake_delete
  svc_mod.unbox_request = fake_delete
  resp2 = asyncio.run(account_role_delete_role_v1(req))
  assert auth.delete_args == "ROLE_NEW"
  assert ("db:security:roles:delete_role:1", {"name": "ROLE_NEW"}) in db.calls
  assert isinstance(resp2, models_mod.RPCResponse)
