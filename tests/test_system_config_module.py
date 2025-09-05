import asyncio
import importlib.util
import pathlib
import sys
import types
from types import SimpleNamespace
import pytest
from fastapi import FastAPI

root = pathlib.Path(__file__).resolve().parent.parent

# stub rpc package to avoid side effects
pkg = types.ModuleType('rpc')
pkg.__path__ = [str(root / 'rpc')]
sys.modules.setdefault('rpc', pkg)

rpc_system_pkg = types.ModuleType('rpc.system')
rpc_system_pkg.__path__ = [str(root / 'rpc/system')]
sys.modules.setdefault('rpc.system', rpc_system_pkg)

rpc_system_config_pkg = types.ModuleType('rpc.system.config')
rpc_system_config_pkg.__path__ = [str(root / 'rpc/system/config')]
sys.modules.setdefault('rpc.system.config', rpc_system_config_pkg)

# stub server package
server_pkg = types.ModuleType('server')
server_pkg.__path__ = [str(root / 'server')]
sys.modules['server'] = server_pkg

modules_pkg = types.ModuleType('server.modules')
modules_pkg.__path__ = [str(root / 'server/modules')]
class BaseModule:
  def __init__(self, app):
    self.app = app
  async def startup(self):
    pass
  async def shutdown(self):
    pass
  def mark_ready(self):
    pass
  async def on_ready(self):
    pass
modules_pkg.BaseModule = BaseModule
sys.modules['server.modules'] = modules_pkg

db_module_pkg = types.ModuleType('server.modules.db_module')
class DbModule:
  async def run(self, op: str, args: dict):
    raise NotImplementedError

db_module_pkg.DbModule = DbModule
sys.modules['server.modules.db_module'] = db_module_pkg

spec = importlib.util.spec_from_file_location(
  'server.modules.system_config_module',
  root / 'server/modules/system_config_module.py',
)
mod = importlib.util.module_from_spec(spec)
sys.modules['server.modules.system_config_module'] = mod
spec.loader.exec_module(mod)
SystemConfigModule = mod.SystemConfigModule

class DummyDb(DbModule):
  def __init__(self):
    self.calls = []
  async def on_ready(self):
    pass
  async def run(self, op: str, args: dict):
    self.calls.append((op, args))
    if op == 'urn:system:config:get_configs:1':
      rows = [{'element_key': 'LoggingLevel', 'element_value': '4'}]
      return SimpleNamespace(rows=rows, rowcount=1)
    if op == 'urn:system:config:upsert_config:1':
      return SimpleNamespace(rows=[], rowcount=1)
    if op == 'urn:system:config:delete_config:1':
      return SimpleNamespace(rows=[], rowcount=1)
    raise AssertionError(f'unexpected op {op}')

app = FastAPI()
db = DummyDb()
app.state.db = db
module = SystemConfigModule(app)
asyncio.run(module.startup())

def test_get_configs_module():
  payload = asyncio.run(module.get_configs('u1', []))
  assert payload.items[0].key == 'LoggingLevel'
  assert ('urn:system:config:get_configs:1', {}) in db.calls

def test_upsert_and_delete_module():
  asyncio.run(module.upsert_config('u1', [], 'LoggingLevel', '2'))
  asyncio.run(module.delete_config('u1', [], 'LoggingLevel'))
  assert (
    'urn:system:config:upsert_config:1',
    {'key': 'LoggingLevel', 'value': '2'}
  ) in db.calls
  assert (
    'urn:system:config:delete_config:1',
    {'key': 'LoggingLevel'}
  ) in db.calls
