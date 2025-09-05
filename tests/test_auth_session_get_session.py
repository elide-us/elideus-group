import sys, types, asyncio, importlib.util
from types import SimpleNamespace


def test_get_session(monkeypatch):
  spec = importlib.util.spec_from_file_location("server.models", "server/models.py")
  models = importlib.util.module_from_spec(spec)
  spec.loader.exec_module(models)
  sys.modules["server.models"] = models
  RPCRequest = models.RPCRequest
  RPCResponse = models.RPCResponse

  helpers = types.ModuleType("rpc.helpers")
  async def fake_unbox_request(request):
    rpc = RPCRequest(op="urn:auth:session:get_session:1", payload=None, version=1)
    return rpc, SimpleNamespace(), None
  helpers.unbox_request = fake_unbox_request
  sys.modules["rpc.helpers"] = helpers

  class DummySession:
    def __init__(self):
      self.calls = []
    async def get_session(self, token, ip_address, user_agent):
      self.calls.append((token, ip_address, user_agent))
      return {"session_guid": "sess-guid"}

  session_mod = DummySession()

  class DummyState:
    def __init__(self):
      self.session = session_mod

  class DummyApp:
    def __init__(self):
      self.state = DummyState()

  class DummyRequest:
    def __init__(self):
      self.app = DummyApp()
      self.headers = {"authorization": "Bearer tok", "user-agent": "ua"}
      self.client = SimpleNamespace(host="127.0.0.1")

  svc_spec = importlib.util.spec_from_file_location(
    "rpc.auth.session.services", "rpc/auth/session/services.py"
  )
  svc_mod = importlib.util.module_from_spec(svc_spec)
  svc_spec.loader.exec_module(svc_mod)
  auth_session_get_session_v1 = svc_mod.auth_session_get_session_v1

  req = DummyRequest()
  resp = asyncio.run(auth_session_get_session_v1(req))
  assert isinstance(resp, RPCResponse)
  assert session_mod.calls[0] == ("tok", "127.0.0.1", "ua")
