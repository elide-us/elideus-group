import importlib.util
import types
import sys
import asyncio
from types import SimpleNamespace


class DBRes:
  def __init__(self, rows=None, rowcount=0):
    self.rows = rows or []
    self.rowcount = rowcount

class DummyDb:
  async def run(self, op, args):
    if op == "db:users:session:get_rotkey:1":
      return DBRes([{ "rotkey": "rot-token", "provider_name": "google" }], 1)
    if op == "db:auth:session:create_session:1":
      return DBRes([{ "session_guid": "sess-guid", "device_guid": "dev-guid" }], 1)
    if op == "db:auth:session:update_device_token:1":
      return DBRes(rowcount=1)
    return DBRes()

class DummyAuth:
  def __init__(self):
    self.provider = None
  def decode_rotation_token(self, token):
    return {"guid": "user-guid"}
  async def get_user_roles(self, _guid):
    return (["user"], 0)
  def make_session_token(self, user_guid, rot, session_guid, device_guid, roles, exp=None):
    return ("new-token", exp)

class DummyState:
  def __init__(self):
    self.db = DummyDb()
    self.auth = DummyAuth()

class DummyApp:
  def __init__(self):
    self.state = DummyState()

class DummyRequest:
  def __init__(self):
    self.app = DummyApp()
    self.headers = {}
    self.cookies = {"rotation_token": "rot-token"}
    self.client = SimpleNamespace(host="127.0.0.1")


def _setup():
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
  sys.modules.setdefault("server", types.ModuleType("server"))
  sys.modules.setdefault("server.modules", types.ModuleType("server.modules"))
  class AuthContext: ...
  models.AuthContext = AuthContext
  db_mod = types.ModuleType("server.modules.db_module")
  class DbModule: ...
  db_mod.DbModule = DbModule
  sys.modules["server.modules.db_module"] = db_mod
  auth_mod = types.ModuleType("server.modules.auth_module")
  class AuthModule: ...
  auth_mod.AuthModule = AuthModule
  sys.modules["server.modules.auth_module"] = auth_mod
  spec = importlib.util.spec_from_file_location("rpc.auth.session.services", "rpc/auth/session/services.py")
  svc_mod = importlib.util.module_from_spec(spec)
  spec.loader.exec_module(svc_mod)
  return svc_mod, RPCResponse


def test_refresh_token_ignores_provider():
  svc_mod, RPCResponse = _setup()
  req = DummyRequest()
  resp = asyncio.run(svc_mod.auth_session_refresh_token_v1(req))
  assert isinstance(resp, RPCResponse)
  assert req.app.state.auth.provider is None
