import asyncio
from types import SimpleNamespace

import pytest

from server.registry.types import DBRequest
from server.modules.service_routes_module import ServiceRoutesModule


class DummyDb:
  def __init__(self, rows=None):
    self.rows = rows or []
    self.calls: list[tuple[str, dict[str, object]]] = []

  async def on_ready(self):
    pass

  async def run(self, request: DBRequest):
    assert isinstance(request, DBRequest)
    self.calls.append((request.op, request.params))
    if request.op == 'db:system:routes:get_routes:1':
      return SimpleNamespace(rows=self.rows, rowcount=len(self.rows))
    return SimpleNamespace(rows=[], rowcount=1)


class DummyAuth:
  def __init__(self, roles=None):
    self.roles = roles or {'ROLE_SERVICE_ADMIN': 1}

  async def on_ready(self):
    pass

  def mask_to_names(self, mask: int) -> list[str]:
    return [name for name, bit in self.roles.items() if mask & bit]

  def names_to_mask(self, names: list[str]) -> int:
    mask = 0
    for name in names:
      mask |= self.roles[name]
    return mask


async def make_module(rows=None, roles=None):
  db = DummyDb(rows)
  auth = DummyAuth(roles)
  app_state = SimpleNamespace(db=db, auth=auth)
  app = SimpleNamespace(state=app_state)
  mod = ServiceRoutesModule(app)
  await mod.startup()
  return mod, db, auth


def test_list_routes_translates_role_masks():
  rows = [{
    'element_path': '/admin',
    'element_name': 'Admin',
    'element_icon': 'shield',
    'element_sequence': 10,
    'element_roles': 3,
  }]
  roles = {'ROLE_SERVICE_ADMIN': 1, 'ROLE_EDITOR': 2}
  mod, db, _ = asyncio.run(make_module(rows, roles))
  routes = asyncio.run(mod.list_routes())
  assert routes == [{
    'path': '/admin',
    'name': 'Admin',
    'icon': 'shield',
    'sequence': 10,
    'required_roles': ['ROLE_SERVICE_ADMIN', 'ROLE_EDITOR'],
  }]
  assert db.calls == [('db:system:routes:get_routes:1', {})]


def test_upsert_route_converts_role_names():
  roles = {'ROLE_SERVICE_ADMIN': 1, 'ROLE_EDITOR': 2}
  mod, db, _ = asyncio.run(make_module([], roles))
  result = asyncio.run(mod.upsert_route(
    path='/admin',
    name='Admin',
    icon='shield',
    sequence=5,
    required_roles=['ROLE_SERVICE_ADMIN'],
  ))
  assert result == {
    'path': '/admin',
    'name': 'Admin',
    'icon': 'shield',
    'sequence': 5,
    'required_roles': ['ROLE_SERVICE_ADMIN'],
  }
  assert db.calls == [(
    'db:system:routes:upsert_route:1',
    {
      'path': '/admin',
      'name': 'Admin',
      'icon': 'shield',
      'sequence': 5,
      'roles': 1,
    },
  )]


def test_upsert_route_invalid_role_raises_key_error():
  roles = {'ROLE_SERVICE_ADMIN': 1}
  mod, _, _ = asyncio.run(make_module([], roles))
  with pytest.raises(KeyError):
    asyncio.run(mod.upsert_route(
      path='/admin',
      name='Admin',
      icon=None,
      sequence=1,
      required_roles=['ROLE_UNKNOWN'],
    ))


def test_delete_route_calls_db():
  mod, db, _ = asyncio.run(make_module([], {'ROLE_SERVICE_ADMIN': 1}))
  result = asyncio.run(mod.delete_route('/admin'))
  assert result == {'path': '/admin'}
  assert db.calls == [('db:system:routes:delete_route:1', {'path': '/admin'})]
