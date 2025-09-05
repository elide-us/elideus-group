import sys, asyncio, importlib.util, types
from types import SimpleNamespace


def test_refresh_token_ignores_provider():
  spec = importlib.util.spec_from_file_location("server.models", "server/models.py")
  models = importlib.util.module_from_spec(spec)
  spec.loader.exec_module(models)
  sys.modules["server.models"] = models
  RPCResponse = models.RPCResponse

  helpers = types.ModuleType("rpc.helpers")
  async def fake_unbox(_req):
    return None
  helpers.unbox_request = fake_unbox
  sys.modules["rpc.helpers"] = helpers

  class DummySession:
    def __init__(self):
      self.calls = 0
    async def refresh_token(self, rotation_token, fingerprint, user_agent, ip_address):
      self.calls += 1
      return "new-token"

  session_mod = DummySession()

  class DummyState:
    def __init__(self):
      self.session = session_mod
      self.auth = SimpleNamespace(provider=None)

  class DummyApp:
    def __init__(self):
      self.state = DummyState()

  class DummyRequest:
    def __init__(self):
      self.app = DummyApp()
      self.headers = {}
      self.cookies = {"rotation_token": "rot-token"}
      self.client = SimpleNamespace(host="127.0.0.1")
    async def json(self):
      return {"fingerprint": "fp"}

  svc_spec = importlib.util.spec_from_file_location("rpc.auth.session.services", "rpc/auth/session/services.py")
  svc_mod = importlib.util.module_from_spec(svc_spec)
  svc_spec.loader.exec_module(svc_mod)

  req = DummyRequest()
  resp = asyncio.run(svc_mod.auth_session_refresh_token_v1(req))
  assert isinstance(resp, RPCResponse)
  assert session_mod.calls == 1
  assert req.app.state.auth.provider is None
