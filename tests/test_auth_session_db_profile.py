import asyncio, importlib.util, sys, types, json
from datetime import datetime, timezone, timedelta
from types import SimpleNamespace

import pytest

def test_auth_session_returns_db_profile(monkeypatch):
  spec = importlib.util.spec_from_file_location("rpc.models", "rpc/models.py")
  models = importlib.util.module_from_spec(spec)
  spec.loader.exec_module(models)
  monkeypatch.setitem(sys.modules, "rpc.models", models)
  monkeypatch.setitem(sys.modules, "rpc", types.ModuleType("rpc"))
  helpers = types.ModuleType("rpc.helpers")
  async def _unbox_request(request):
    raise NotImplementedError
  helpers.unbox_request = _unbox_request
  monkeypatch.setitem(sys.modules, "rpc.helpers", helpers)
  monkeypatch.setitem(sys.modules, "server", types.ModuleType("server"))
  monkeypatch.setitem(sys.modules, "server.modules", types.ModuleType("server.modules"))
  auth_mod = types.ModuleType("server.modules.auth_module")
  class AuthModule: ...
  auth_mod.AuthModule = AuthModule
  monkeypatch.setitem(sys.modules, "server.modules.auth_module", auth_mod)
  db_mod = types.ModuleType("server.modules.db_module")
  class DbModule: ...
  db_mod.DbModule = DbModule
  monkeypatch.setitem(sys.modules, "server.modules.db_module", db_mod)

  svc_spec = importlib.util.spec_from_file_location("rpc.auth.session.services", "rpc/auth/session/services.py")
  svc_mod = importlib.util.module_from_spec(svc_spec)
  svc_spec.loader.exec_module(svc_mod)
  auth_session_get_token_v1 = svc_mod.auth_session_get_token_v1

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
        return DBRes([{ "guid": "u1", "display_name": "DB", "email": "db@example.com", "credits": 5, "profile_image": "img" }], 1)
      return DBRes()

  class DummyAuth:
    async def handle_auth_login(self, provider, id_token, access_token):
      return "0a1b2c3d-4e5f-6789-aaaa-bbbbccccdddd", {"email": "prov@example.com", "username": "Prov"}, {}
    def make_rotation_token(self, user_guid):
      return "rot", datetime.now(timezone.utc) + timedelta(hours=1)
    def make_session_token(self, user_guid, rot, roles, provider):
      return "sess", datetime.now(timezone.utc) + timedelta(hours=1)
    async def get_user_roles(self, guid, refresh=False):
      return [], 0

  class DummyState:
    def __init__(self):
      self.db = DummyDb()
      self.auth = DummyAuth()

  class DummyRequest:
    def __init__(self):
      self.app = SimpleNamespace(state=DummyState())
      self.headers = {"user-agent": "tester"}
      self.client = SimpleNamespace(host="127.0.0.1")
    async def json(self):
      return {"provider": "google", "id_token": "id", "access_token": "acc"}

  req = DummyRequest()
  resp = asyncio.run(auth_session_get_token_v1(req))
  data = json.loads(resp.body)
  profile = data["payload"]["profile"]
  assert profile["display_name"] == "DB"
  assert profile["email"] == "db@example.com"
