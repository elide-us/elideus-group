import asyncio
import importlib.util
import pathlib
import sys
import types

# stub rpc package and models
pkg = types.ModuleType("rpc")
pkg.__path__ = [str(pathlib.Path(__file__).resolve().parent.parent / "rpc")]
sys.modules.setdefault("rpc", pkg)

spec = importlib.util.spec_from_file_location("rpc.models", "rpc/models.py")
models = importlib.util.module_from_spec(spec)
spec.loader.exec_module(models)
RPCResponse = models.RPCResponse
sys.modules["rpc.models"] = models

# stub files package with dispatcher map
files_pkg = types.ModuleType("rpc.storage.files")
files_pkg.DISPATCHERS = {}
sys.modules["rpc.storage.files"] = files_pkg

# import handler with stubs
handler_spec = importlib.util.spec_from_file_location("rpc.storage.files.handler", "rpc/storage/files/handler.py")
handler_mod = importlib.util.module_from_spec(handler_spec)
handler_spec.loader.exec_module(handler_mod)
handle_files_request = handler_mod.handle_files_request


class DummyRequest:
  def __init__(self):
    self.app = types.SimpleNamespace()
    self.headers = {}


def test_handle_files_request_dispatches():
  called = False

  async def stub_service(request):
    nonlocal called
    called = True
    return RPCResponse(op="ok", payload=None, version=1)

  files_pkg.DISPATCHERS[("get_files", "1")] = stub_service
  req = DummyRequest()

  resp = asyncio.run(handle_files_request(["get_files", "1"], req))

  assert isinstance(resp, RPCResponse)
  assert called
