import types, sys, pathlib
from types import SimpleNamespace
from fastapi import FastAPI
from fastapi.testclient import TestClient
from starlette.requests import Request

# Stub rpc package
pkg = types.ModuleType('rpc')
pkg.__path__ = [str(pathlib.Path(__file__).resolve().parent.parent / 'rpc')]
sys.modules.setdefault('rpc', pkg)

rpc_system_pkg = types.ModuleType('rpc.system')
rpc_system_pkg.__path__ = [str(pathlib.Path(__file__).resolve().parent.parent / 'rpc/system')]
sys.modules.setdefault('rpc.system', rpc_system_pkg)

rpc_system_roles_pkg = types.ModuleType('rpc.system.roles')
rpc_system_roles_pkg.__path__ = [str(pathlib.Path(__file__).resolve().parent.parent / 'rpc/system/roles')]
sys.modules.setdefault('rpc.system.roles', rpc_system_roles_pkg)

# Stub server modules
server_pkg = types.ModuleType('server')
modules_pkg = types.ModuleType('server.modules')
db_module_pkg = types.ModuleType('server.modules.db_module')
auth_module_pkg = types.ModuleType('server.modules.auth_module')
models_pkg = types.ModuleType('server.models')

class DbModule:
  pass

db_module_pkg.DbModule = DbModule
modules_pkg.db_module = db_module_pkg

class AuthModule:
  def __init__(self, db=None):
    self.db = db
    self.refreshed = False
    self.upsert_args = None
    self.delete_args = None

  async def refresh_role_cache(self):
    self.refreshed = True

  async def upsert_role(self, name, mask, display):
    self.upsert_args = (name, mask, display)
    if self.db:
      await self.db.run('db:security:roles:upsert_role:1', {'name': name, 'mask': mask, 'display': display})
    await self.refresh_role_cache()

  async def delete_role(self, name):
    self.delete_args = name
    if self.db:
      await self.db.run('db:security:roles:delete_role:1', {'name': name})
    await self.refresh_role_cache()

auth_module_pkg.AuthModule = AuthModule
modules_pkg.auth_module = auth_module_pkg

class AuthContext:
  def __init__(self, **data):
    self.role_mask = 0
    self.__dict__.update(data)

models_pkg.AuthContext = AuthContext
server_pkg.modules = modules_pkg
server_pkg.models = models_pkg

sys.modules.setdefault('server', server_pkg)
sys.modules.setdefault('server.modules', modules_pkg)
sys.modules.setdefault('server.modules.db_module', db_module_pkg)
sys.modules.setdefault('server.modules.auth_module', auth_module_pkg)
sys.modules.setdefault('server.models', models_pkg)

import importlib.util

svc_spec = importlib.util.spec_from_file_location(
  'rpc.system.roles.services',
  pathlib.Path(__file__).resolve().parent.parent / 'rpc/system/roles/services.py',
)
svc = importlib.util.module_from_spec(svc_spec)
sys.modules['rpc.system.roles.services'] = svc
svc_spec.loader.exec_module(svc)

system_roles_get_roles_v1 = svc.system_roles_get_roles_v1
system_roles_upsert_role_v1 = svc.system_roles_upsert_role_v1
system_roles_delete_role_v1 = svc.system_roles_delete_role_v1

async def fake_unbox(request: Request):
  body = await request.json()
  op = body.get('op')
  payload = body.get('payload')
  rpc_req = SimpleNamespace(op=op, payload=payload, version=1)
  auth_ctx = SimpleNamespace(user_guid='u1', roles=[])
  return rpc_req, auth_ctx, None

svc.unbox_request = fake_unbox

class DummyDb:
  def __init__(self):
    self.calls = []
  async def run(self, op: str, args: dict):
    self.calls.append((op, args))
    if op == 'db:system:roles:list:1':
      rows = [{'name': 'ROLE_FOO', 'mask': 1, 'display': 'Foo'}]
      return SimpleNamespace(rows=rows, rowcount=1)
    if op == 'db:security:roles:upsert_role:1':
      return SimpleNamespace(rows=[], rowcount=1)
    if op == 'db:security:roles:delete_role:1':
      return SimpleNamespace(rows=[], rowcount=1)
    raise AssertionError(f'unexpected op {op}')

db = DummyDb()
auth = AuthModule(db)
class DummyRoleAdmin:
  def __init__(self, db, auth):
    self.db = db
    self.auth = auth

  async def list_roles(self):
    res = await self.db.run('db:system:roles:list:1', {})
    return [
      {
        'name': r.get('name', ''),
        'mask': str(r.get('mask', '')),
        'display': r.get('display'),
      }
      for r in res.rows
      if r.get('name') != 'ROLE_REGISTERED'
    ]

  async def upsert_role(self, name, mask, display):
    await self.auth.upsert_role(name, mask, display)

  async def delete_role(self, name):
    await self.auth.delete_role(name)
app = FastAPI()
app.state.db = db
app.state.auth = auth
app.state.role_admin = DummyRoleAdmin(db, auth)

@app.post('/rpc')
async def rpc_endpoint(request: Request):
  body = await request.json()
  op = body['op']
  if op == 'urn:system:roles:get_roles:1':
    return await system_roles_get_roles_v1(request)
  if op == 'urn:system:roles:upsert_role:1':
    return await system_roles_upsert_role_v1(request)
  if op == 'urn:system:roles:delete_role:1':
    return await system_roles_delete_role_v1(request)
  raise AssertionError('unexpected op')

client = TestClient(app)

def test_get_roles_service():
  resp = client.post('/rpc', json={'op': 'urn:system:roles:get_roles:1'})
  assert resp.status_code == 200
  data = resp.json()
  assert data['payload'] == {
    'roles': [{'name': 'ROLE_FOO', 'mask': '1', 'display': 'Foo'}]
  }
  assert ('db:system:roles:list:1', {}) in db.calls

def test_upsert_and_delete_role_service():
  resp = client.post('/rpc', json={'op': 'urn:system:roles:upsert_role:1', 'payload': {'name': 'ROLE_FOO', 'mask': '1', 'display': 'Foo'}})
  assert resp.status_code == 200
  resp = client.post('/rpc', json={'op': 'urn:system:roles:delete_role:1', 'payload': {'name': 'ROLE_FOO'}})
  assert resp.status_code == 200
  assert ('db:security:roles:upsert_role:1', {'name': 'ROLE_FOO', 'mask': 1, 'display': 'Foo'}) in db.calls
  assert ('db:security:roles:delete_role:1', {'name': 'ROLE_FOO'}) in db.calls
  assert getattr(auth, 'refreshed', False)
