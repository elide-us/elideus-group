import types, sys, importlib.util, asyncio
import pytest
from types import SimpleNamespace
from fastapi import HTTPException


def _setup():
  spec = importlib.util.spec_from_file_location("server.models", "server/models.py")
  models = importlib.util.module_from_spec(spec)
  spec.loader.exec_module(models)
  sys.modules["server.models"] = models
  RPCRequest = models.RPCRequest
  RPCResponse = models.RPCResponse

  helpers = types.ModuleType("rpc.helpers")
  async def fake_unbox(req):
    payload = {"fingerprint": "fp"} if req.op == "urn:auth:session:refresh_token:1" else None
    rpc = RPCRequest(op=req.op, payload=payload, version=1)
    return rpc, SimpleNamespace(user_guid="user-guid", claims={}), None
  helpers.unbox_request = fake_unbox
  sys.modules["rpc.helpers"] = helpers

  class DummySession:
    def __init__(self):
      self.revoked = False
    async def logout_device(self, token):
      self.revoked = True
    async def get_session(self, token, ip_address, user_agent):
      if self.revoked:
        raise HTTPException(status_code=401, detail="Session revoked")
      return {}
    async def refresh_token(self, rotation_token, fingerprint, user_agent, ip_address):
      return "new-token"

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
      self.cookies = {"rotation_token": "rot-token"}
      self.op = ""
    async def json(self):
      return {"fingerprint": "fp"}

  svc_spec = importlib.util.spec_from_file_location("rpc.auth.session.services", "rpc/auth/session/services.py")
  svc_mod = importlib.util.module_from_spec(svc_spec)
  svc_spec.loader.exec_module(svc_mod)
  return svc_mod, RPCResponse, DummyRequest


def test_logout_device_revokes_token(monkeypatch):
  svc_mod, RPCResponse, DummyRequest = _setup()
  req = DummyRequest()
  req.op = "urn:auth:session:logout_device:1"
  resp = asyncio.run(svc_mod.auth_session_logout_device_v1(req))
  assert isinstance(resp, RPCResponse)
  req.op = "urn:auth:session:get_session:1"
  with pytest.raises(HTTPException):
    asyncio.run(svc_mod.auth_session_get_session_v1(req))


def test_logout_device_allows_refresh(monkeypatch):
  svc_mod, RPCResponse, DummyRequest = _setup()
  req = DummyRequest()
  req.op = "urn:auth:session:logout_device:1"
  asyncio.run(svc_mod.auth_session_logout_device_v1(req))
  req.op = "urn:auth:session:refresh_token:1"
  resp = asyncio.run(svc_mod.auth_session_refresh_token_v1(req))
  assert isinstance(resp, RPCResponse)
  assert resp.payload["token"] == "new-token"
