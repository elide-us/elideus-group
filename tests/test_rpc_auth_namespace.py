import asyncio
from fastapi import FastAPI, Request
from server.modules import ModuleRegistry, BaseModule
from server.modules.auth_module import AuthModule
from server.modules.env_module import EnvironmentModule
from rpc.handler import handle_rpc_request
from rpc.models import RPCRequest


class DummyModule(BaseModule):
  async def startup(self):
    pass

  async def shutdown(self):
    pass


def setup_modules(app: FastAPI) -> ModuleRegistry:
  app.state.env = EnvironmentModule(app)
  app.state.discord = DummyModule(app)
  app.state.database = DummyModule(app)
  app.state.auth = AuthModule(app)
  modules = ModuleRegistry(app)
  app.state.modules = modules
  return modules


def test_ms_user_login_stub(monkeypatch):
  app = FastAPI()
  modules = setup_modules(app)
  request = Request({"type": "http", "app": app})

  async def fake_handle(self, id_token, access_token):
    return "guid", {"username": "tester", "email": "tester@example.com"}

  monkeypatch.setattr(AuthModule, "handle_ms_auth_login", fake_handle)
  monkeypatch.setattr(AuthModule, "make_bearer_token", lambda self, guid: "stub-token")

  rpc_request = RPCRequest(
    op="urn:auth:microsoft:user_login:1",
    payload={"idToken": "id", "accessToken": "access"}
  )
  response = asyncio.run(handle_rpc_request(rpc_request, request))

  assert response.op == "urn:auth:microsoft:login_data:1"
  assert response.payload.username == "tester"
  assert response.payload.email == "tester@example.com"
