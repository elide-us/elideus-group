import asyncio
import importlib.util
import pathlib
import sys
import types
from types import SimpleNamespace

# stub rpc package
root_path = pathlib.Path(__file__).resolve().parent.parent
pkg = types.ModuleType("rpc")
pkg.__path__ = [str(root_path / "rpc")]
sys.modules["rpc"] = pkg

# ensure nested rpc packages exist for relative imports
storage_pkg = types.ModuleType("rpc.storage")
storage_pkg.__path__ = [str(root_path / "rpc" / "storage")]
sys.modules["rpc.storage"] = storage_pkg

files_pkg = types.ModuleType("rpc.storage.files")
files_pkg.__path__ = [str(root_path / "rpc" / "storage" / "files")]
sys.modules["rpc.storage.files"] = files_pkg

spec = importlib.util.spec_from_file_location("server.models", "server/models.py")
models = importlib.util.module_from_spec(spec)
spec.loader.exec_module(models)
RPCRequest = models.RPCRequest
RPCResponse = models.RPCResponse
sys.modules["server.models"] = models

# stub server packages for storage module
server_pkg = types.ModuleType("server")
modules_pkg = types.ModuleType("server.modules")
storage_module_pkg = types.ModuleType("server.modules.storage_module")
storage_cache_module_pkg = types.ModuleType("server.modules.storage_cache_module")

class StorageModule:
  def __init__(self):
    self.files = []
    self.uploads = []
    self.deleted = []
    self.validated = []
    self.created = []
    self.moved = []
  async def list_user_files(self, user_guid):
    return self.files
  async def upload_files(self, user_guid, files):
    for item in files:
      name = getattr(item, "name", None) or item.get("name")
      ct = getattr(item, "content_type", None) or item.get("content_type")
      b64 = getattr(item, "content_b64", None) or item.get("content_b64")
      self.uploads.append((user_guid, name, ct, b64))
  async def delete_files(self, user_guid, files):
    for name in files:
      self.deleted.append((user_guid, name))
  async def ensure_user_file(self, user_guid, name):
    self.validated.append((user_guid, name))
    if not any(f.get("name") == name for f in self.files):
      raise FileNotFoundError(name)
  async def create_folder(self, user_guid, path):
    self.created.append((user_guid, path))
  async def move_file(self, user_guid, src, dst):
    self.moved.append((user_guid, src, dst))

storage_module_pkg.StorageModule = StorageModule
modules_pkg.storage_module = storage_module_pkg
class StorageCacheModule:
  def __init__(self, storage):
    self.storage = storage
    self.cache = []
  async def list_user_files(self, user_guid):
    return self.cache
  async def refresh_user_cache(self, user_guid):
    self.cache = self.storage.files
    return self.cache
storage_cache_module_pkg.StorageCacheModule = StorageCacheModule
modules_pkg.storage_cache_module = storage_cache_module_pkg
server_pkg.modules = modules_pkg
models_pkg = types.ModuleType("server.models")
class AuthContext:
  def __init__(self, **data):
    self.role_mask = 0
    self.__dict__.update(data)
models_pkg.AuthContext = AuthContext
server_pkg.models = models_pkg

sys.modules.setdefault("server", server_pkg)
sys.modules.setdefault("server.modules", modules_pkg)
sys.modules.setdefault("server.modules.storage_module", storage_module_pkg)
sys.modules.setdefault("server.modules.storage_cache_module", storage_cache_module_pkg)
sys.modules.setdefault("server.models", models_pkg)

# load real helpers then override for service import
real_helpers_spec = importlib.util.spec_from_file_location("rpc.helpers", "rpc/helpers.py")
real_helpers = importlib.util.module_from_spec(real_helpers_spec)
real_helpers_spec.loader.exec_module(real_helpers)

helpers_stub = types.ModuleType("rpc.helpers")
async def _stub(request):
  raise NotImplementedError
helpers_stub.unbox_request = _stub
sys.modules["rpc.helpers"] = helpers_stub

# import services with stubbed helpers
svc_spec = importlib.util.spec_from_file_location(
  "rpc.storage.files.services", "rpc/storage/files/services.py"
)
svc_mod = importlib.util.module_from_spec(svc_spec)
sys.modules["rpc.storage.files.services"] = svc_mod
svc_spec.loader.exec_module(svc_mod)

# restore real helpers for other tests
sys.modules["rpc.helpers"] = real_helpers

storage_files_get_files_v1 = svc_mod.storage_files_get_files_v1
storage_files_upload_files_v1 = svc_mod.storage_files_upload_files_v1
storage_files_delete_files_v1 = svc_mod.storage_files_delete_files_v1
storage_files_set_gallery_v1 = svc_mod.storage_files_set_gallery_v1
storage_files_create_folder_v1 = svc_mod.storage_files_create_folder_v1
storage_files_move_file_v1 = svc_mod.storage_files_move_file_v1
storage_files_refresh_cache_v1 = svc_mod.storage_files_refresh_cache_v1

class DummyAuth:
  def __init__(self):
    self.roles = {"ROLE_STORAGE": 0x2}


class DummyState:
  def __init__(self, storage, cache):
    self.storage = storage
    self.storage_cache = cache
    self.auth = DummyAuth()

class DummyApp:
  def __init__(self, state):
    self.state = state

