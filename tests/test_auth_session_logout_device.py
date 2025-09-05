import importlib.util
import types
import sys
import asyncio
import pytest
from types import SimpleNamespace
from fastapi import HTTPException


class DBRes:
  def __init__(self, rows=None, rowcount=0):
    self.rows = rows or []
    self.rowcount = rowcount

class DummyDb:
  def __init__(self):
    self.calls = []
    self.revoked = False
  async def run(self, op, args):
    self.calls.append((op, args))
    if op == "db:auth:session:revoke_device_token:1":
      self.revoked = True
      return DBRes(rowcount=1)
    if op == "db:auth:session:get_by_access_token:1":
      if self.revoked:
        return DBRes([{"revoked_at": "2024-01-01T00:00:00Z"}], 1)
      return DBRes([{"revoked_at": None}], 1)
    if op == "db:users:session:get_rotkey:1":
      return DBRes([{"rotkey": "rot-token", "provider_name": "microsoft"}], 1)
    if op == "db:auth:session:create_session:1":
      return DBRes([{ "session_guid": "sess-guid", "device_guid": "dev-guid" }], 1)
    if op == "db:auth:session:update_device_token:1":
      return DBRes(rowcount=1)
    return DBRes()

class DummyAuth:
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
    self.headers = {"authorization": "Bearer tok", "user-agent": "ua"}
    self.client = SimpleNamespace(host="127.0.0.1")
    self.cookies = {"rotation_token": "rot-token"}
    self.op = ""
  async def json(self):
    return {"fingerprint": "fp"}


def _setup(monkeypatch):
  spec = importlib.util.spec_from_file_location("server.models", "server/models.py")
  models = importlib.util.module_from_spec(spec)
  spec.loader.exec_module(models)
  sys.modules["server.models"] = models
  RPCRequest = models.RPCRequest
  RPCResponse = models.RPCResponse

  helpers = types.ModuleType("rpc.helpers")
  async def fake_unbox(req):
    rpc = RPCRequest(op=req.op, payload=None, version=1)
    return rpc, SimpleNamespace(user_guid="user-guid", claims={}), None
  helpers.unbox_request = fake_unbox
  sys.modules["rpc.helpers"] = helpers

  sys.modules.setdefault("server", types.ModuleType("server"))
  sys.modules.setdefault("server.modules", types.ModuleType("server.modules"))
  db_mod = types.ModuleType("server.modules.db_module")
  class DbModule: ...
  db_mod.DbModule = DbModule
  sys.modules["server.modules.db_module"] = db_mod

  auth_mod = types.ModuleType("server.modules.auth_module")
  class AuthModule: ...
  auth_mod.AuthModule = AuthModule
  sys.modules["server.modules.auth_module"] = auth_mod

  svc_spec = importlib.util.spec_from_file_location("rpc.auth.session.services", "rpc/auth/session/services.py")
  svc_mod = importlib.util.module_from_spec(svc_spec)
  svc_spec.loader.exec_module(svc_mod)
  return svc_mod, RPCResponse


def test_logout_device_revokes_token(monkeypatch):
  svc_mod, RPCResponse = _setup(monkeypatch)
  req = DummyRequest()
  req.op = "urn:auth:session:logout_device:1"
  resp = asyncio.run(svc_mod.auth_session_logout_device_v1(req))
  assert isinstance(resp, RPCResponse)
  assert ("db:auth:session:revoke_device_token:1", {"access_token": "tok"}) in req.app.state.db.calls
  req.op = "urn:auth:session:get_session:1"
  with pytest.raises(HTTPException):
    asyncio.run(svc_mod.auth_session_get_session_v1(req))


def test_logout_device_allows_refresh(monkeypatch):
  svc_mod, RPCResponse = _setup(monkeypatch)
  req = DummyRequest()
  req.op = "urn:auth:session:logout_device:1"
  asyncio.run(svc_mod.auth_session_logout_device_v1(req))
  req.op = "urn:auth:session:refresh_token:1"
  resp = asyncio.run(svc_mod.auth_session_refresh_token_v1(req))
  assert isinstance(resp, RPCResponse)
  assert resp.payload["token"] == "new-token"
