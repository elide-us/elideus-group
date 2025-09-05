import sys, types, importlib.util, asyncio
from types import SimpleNamespace
from datetime import datetime, timezone, timedelta
import json


class DummyAuth:
  def __init__(self, profile):
    self.profile = profile
  async def handle_auth_login(self, provider, id_token, access_token):
    return "00000000-0000-0000-0000-000000000001", self.profile, {}
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
  def __init__(self, allow_update):
    self.calls = []
    self.allow_update = allow_update
  async def run(self, op, args):
    self.calls.append((op, args))
    if op == "urn:users:providers:get_by_provider_identifier:1":
      return DBRes([{ "guid": "user-guid", "display_name": "User", "credits": 0, "provider_name": "microsoft" }], 1)
    if op == "urn:users:profile:update_if_unedited:1":
      if self.allow_update:
        return DBRes([{ "display_name": args["display_name"], "email": args["email"] }], 1)
      return DBRes([], 0)
    if op == "db:users:session:set_rotkey:1":
      return DBRes([], 1)
    if op == "db:auth:session:create_session:1":
      return DBRes([{ "session_guid": "sess", "device_guid": "dev" }], 1)
    if op == "db:auth:session:update_device_token:1":
      return DBRes([], 1)
    return DBRes()


class DummyState:
  def __init__(self, auth, db):
    self.auth = auth
    self.db = db


class DummyApp:
  def __init__(self, state):
    self.state = state


class DummyRequest:
  def __init__(self, state):
    self.app = DummyApp(state)
    self.headers = {"user-agent": "tester"}
    self.client = SimpleNamespace(host="127.0.0.1")


def setup_module(mod):
  spec = importlib.util.spec_from_file_location("server.models", "server/models.py")
  models = importlib.util.module_from_spec(spec)
  spec.loader.exec_module(models)
  sys.modules["server.models"] = models
  RPCRequest = models.RPCRequest

  helpers = types.ModuleType("rpc.helpers")
  async def fake_unbox_request(_):
    rpc = RPCRequest(op="urn:auth:microsoft:oauth_login:1", payload={"idToken": "id", "accessToken": "acc", "fingerprint": "fp"}, version=1)
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
  mod.auth_microsoft_oauth_login_v1 = svc_mod.auth_microsoft_oauth_login_v1


def test_updates_profile_if_unedited():
  auth = DummyAuth({"email": "new@example.com", "username": "New"})
  db = DummyDb(True)
  state = DummyState(auth, db)
  req = DummyRequest(state)
  resp = asyncio.run(auth_microsoft_oauth_login_v1(req))
  assert any(op == "urn:users:profile:update_if_unedited:1" for op, _ in db.calls)
  data = json.loads(resp.body)
  assert data["payload"]["display_name"] == "New"


def test_leaves_profile_if_edited():
  auth = DummyAuth({"email": "new@example.com", "username": "New"})
  db = DummyDb(False)
  state = DummyState(auth, db)
  req = DummyRequest(state)
  resp = asyncio.run(auth_microsoft_oauth_login_v1(req))
  assert any(op == "urn:users:profile:update_if_unedited:1" for op, _ in db.calls)
  data = json.loads(resp.body)
  assert data["payload"]["display_name"] == "User"

