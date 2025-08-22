from types import SimpleNamespace
from datetime import datetime, timezone, timedelta
import asyncio
import importlib.util
import sys
import types
import uuid

class DummyAuth:
  async def handle_auth_login(self, provider, id_token, access_token):
    profile = {"email": "user@example.com", "username": "User"}
    return str(uuid.uuid4()), profile, {}
  def make_rotation_token(self, user_guid):
    return "rot", datetime.now(timezone.utc) + timedelta(hours=1)
  def make_session_token(self, user_guid, rot, roles, provider):
    return "sess", datetime.now(timezone.utc) + timedelta(hours=1)
  async def get_user_roles(self, guid, refresh=False):
    return [], 0
  def __init__(self):
    self.providers = {"google": SimpleNamespace(audience="gid")}

class DBRes:
  def __init__(self, rows=None, rowcount=0):
    self.rows = rows or []
    self.rowcount = rowcount

class DummyDb:
  def __init__(self):
    self.calls = []
  async def run(self, op, args):
    self.calls.append((op, args))
    if op == "urn:users:providers:get_by_provider_identifier:1":
      return DBRes([{ "guid": "user-guid", "display_name": "User", "credits": 0 }], 1)
    if op == "urn:system:config:get_config:1":
      key = args.get("key")
      if key == "GoogleApiId":
        return DBRes([{ "value": "gsecret" }], 1)
      if key == "GoogleAuthRedirectLocalhost":
        return DBRes([{ "value": "http://localhost:8000/userpage" }], 1)
    return DBRes()

  async def get_google_api_secret(self):
    return "gsecret"

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

def test_lookup_existing_user(monkeypatch):
  spec = importlib.util.spec_from_file_location("rpc.models", "rpc/models.py")
  models = importlib.util.module_from_spec(spec)
  spec.loader.exec_module(models)
  sys.modules["rpc.models"] = models
  RPCRequest = models.RPCRequest
  RPCResponse = models.RPCResponse

  helpers = types.ModuleType("rpc.helpers")
  async def fake_unbox_request(request):
    rpc = RPCRequest(op="urn:auth:google:oauth_login:1", payload={"code": "auth-code"}, version=1)
    return rpc, None, None
  helpers.unbox_request = fake_unbox_request
  sys.modules["rpc.helpers"] = helpers

  sys.modules.setdefault("rpc", types.ModuleType("rpc"))
  sys.modules.setdefault("rpc.auth", types.ModuleType("rpc.auth"))
  rpc_auth_google = types.ModuleType("rpc.auth.google")
  rpc_auth_google.__path__ = []
  sys.modules.setdefault("rpc.auth.google", rpc_auth_google)
  from pydantic import BaseModel
  models_mod = types.ModuleType("rpc.auth.google.models")
  class AuthGoogleOauthLoginPayload1(BaseModel):
    provider: str = "google"
    code: str
    fingerprint: str | None = None
  class AuthGoogleOauthLogin1(BaseModel):
    sessionToken: str
    display_name: str
    credits: int
    profile_image: str | None = None
  models_mod.AuthGoogleOauthLoginPayload1 = AuthGoogleOauthLoginPayload1
  models_mod.AuthGoogleOauthLogin1 = AuthGoogleOauthLogin1
  sys.modules["rpc.auth.google.models"] = models_mod

  sys.modules["server"] = types.ModuleType("server")
  sys.modules["server.models"] = types.ModuleType("server.models")
  sys.modules["server.modules"] = types.ModuleType("server.modules")
  auth_mod = types.ModuleType("server.modules.auth_module")
  class AuthModule: ...
  auth_mod.AuthModule = AuthModule
  sys.modules["server.modules.auth_module"] = auth_mod
  db_mod = types.ModuleType("server.modules.db_module")
  class DbModule: ...
  db_mod.DbModule = DbModule
  sys.modules["server.modules.db_module"] = db_mod

  svc_spec = importlib.util.spec_from_file_location(
    "rpc.auth.google.services", "rpc/auth/google/services.py"
  )
  svc_mod = importlib.util.module_from_spec(svc_spec)
  svc_spec.loader.exec_module(svc_mod)
  async def fake_exchange(code, client_id, client_secret, redirect_uri):
    assert code == "auth-code"
    assert redirect_uri == "http://localhost:8000/userpage"
    return "id", "acc"
  svc_mod.exchange_code_for_tokens = fake_exchange
  auth_google_oauth_login_v1 = svc_mod.auth_google_oauth_login_v1

  req = DummyRequest()
  resp = asyncio.run(auth_google_oauth_login_v1(req))
  assert isinstance(resp, RPCResponse)
  assert not any(op == "urn:users:providers:create_from_provider:1" for op, _ in req.app.state.db.calls)
