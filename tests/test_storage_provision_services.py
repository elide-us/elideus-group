import asyncio, importlib.util, pathlib, sys, types

# stub rpc package
root_path = pathlib.Path(__file__).resolve().parent.parent
pkg = types.ModuleType("rpc")
pkg.__path__ = [str(root_path / "rpc")]
sys.modules["rpc"] = pkg

# ensure nested rpc packages exist
storage_pkg = types.ModuleType("rpc.storage")
storage_pkg.__path__ = [str(root_path / "rpc" / "storage")]
sys.modules["rpc.storage"] = storage_pkg

provision_pkg = types.ModuleType("rpc.storage.provision")
provision_pkg.__path__ = [str(root_path / "rpc" / "storage" / "provision")]
sys.modules["rpc.storage.provision"] = provision_pkg

spec = importlib.util.spec_from_file_location("server.models", "server/models.py")
models = importlib.util.module_from_spec(spec)
spec.loader.exec_module(models)
RPCRequest = models.RPCRequest
RPCResponse = models.RPCResponse
sys.modules["server.models"] = models

# stub server module
server_pkg = types.ModuleType("server")
modules_pkg = types.ModuleType("server.modules")
storage_module_pkg = types.ModuleType("server.modules.storage_module")

class StorageModule:
  def __init__(self):
    self.created = []
    self.exists = False
  async def ensure_user_folder(self, user_guid):
    self.created.append(user_guid)
  async def user_folder_exists(self, user_guid):
    return self.exists

storage_module_pkg.StorageModule = StorageModule
modules_pkg.storage_module = storage_module_pkg
server_pkg.modules = modules_pkg
sys.modules.setdefault("server", server_pkg)
sys.modules.setdefault("server.modules", modules_pkg)
sys.modules.setdefault("server.modules.storage_module", storage_module_pkg)

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
  "rpc.storage.provision.services", "rpc/storage/provision/services.py",
)
svc_mod = importlib.util.module_from_spec(svc_spec)
sys.modules["rpc.storage.provision.services"] = svc_mod
svc_spec.loader.exec_module(svc_mod)

# restore real helpers
sys.modules["rpc.helpers"] = real_helpers

storage_provision_create_user_v1 = svc_mod.storage_provision_create_user_v1
storage_provision_check_user_v1 = svc_mod.storage_provision_check_user_v1


class DummyState:
  def __init__(self, storage):
    self.storage = storage

class DummyRequest:
  def __init__(self, storage):
    self.app = types.SimpleNamespace(state=DummyState(storage))
    self.headers = {}


def test_create_user_calls_storage():
  async def fake_unbox(request):
    rpc = RPCRequest(op="urn:storage:provision:create_user:1", payload=None, version=1)
    auth = types.SimpleNamespace(user_guid="u1")
    return rpc, auth, None
  svc_mod.unbox_request = fake_unbox
  storage = StorageModule()
  req = DummyRequest(storage)
  resp = asyncio.run(storage_provision_create_user_v1(req))
  assert "u1" in storage.created
  assert isinstance(resp, RPCResponse)


def test_check_user_returns_status():
  async def fake_unbox(request):
    rpc = RPCRequest(op="urn:storage:provision:check_user:1", payload=None, version=1)
    auth = types.SimpleNamespace(user_guid="u1")
    return rpc, auth, None
  svc_mod.unbox_request = fake_unbox
  storage = StorageModule()
  storage.exists = True
  req = DummyRequest(storage)
  resp = asyncio.run(storage_provision_check_user_v1(req))
  assert resp.payload["exists"] is True
  assert isinstance(resp, RPCResponse)