class DummyRequest:
  def __init__(self, storage, cache):
    self.app = DummyApp(DummyState(storage, cache))
    self.headers = {}


def test_get_files_returns_list():
  async def fake_get(request):
    rpc = RPCRequest(op="urn:storage:files:get_files:1", payload=None, version=1)
    auth = SimpleNamespace(user_guid="u1", roles=["ROLE_STORAGE"], role_mask=0x2)
    return rpc, auth, None
  svc_mod.unbox_request = fake_get
  storage = StorageModule()
  storage.files = [{"name": "a.txt", "url": "http://x/a.txt", "content_type": "text/plain"}]
  cache = StorageCacheModule(storage)
  cache.cache = storage.files
  req = DummyRequest(storage, cache)
  resp = asyncio.run(storage_files_get_files_v1(req))
  assert isinstance(resp, RPCResponse)
  assert resp.payload["files"][0]["name"] == "a.txt"


def test_upload_files_calls_storage():
  async def fake_up(request):
    rpc = RPCRequest(
      op="urn:storage:files:upload_files:1",
      payload={"files": [{"name": "a.txt", "content_b64": "YQ==", "content_type": "text/plain"}]},
      version=1,
    )
    auth = SimpleNamespace(user_guid="u1", roles=["ROLE_STORAGE"], role_mask=0x2)
    return rpc, auth, None
  svc_mod.unbox_request = fake_up
  storage = StorageModule()
  cache = StorageCacheModule(storage)
  req = DummyRequest(storage, cache)
  resp = asyncio.run(storage_files_upload_files_v1(req))
  assert storage.uploads and storage.uploads[0][1] == "a.txt"
  assert isinstance(resp, RPCResponse)


def test_delete_files_calls_storage():
  async def fake_del(request):
    rpc = RPCRequest(
      op="urn:storage:files:delete_files:1",
      payload={"files": ["a.txt", "b.txt"]},
      version=1,
    )
    auth = SimpleNamespace(user_guid="u1", roles=["ROLE_STORAGE"], role_mask=0x2)
    return rpc, auth, None
  svc_mod.unbox_request = fake_del
  storage = StorageModule()
  cache = StorageCacheModule(storage)
  req = DummyRequest(storage, cache)
  resp = asyncio.run(storage_files_delete_files_v1(req))
  assert ("u1", "a.txt") in storage.deleted
  assert ("u1", "b.txt") in storage.deleted
  assert isinstance(resp, RPCResponse)


def test_set_gallery_validates_file():
  async def fake_set(request):
    rpc = RPCRequest(
      op="urn:storage:files:set_gallery:1",
      payload={"name": "a.txt", "gallery": True},
      version=1,
    )
    auth = SimpleNamespace(user_guid="u1", roles=["ROLE_STORAGE"], role_mask=0x2)
    return rpc, auth, None
  svc_mod.unbox_request = fake_set
  storage = StorageModule()
  storage.files = [{"name": "a.txt", "url": "http://x/a.txt"}]
  cache = StorageCacheModule(storage)
  req = DummyRequest(storage, cache)
  resp = asyncio.run(storage_files_set_gallery_v1(req))
  assert resp.payload["name"] == "a.txt"
  assert ("u1", "a.txt") in storage.validated


def test_create_folder_calls_storage():
  async def fake_create(request):
    rpc = RPCRequest(
      op="urn:storage:files:create_folder:1",
      payload={"path": "a/b"},
      version=1,
    )
    auth = SimpleNamespace(user_guid="u1", roles=["ROLE_STORAGE"], role_mask=0x2)
    return rpc, auth, None
  svc_mod.unbox_request = fake_create
  storage = StorageModule()
  cache = StorageCacheModule(storage)
  req = DummyRequest(storage, cache)
  resp = asyncio.run(storage_files_create_folder_v1(req))
  assert ("u1", "a/b") in storage.created
  assert isinstance(resp, RPCResponse)


def test_move_file_calls_storage():
  async def fake_move(request):
    rpc = RPCRequest(
      op="urn:storage:files:move_file:1",
      payload={"src": "a.txt", "dst": "b/a.txt"},
      version=1,
    )
    auth = SimpleNamespace(user_guid="u1", roles=["ROLE_STORAGE"], role_mask=0x2)
    return rpc, auth, None
  svc_mod.unbox_request = fake_move
  storage = StorageModule()
  cache = StorageCacheModule(storage)
  req = DummyRequest(storage, cache)
  resp = asyncio.run(storage_files_move_file_v1(req))
  assert ("u1", "a.txt", "b/a.txt") in storage.moved
  assert isinstance(resp, RPCResponse)


def test_refresh_cache_updates_cache():
  async def fake_refresh(request):
    rpc = RPCRequest(op="urn:storage:files:refresh_cache:1", payload=None, version=1)
    auth = SimpleNamespace(user_guid="u1", roles=["ROLE_STORAGE"], role_mask=0x2)
    return rpc, auth, None
  svc_mod.unbox_request = fake_refresh
  storage = StorageModule()
  storage.files = [{"name": "a.txt", "url": "http://x/a.txt", "content_type": "text/plain"}]
  cache = StorageCacheModule(storage)
  req = DummyRequest(storage, cache)
  resp = asyncio.run(storage_files_refresh_cache_v1(req))
  assert cache.cache and cache.cache[0]["name"] == "a.txt"
  assert isinstance(resp, RPCResponse)
