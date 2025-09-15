import asyncio, importlib.util, sys, types, json
from datetime import datetime, timezone, timedelta
from types import SimpleNamespace

import pytest


def test_auth_session_returns_db_profile(monkeypatch):
  spec = importlib.util.spec_from_file_location("server.models", "server/models.py")
  models = importlib.util.module_from_spec(spec)
  spec.loader.exec_module(models)
  monkeypatch.setitem(sys.modules, "server.models", models)
  monkeypatch.setitem(sys.modules, "rpc", types.ModuleType("rpc"))
  helpers = types.ModuleType("rpc.helpers")
  async def _unbox_request(request):
    raise NotImplementedError
  helpers.unbox_request = _unbox_request
  monkeypatch.setitem(sys.modules, "rpc.helpers", helpers)

  class DummySession:
    def __init__(self):
      self.called = None
    async def issue_token(
      self,
      provider,
      id_token,
      access_token,
      fingerprint,
      user_agent,
      ip_address,
      confirm=None,
      reauth_token=None,
    ):
      self.called = (
        provider,
        id_token,
        access_token,
        fingerprint,
        user_agent,
        ip_address,
        confirm,
        reauth_token,
      )
      return "sess", "rot", datetime.now(timezone.utc) + timedelta(hours=1), {
        "display_name": "DB",
        "email": "db@example.com",
        "credits": 5,
        "profile_image": "img",
      }

  session_mod = DummySession()

  class DummyState:
    def __init__(self):
      self.session = session_mod

  class DummyRequest:
    def __init__(self):
      self.app = SimpleNamespace(state=DummyState())
      self.headers = {"user-agent": "tester"}
      self.client = SimpleNamespace(host="127.0.0.1")
    async def json(self):
      return {"provider": "google", "id_token": "id", "access_token": "acc", "fingerprint": "fp"}

  svc_spec = importlib.util.spec_from_file_location("rpc.auth.session.services", "rpc/auth/session/services.py")
  svc_mod = importlib.util.module_from_spec(svc_spec)
  svc_spec.loader.exec_module(svc_mod)
  auth_session_get_token_v1 = svc_mod.auth_session_get_token_v1

  req = DummyRequest()
  resp = asyncio.run(auth_session_get_token_v1(req))
  data = json.loads(resp.body)
  profile = data["payload"]["profile"]
  assert profile["display_name"] == "DB"
  assert profile["email"] == "db@example.com"
  assert session_mod.called[0] == "google"
