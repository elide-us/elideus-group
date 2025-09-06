import asyncio
import importlib.util
import sys
import types
from pathlib import Path

root_path = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root_path))

spec_modules = importlib.util.spec_from_file_location(
  "server.modules", root_path / "server/modules/__init__.py"
)
modules_pkg = importlib.util.module_from_spec(spec_modules)
spec_modules.loader.exec_module(modules_pkg)
sys.modules["server.modules"] = modules_pkg

storage_module_pkg = types.ModuleType("server.modules.storage_module")
class StorageModule:
  def __init__(self):
    self.calls = []
  async def ensure_user_folder(self, guid):
    self.calls.append(("ensure_user_folder", guid))
storage_module_pkg.StorageModule = StorageModule

storage_cache_module_pkg = types.ModuleType("server.modules.storage_cache_module")
class StorageCacheModule:
  def __init__(self):
    self.calls = []
  async def refresh_user_cache(self, guid):
    self.calls.append(("refresh_user_cache", guid))
storage_cache_module_pkg.StorageCacheModule = StorageCacheModule

db_module_pkg = types.ModuleType("server.modules.db_module")
class DbModule:
  def __init__(self):
    self.calls = []
  async def run(self, op, payload):
    self.calls.append((op, payload))
db_module_pkg.DbModule = DbModule

modules_pkg.storage_module = storage_module_pkg
modules_pkg.storage_cache_module = storage_cache_module_pkg
modules_pkg.db_module = db_module_pkg
sys.modules["server.modules.storage_module"] = storage_module_pkg
sys.modules["server.modules.storage_cache_module"] = storage_cache_module_pkg
sys.modules["server.modules.db_module"] = db_module_pkg

spec_ua = importlib.util.spec_from_file_location(
  "server.modules.user_admin_module", root_path / "server/modules/user_admin_module.py"
)
ua_mod = importlib.util.module_from_spec(spec_ua)
spec_ua.loader.exec_module(ua_mod)
UserAdminModule = ua_mod.UserAdminModule

class DummyState:
  def __init__(self, db, storage, cache):
    self.db = db
    self.storage = storage
    self.storage_cache = cache

class DummyApp:
  def __init__(self, state):
    self.state = state

def test_enable_storage_refreshes_cache():
  db = DbModule()
  storage = StorageModule()
  cache = StorageCacheModule()
  state = DummyState(db, storage, cache)
  ua = UserAdminModule(DummyApp(state))
  ua.db = db
  ua.storage = storage
  ua.storage_cache = cache
  asyncio.run(ua.enable_storage("u1"))
  assert db.calls[0][0] == "db:support:users:enable_storage:1"
  assert ("ensure_user_folder", "u1") in storage.calls
  assert ("refresh_user_cache", "u1") in cache.calls
