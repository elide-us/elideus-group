import asyncio
import importlib.util
import pathlib
import sys
import types
from types import SimpleNamespace


def _dummy_request(oauth_module):
  return SimpleNamespace(app=SimpleNamespace(state=SimpleNamespace(oauth=oauth_module)))


def _load_module(name: str, path: pathlib.Path):
  spec = importlib.util.spec_from_file_location(name, path)
  module = importlib.util.module_from_spec(spec)
  spec.loader.exec_module(module)
  return module


class StubOauthModule:
  def __init__(self):
    self.calls = []
    self.ready = False

  async def on_ready(self):
    self.ready = True

  async def unlink_last_provider_record(self, guid: str, provider: str):
    self.calls.append((guid, provider))


def test_auth_providers_unlink_last_provider_uses_module(monkeypatch):
  root_path = pathlib.Path(__file__).resolve().parent.parent

  rpc_pkg = types.ModuleType("rpc")
  rpc_pkg.__path__ = [str(root_path / "rpc")]
  rpc_pkg.HANDLERS = {}
  monkeypatch.setitem(sys.modules, "rpc", rpc_pkg)

  server_pkg = types.ModuleType("server")
  server_pkg.__path__ = [str(root_path / "server")]
  monkeypatch.setitem(sys.modules, "server", server_pkg)

  models_mod = _load_module("server.models", root_path / "server/models.py")
  RPCRequest = models_mod.RPCRequest
  monkeypatch.setitem(sys.modules, "server.models", models_mod)
  server_pkg.models = models_mod

  helpers_mod = _load_module("rpc.helpers", root_path / "rpc/helpers.py")
  monkeypatch.setitem(sys.modules, "rpc.helpers", helpers_mod)

  modules_mod = _load_module("server.modules", root_path / "server/modules/__init__.py")
  monkeypatch.setitem(sys.modules, "server.modules", modules_mod)
  server_pkg.modules = modules_mod

  oauth_stub = types.ModuleType("server.modules.oauth_module")
  class OauthModule:  # pragma: no cover
    pass
  oauth_stub.OauthModule = OauthModule
  monkeypatch.setitem(sys.modules, "server.modules.oauth_module", oauth_stub)

  auth_models_mod = _load_module(
    "rpc.auth.providers.models",
    root_path / "rpc/auth/providers/models.py",
  )
  monkeypatch.setitem(sys.modules, "rpc.auth.providers.models", auth_models_mod)

  services_mod = _load_module(
    "rpc.auth.providers.services",
    root_path / "rpc/auth/providers/services.py",
  )

  module = StubOauthModule()
  request = _dummy_request(module)

  async def fake_unbox(_request):
    return (
      RPCRequest(
        op="urn:auth:providers:unlink_last_provider:1",
        payload={"guid": "user-guid", "provider": "google"},
        version=1,
      ),
      None,
      None,
    )

  original_unbox = services_mod.unbox_request
  monkeypatch.setattr(services_mod, "unbox_request", fake_unbox)

  try:
    resp = asyncio.run(services_mod.auth_providers_unlink_last_provider_v1(request))
  finally:
    services_mod.unbox_request = original_unbox

  assert module.ready is True
  assert module.calls == [("user-guid", "google")]
  assert resp.payload == {"ok": True}
