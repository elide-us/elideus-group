import types, asyncio
from fastapi import HTTPException

from server.modules.role_admin_module import RoleAdminModule


class DummyDb:
  def __init__(self, roles=None):
    self.roles = roles or []
  async def on_ready(self):
    pass
  async def run(self, op, args):
    if op == "db:system:roles:list:1":
      return types.SimpleNamespace(rows=self.roles)
    return types.SimpleNamespace(rows=[])

class RoleCache:
  def __init__(self, roles=None):
    self.roles = roles or {}
  async def refresh_user_roles(self, guid):
    pass
  async def upsert_role(self, name, mask, display):
    self.roles[name] = mask
  async def delete_role(self, name):
    self.roles.pop(name, None)

class DummyAuth:
  def __init__(self, roles=None):
    self.role_cache = RoleCache(roles)
  async def on_ready(self):
    pass
  @property
  def roles(self):
    return self.role_cache.roles
  async def refresh_user_roles(self, guid):
    await self.role_cache.refresh_user_roles(guid)
  async def upsert_role(self, name, mask, display):
    await self.role_cache.upsert_role(name, mask, display)
  async def delete_role(self, name):
    await self.role_cache.delete_role(name)

async def make_module(roles, auth_roles):
  db = DummyDb(roles)
  auth = DummyAuth(auth_roles)
  app = types.SimpleNamespace(state=types.SimpleNamespace(db=db, auth=auth))
  mod = RoleAdminModule(app)
  await mod.startup()
  return mod

def test_list_roles_filters_and_sorts():
  roles = [
    {"name": "ROLE_B", "mask": 4, "display": None},
    {"name": "ROLE_REGISTERED", "mask": 1, "display": None},
    {"name": "ROLE_A", "mask": 2, "display": None},
  ]
  mod = asyncio.run(make_module(roles, {}))
  res = asyncio.run(mod.list_roles(4))
  assert [r["name"] for r in res] == ["ROLE_A", "ROLE_B"]

def test_permission_check_blocks_higher_mask():
  mod = asyncio.run(make_module([], {}))
  try:
    asyncio.run(mod.upsert_role("ROLE_X", 8, None, 4))
    assert False, "expected forbidden"
  except HTTPException as e:
    assert e.status_code == 403
