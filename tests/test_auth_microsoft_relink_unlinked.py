import sys, types, importlib.util, asyncio
from types import SimpleNamespace
from datetime import datetime, timezone, timedelta

class DummyAuth:
  async def handle_auth_login(self, provider, id_token, access_token):
    profile = {"email": "user@example.com", "username": "User"}
    return "00000000-0000-0000-0000-000000000001", profile, {}
  def make_rotation_token(self, user_guid):
    return "rot", datetime.now(timezone.utc) + timedelta(hours=1)
  def make_session_token(self, user_guid, rot, session_guid, device_guid, roles, exp=None):
    return "sess", exp or datetime.now(timezone.utc) + timedelta(hours=1)
  async def get_user_roles(self, guid, refresh=False):
    return [], 0

class DBRes:
  def __init__(self, rows=None, rowcount=0):
    self.rows = rows or []
    self.rowcount = rowcount

class DummyDb:
  def __init__(self):
    self.calls = []
    self._get_by_count = 0
  async def run(self, op, args):
    self.calls.append((op, args))
    if op == "urn:users:providers:get_by_provider_identifier:1":
      self._get_by_count += 1
      if self._get_by_count == 1:
        return DBRes([], 0)
      return DBRes([{ "guid": "user-guid", "display_name": "User", "credits": 0 }], 1)
    if op == "urn:users:providers:get_any_by_provider_identifier:1":
      return DBRes([{"guid": "user-guid"}], 1)
    if op == "urn:auth:microsoft:oauth_relink:1":
      return DBRes([{ "guid": "user-guid", "display_name": "User", "credits": 0 }], 1)
    if op == "db:users:session:set_rotkey:1":
      return DBRes([], 1)
    if op == "db:auth:session:create_session:1":
      return DBRes([{ "session_guid": "sess", "device_guid": "dev" }], 1)
    if op == "db:auth:session:update_device_token:1":
      return DBRes([], 1)
    return DBRes()

class DummyState:
  def __init__(self):
    self.auth = DummyAuth()
    self.db = DummyDb()

class DummyApp:
  def __init__(self):
    self.state = DummyState()

class DummyRequest:
  def __init__(self):
    self.app = DummyApp()
    self.headers = {"user-agent": "tester"}
    self.client = SimpleNamespace(host="127.0.0.1")

def test_relinks_unlinked_account(monkeypatch):
  spec = importlib.util.spec_from_file_location("server.models", "server/models.py")
  models = importlib.util.module_from_spec(spec)
  spec.loader.exec_module(models)
  sys.modules["server.models"] = models
  RPCRequest = models.RPCRequest

  helpers = types.ModuleType("rpc.helpers")
  async def fake_unbox_request(_):
    rpc = RPCRequest(op="urn:auth:microsoft:oauth_login:1", payload={"idToken": "id", "accessToken": "acc"}, version=1)
    return rpc, None, None
  helpers.unbox_request = fake_unbox_request
  sys.modules["rpc.helpers"] = helpers

  sys.modules.setdefault("rpc", types.ModuleType("rpc"))
  sys.modules.setdefault("rpc.auth", types.ModuleType("rpc.auth"))
  rpc_auth_ms = types.ModuleType("rpc.auth.microsoft")
  rpc_auth_ms.__path__ = []
  sys.modules.setdefault("rpc.auth.microsoft", rpc_auth_ms)
  from pydantic import BaseModel
  models_mod = types.ModuleType("rpc.auth.microsoft.models")
  class AuthMicrosoftOauthLogin1(BaseModel):
    sessionToken: str
    display_name: str
    credits: int
    profile_image: str | None = None
  models_mod.AuthMicrosoftOauthLogin1 = AuthMicrosoftOauthLogin1
  sys.modules["rpc.auth.microsoft.models"] = models_mod

  sys.modules["server"] = types.ModuleType("server")
  sys.modules["server.modules"] = types.ModuleType("server.modules")
  auth_mod = types.ModuleType("server.modules.auth_module")
  class AuthModule: ...
  auth_mod.AuthModule = AuthModule
  sys.modules["server.modules.auth_module"] = auth_mod
  db_mod = types.ModuleType("server.modules.db_module")
  class DbModule: ...
  db_mod.DbModule = DbModule
  sys.modules["server.modules.db_module"] = db_mod

  svc_spec = importlib.util.spec_from_file_location("rpc.auth.microsoft.services", "rpc/auth/microsoft/services.py")
  svc_mod = importlib.util.module_from_spec(svc_spec)
  svc_spec.loader.exec_module(svc_mod)
  auth_microsoft_oauth_login_v1 = svc_mod.auth_microsoft_oauth_login_v1

  req = DummyRequest()
  asyncio.run(auth_microsoft_oauth_login_v1(req))
  calls = req.app.state.db.calls
  assert any(op == "urn:auth:microsoft:oauth_relink:1" for op, _ in calls)
  assert not any(op == "urn:users:providers:create_from_provider:1" for op, _ in calls)
