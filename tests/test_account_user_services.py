import types, sys, asyncio, pathlib, importlib
from types import SimpleNamespace

root_path = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root_path))

# stub rpc package to avoid loading full rpc.__init__
rpc_pkg = types.ModuleType("rpc")
rpc_pkg.__path__ = [str(root_path / "rpc")]
rpc_pkg.HANDLERS = {}
sys.modules["rpc"] = rpc_pkg

spec_models = importlib.util.spec_from_file_location(
  "server.models", root_path / "server/models.py"
)
models_mod = importlib.util.module_from_spec(spec_models)
spec_models.loader.exec_module(models_mod)
RPCRequest = models_mod.RPCRequest
RPCResponse = models_mod.RPCResponse
sys.modules["server.models"] = models_mod

spec_helpers = importlib.util.spec_from_file_location(
  "rpc.helpers", root_path / "rpc/helpers.py"
)
helpers = importlib.util.module_from_spec(spec_helpers)
spec_helpers.loader.exec_module(helpers)
sys.modules["rpc.helpers"] = helpers

svc_mod = importlib.import_module("rpc.account.user.services")

account_user_get_profile_v1 = svc_mod.account_user_get_profile_v1
account_user_set_credits_v1 = svc_mod.account_user_set_credits_v1
account_user_reset_display_v1 = svc_mod.account_user_reset_display_v1
account_user_enable_storage_v1 = svc_mod.account_user_enable_storage_v1
account_user_check_storage_v1 = svc_mod.account_user_check_storage_v1


class DummyUserAdmin:
  def __init__(self):
    self.calls = []
    self.profile = SimpleNamespace(model_dump=lambda: {"guid": "u1"})
    self.exists = True

  async def get_profile(self, guid):
    self.calls.append(("get_profile", guid))
    return self.profile

  async def set_credits(self, guid, credits):
    self.calls.append(("set_credits", guid, credits))

  async def reset_display(self, guid):
    self.calls.append(("reset_display", guid))

  async def enable_storage(self, guid):
    self.calls.append(("enable_storage", guid))

  async def check_storage(self, guid):
    self.calls.append(("check_storage", guid))
    return self.exists


class DummyState:
  def __init__(self, user_admin):
    self.user_admin = user_admin

class DummyApp:
  def __init__(self, state):
    self.state = state

class DummyRequest:
  def __init__(self, state):
    self.app = DummyApp(state)
    self.headers = {}


def _make_rpc(op, payload=None):
  return RPCRequest(op=op, payload=payload, version=1)


def test_account_user_calls_user_admin():
  ua = DummyUserAdmin()
  state = DummyState(ua)
  req = DummyRequest(state)

  async def fake_get_profile(request):
    return _make_rpc("urn:account:user:get_profile:1", {"userGuid": "u1"}), None, None
  helpers.unbox_request = fake_get_profile
  svc_mod.unbox_request = fake_get_profile
  resp = asyncio.run(account_user_get_profile_v1(req))
  assert ("get_profile", "u1") in ua.calls
  assert resp.op == "urn:account:user:get_profile:1"

  async def fake_set_credits(request):
    return _make_rpc("urn:account:user:set_credits:1", {"userGuid": "u1", "credits": 5}), None, None
  helpers.unbox_request = fake_set_credits
  svc_mod.unbox_request = fake_set_credits
  asyncio.run(account_user_set_credits_v1(req))
  assert ("set_credits", "u1", 5) in ua.calls

  async def fake_reset_display(request):
    return _make_rpc("urn:account:user:reset_display:1", {"userGuid": "u1"}), None, None
  helpers.unbox_request = fake_reset_display
  svc_mod.unbox_request = fake_reset_display
  asyncio.run(account_user_reset_display_v1(req))
  assert ("reset_display", "u1") in ua.calls

  async def fake_enable_storage(request):
    return _make_rpc("urn:account:user:enable_storage:1", {"userGuid": "u1"}), None, None
  helpers.unbox_request = fake_enable_storage
  svc_mod.unbox_request = fake_enable_storage
  asyncio.run(account_user_enable_storage_v1(req))
  assert ("enable_storage", "u1") in ua.calls

  async def fake_check_storage(request):
    return _make_rpc("urn:account:user:check_storage:1", {"userGuid": "u1"}), None, None
  helpers.unbox_request = fake_check_storage
  svc_mod.unbox_request = fake_check_storage
  resp2 = asyncio.run(account_user_check_storage_v1(req))
  assert ("check_storage", "u1") in ua.calls
  assert resp2.payload["exists"] is True
