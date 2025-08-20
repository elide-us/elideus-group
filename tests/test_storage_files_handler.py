import asyncio
import importlib.util
import pathlib
import sys
import types
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

# stub rpc package and models
pkg = types.ModuleType("rpc")
pkg.__path__ = [str(pathlib.Path(__file__).resolve().parent.parent / "rpc")]
sys.modules.setdefault("rpc", pkg)

spec = importlib.util.spec_from_file_location("rpc.models", "rpc/models.py")
models = importlib.util.module_from_spec(spec)
spec.loader.exec_module(models)
RPCRequest = models.RPCRequest
RPCResponse = models.RPCResponse
sys.modules["rpc.models"] = models

# stub helpers for handler import
helpers_stub = types.ModuleType("rpc.helpers")
async def _stub(request):
  raise NotImplementedError
helpers_stub.get_rpcrequest_from_request = _stub
sys.modules["rpc.helpers"] = helpers_stub

# stub files package with dispatcher map
files_pkg = types.ModuleType("rpc.storage.files")
files_pkg.DISPATCHERS = {}
sys.modules["rpc.storage.files"] = files_pkg

# import handler with stubs
handler_spec = importlib.util.spec_from_file_location("rpc.storage.files.handler", "rpc/storage/files/handler.py")
handler_mod = importlib.util.module_from_spec(handler_spec)
handler_spec.loader.exec_module(handler_mod)
handle_files_request = handler_mod.handle_files_request

# restore real helpers for other tests
real_helpers_spec = importlib.util.spec_from_file_location("rpc.helpers", "rpc/helpers.py")
real_helpers = importlib.util.module_from_spec(real_helpers_spec)
real_helpers_spec.loader.exec_module(real_helpers)
sys.modules["rpc.helpers"] = real_helpers


class DummyAuth:
  def __init__(self):
    self.roles = {"ROLE_STORAGE_ENABLED": 0x2}


class DummyState:
  def __init__(self):
    self.auth = DummyAuth()


class DummyApp:
  def __init__(self):
    self.state = DummyState()


class DummyRequest:
  def __init__(self):
    self.app = DummyApp()
    self.headers = {}


def test_handle_files_request_requires_role():
  called = False

  async def stub_service(request):
    nonlocal called
    called = True
    return RPCResponse(op="ok", payload=None, version=1)

  files_pkg.DISPATCHERS[("get_files", "1")] = stub_service

  async def fake_get(request):
    rpc = RPCRequest(op="urn:storage:files:get_files:1", payload=None, version=1)
    auth = SimpleNamespace(roles=[], role_mask=0)
    return rpc, auth, None

  handler_mod.get_rpcrequest_from_request = fake_get
  req = DummyRequest()

  with pytest.raises(HTTPException) as exc:
    asyncio.run(handle_files_request(["get_files", "1"], req))

  assert exc.value.status_code == 403
  assert not called


def test_handle_files_request_dispatches():
  called = False

  async def stub_service(request):
    nonlocal called
    called = True
    return RPCResponse(op="ok", payload=None, version=1)

  files_pkg.DISPATCHERS[("get_files", "1")] = stub_service

  async def fake_get(request):
    rpc = RPCRequest(op="urn:storage:files:get_files:1", payload=None, version=1)
    auth = SimpleNamespace(roles=["ROLE_STORAGE_ENABLED"], role_mask=0x2)
    return rpc, auth, None

  handler_mod.get_rpcrequest_from_request = fake_get
  req = DummyRequest()

  resp = asyncio.run(handle_files_request(["get_files", "1"], req))

  assert isinstance(resp, RPCResponse)
  assert called

