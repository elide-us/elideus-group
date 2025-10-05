import asyncio
import importlib.util
import pathlib
import types
from types import SimpleNamespace
import sys

import pytest
from server.registry.types import DBRequest

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
RPCResponse = models_mod.RPCResponse
sys.modules["server.models"] = models_mod

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

  async def run(self, request: DBRequest):
    self.calls.append(request)
    op = request.op
    if op == "db:system:roles:get_role_members:1":
      return DBRes(self.members, len(self.members))
    if op == "db:system:roles:get_role_non_members:1":
      return DBRes(self.non_members, len(self.non_members))
    if op == "db:system:roles:list:1":
      return DBRes([], 0)
    return DBRes()


class RoleCache:
  def __init__(self, db=None):
    self.db = db
    self.loaded = False
    self.roles = {
      "ROLE_ACCOUNT_ADMIN": 1,
      "ROLE_SYSTEM_ADMIN": 2,
      "ROLE_SERVICE_ADMIN": 0x4000000000000000,
    }
    self.user_roles: dict[str, int] = {}
    self.upsert_args = None
    self.delete_args = None

  async def refresh_role_cache(self):
    self.loaded = True

  async def upsert_role(self, name, mask, display):
    self.upsert_args = (name, mask, display)
    if self.db:
      await self.db.run(
        DBRequest(
          op="db:system:roles:upsert_role:1",
          params={"name": name, "mask": mask, "display": display},
        )
      )
    await self.refresh_role_cache()

  async def delete_role(self, name):
    self.delete_args = name
    if self.db:
      await self.db.run(DBRequest(op="db:system:roles:delete_role:1", params={"name": name}))
    await self.refresh_role_cache()

  def get_role_names(self, exclude_registered=False):
    return ["ROLE_ACCOUNT_ADMIN"]

  def names_to_mask(self, names):
    mask = 0
    missing = [n for n in names if n not in self.roles]
    if missing:
      raise KeyError(f"Undefined roles: {', '.join(missing)}")
    for n in names:
      mask |= self.roles[n]
    return mask

  def require_role_mask(self, name):
    if name not in self.roles:
      raise KeyError(f"Role {name} is not defined")
    return self.roles[name]

  async def user_has_role(self, guid: str, mask: int) -> bool:
    return bool(self.user_roles.get(guid, 0) & mask)

class DummyAuth:
  def __init__(self, db=None):
    self.role_cache = RoleCache(db)
    self.db = db

  @property
  def roles(self):
    return self.role_cache.roles

  async def refresh_role_cache(self):
    await self.role_cache.refresh_role_cache()

  async def upsert_role(self, name, mask, display):
    await self.role_cache.upsert_role(name, mask, display)

  async def delete_role(self, name):
    await self.role_cache.delete_role(name)

  def get_role_names(self, exclude_registered=False):
    return self.role_cache.get_role_names(exclude_registered)

  def names_to_mask(self, names):
    return self.role_cache.names_to_mask(names)

  def require_role_mask(self, name):
    return self.role_cache.require_role_mask(name)

  async def user_has_role(self, guid: str, mask: int) -> bool:
    return await self.role_cache.user_has_role(guid, mask)


class DummyRoleAdmin:
  def __init__(self, db, auth):
    self.db = db
    self.auth = auth

  async def list_roles(self):
    res = await self.db.run(DBRequest(op="db:system:roles:list:1", params={}))
    return [
      {
        "name": r.get("name", ""),
        "mask": str(r.get("mask", "")),
        "display": r.get("display"),
      }
      for r in res.rows
      if r.get("name") != "ROLE_REGISTERED"
    ]

  async def upsert_role(self, name, mask, display):
    await self.auth.role_cache.upsert_role(name, mask, display)

  async def delete_role(self, name):
    await self.auth.role_cache.delete_role(name)


class DummyState:
  def __init__(self, db, auth):
    self.db = db
    self.auth = auth
    self.role_admin = DummyRoleAdmin(db, auth)
    self.services = SimpleNamespace(auth=auth, role_admin=self.role_admin)


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


def test_get_roles_allows_system_admin():
  async def fake_get(request):
    rpc = RPCRequest(op="urn:service:roles:get_roles:1", payload=None, version=1)
    auth = SimpleNamespace(user_guid="u1")
    request.app.state.auth.role_cache.user_roles["u1"] = 0x4000000000000000
    parts = rpc.op.split(":")
    return rpc, auth, parts

  handler_mod.unbox_request = fake_get
  service_handler.unbox_request = fake_get

  called = False

  async def stub(parts, request):
    nonlocal called
    called = True
    return RPCResponse(op="urn:service:roles:get_roles:1", payload=None, version=1)

  service_pkg.HANDLERS["roles"] = stub
  req = DummyRequest(DummyState(DummyDb(), DummyAuth()))
  resp = asyncio.run(handle_rpc_request(req))
  assert isinstance(resp, RPCResponse)
  assert called


def test_upsert_role_calls_db_and_loads_roles():
  async def fake_get(request):
    rpc = RPCRequest(
      op="urn:service:roles:upsert_role:1",
      payload={"name": "ROLE_NEW", "mask": "4", "display": "New"},
      version=1,
    )
    return rpc, None, None

  helpers.unbox_request = fake_get
  svc_mod.unbox_request = fake_get
  db = DummyDb()
  auth = DummyAuth(db)
  req = DummyRequest(DummyState(db, auth))
  resp = asyncio.run(service_roles_upsert_role_v1(req))
  assert isinstance(resp, RPCResponse)
  assert auth.role_cache.upsert_args == ("ROLE_NEW", 4, "New")
  assert any(
    c.op == "db:system:roles:upsert_role:1"
    and c.params == {"name": "ROLE_NEW", "mask": 4, "display": "New"}
    for c in db.calls
  )
  assert auth.role_cache.loaded


def test_delete_role_calls_db_and_loads_roles():
  async def fake_get(request):
    rpc = RPCRequest(
      op="urn:service:roles:delete_role:1",
      payload={"name": "ROLE_OLD"},
      version=1,
    )
    return rpc, None, None

  helpers.unbox_request = fake_get
  svc_mod.unbox_request = fake_get
  db = DummyDb()
  auth = DummyAuth(db)
  req = DummyRequest(DummyState(db, auth))
  resp = asyncio.run(svc_mod.service_roles_delete_role_v1(req))
  assert isinstance(resp, RPCResponse)
  assert auth.role_cache.delete_args == "ROLE_OLD"
  assert any(
    c.op == "db:system:roles:delete_role:1" and c.params == {"name": "ROLE_OLD"}
    for c in db.calls
  )
  assert auth.role_cache.loaded


