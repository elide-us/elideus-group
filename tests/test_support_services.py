import types, sys, asyncio, pathlib, importlib
from types import SimpleNamespace

root_path = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root_path))

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

account_mod = importlib.import_module("rpc.account.user.services")
support_mod = importlib.import_module("rpc.support.users.services")
importlib.reload(account_mod)
importlib.reload(support_mod)


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


def test_support_routes_reuse_account_routes():
  calls = []

  async def fake_profile(request):
    calls.append("get_profile")
    return RPCResponse(op="o", payload={}, version=1)

  orig_profile = account_mod.account_user_get_profile_v1
  account_mod.account_user_get_profile_v1 = fake_profile
  asyncio.run(support_mod.support_users_get_profile_v1(None))
  account_mod.account_user_get_profile_v1 = orig_profile
  assert "get_profile" in calls

  async def fake_set_credits(request):
    calls.append("set_credits")
    return RPCResponse(op="o", payload={}, version=1)

  orig_set_credits = account_mod.account_user_set_credits_v1
  account_mod.account_user_set_credits_v1 = fake_set_credits
  asyncio.run(support_mod.support_users_set_credits_v1(None))
  account_mod.account_user_set_credits_v1 = orig_set_credits
  assert "set_credits" in calls

  async def fake_reset_display(request):
    calls.append("reset_display")
    return RPCResponse(op="o", payload={}, version=1)

  orig_reset_display = account_mod.account_user_reset_display_v1
  account_mod.account_user_reset_display_v1 = fake_reset_display
  asyncio.run(support_mod.support_users_reset_display_v1(None))
  account_mod.account_user_reset_display_v1 = orig_reset_display
  assert "reset_display" in calls

  async def fake_enable_storage(request):
    calls.append("enable_storage")
    return RPCResponse(op="o", payload={}, version=1)

  orig_enable_storage = account_mod.account_user_enable_storage_v1
  account_mod.account_user_enable_storage_v1 = fake_enable_storage
  asyncio.run(support_mod.support_users_enable_storage_v1(None))
  account_mod.account_user_enable_storage_v1 = orig_enable_storage
  assert "enable_storage" in calls

  async def fake_check_storage(request):
    calls.append("check_storage")
    return RPCResponse(op="o", payload={}, version=1)

  orig_check_storage = account_mod.account_user_check_storage_v1
  account_mod.account_user_check_storage_v1 = fake_check_storage
  asyncio.run(support_mod.support_users_check_storage_v1(None))
  account_mod.account_user_check_storage_v1 = orig_check_storage
  assert "check_storage" in calls


def test_support_users_calls_user_admin():
  ua = DummyUserAdmin()
  state = DummyState(ua)
  req = DummyRequest(state)

  async def fake_get_profile(request):
    return _make_rpc("urn:support:users:get_profile:1", {"userGuid": "u1"}), None, None
  helpers.unbox_request = fake_get_profile
  account_mod.unbox_request = fake_get_profile
  resp = asyncio.run(support_mod.support_users_get_profile_v1(req))
  assert ("get_profile", "u1") in ua.calls
  assert isinstance(resp, RPCResponse)

  async def fake_set_credits(request):
    return _make_rpc("urn:support:users:set_credits:1", {"userGuid": "u1", "credits": 5}), None, None
  helpers.unbox_request = fake_set_credits
  account_mod.unbox_request = fake_set_credits
  asyncio.run(support_mod.support_users_set_credits_v1(req))
  assert ("set_credits", "u1", 5) in ua.calls

  async def fake_reset_display(request):
    return _make_rpc("urn:support:users:reset_display:1", {"userGuid": "u1"}), None, None
  helpers.unbox_request = fake_reset_display
  account_mod.unbox_request = fake_reset_display
  asyncio.run(support_mod.support_users_reset_display_v1(req))
  assert ("reset_display", "u1") in ua.calls

  async def fake_enable_storage(request):
    return _make_rpc("urn:support:users:enable_storage:1", {"userGuid": "u1"}), None, None
  helpers.unbox_request = fake_enable_storage
  account_mod.unbox_request = fake_enable_storage
  asyncio.run(support_mod.support_users_enable_storage_v1(req))
  assert ("enable_storage", "u1") in ua.calls

  async def fake_check_storage(request):
    return _make_rpc("urn:support:users:check_storage:1", {"userGuid": "u1"}), None, None
  helpers.unbox_request = fake_check_storage
  account_mod.unbox_request = fake_check_storage
  resp2 = asyncio.run(support_mod.support_users_check_storage_v1(req))
  assert ("check_storage", "u1") in ua.calls
  assert resp2.payload["exists"] is True
