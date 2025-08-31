import sys, types, asyncio, importlib.util
from types import SimpleNamespace

class DBRes:
  def __init__(self, rows=None, rowcount=0):
    self.rows = rows or []
    self.rowcount = rowcount

class DummyDb:
  def __init__(self):
    self.calls = []
  async def run(self, op, args):
    self.calls.append((op, args))
    if op == "db:auth:session:get_by_access_token:1":
      return DBRes([
        {
          "session_guid": "sess-guid",
          "device_guid": "dev-guid",
          "user_guid": "user-guid",
          "issued_at": "2099-01-01T00:00:00Z",
          "expires_at": "2099-01-01T01:00:00Z",
          "device_fingerprint": "fp",
          "user_agent": "ua",
          "ip_last_seen": "127.0.0.1",
        }
      ], 1)
    return DBRes()

class DummyState:
  def __init__(self):
    self.db = DummyDb()

class DummyApp:
  def __init__(self):
    self.state = DummyState()

class DummyRequest:
  def __init__(self):
    self.app = DummyApp()
    self.headers = {"authorization": "Bearer tok", "user-agent": "ua"}
    self.client = SimpleNamespace(host="127.0.0.1")


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

  sys.modules.setdefault("server", types.ModuleType("server"))
  sys.modules.setdefault("server.modules", types.ModuleType("server.modules"))
  db_mod = types.ModuleType("server.modules.db_module")
  class DbModule: ...
  db_mod.DbModule = DbModule
  sys.modules["server.modules.db_module"] = db_mod

  svc_spec = importlib.util.spec_from_file_location(
    "rpc.auth.session.services", "rpc/auth/session/services.py"
  )
  svc_mod = importlib.util.module_from_spec(svc_spec)
  svc_spec.loader.exec_module(svc_mod)
  auth_session_get_session_v1 = svc_mod.auth_session_get_session_v1

  req = DummyRequest()
  resp = asyncio.run(auth_session_get_session_v1(req))
  assert isinstance(resp, RPCResponse)
  calls = [op for op, _ in req.app.state.db.calls]
  assert "db:auth:session:get_by_access_token:1" in calls
  assert "db:auth:session:update_session:1" in calls
