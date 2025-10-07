import types, sys, asyncio, pathlib, importlib

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
support_pkg = importlib.import_module("rpc.support.users")
importlib.reload(account_mod)
importlib.reload(support_pkg)


class DummyUserAdmin:
  def __init__(self):
    self.calls = []

  async def get_displayname(self, guid):
    self.calls.append(("get_displayname", guid))
    return "User"

  async def get_credits(self, guid):
    self.calls.append(("get_credits", guid))
    return 5

  async def set_credits(self, guid, credits):
    self.calls.append(("set_credits", guid, credits))

  async def reset_display(self, guid):
    self.calls.append(("reset_display", guid))



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


def test_support_dispatchers_reference_account_services():
  assert support_pkg.DISPATCHERS[("get_displayname", "1")] is account_mod.account_user_get_displayname_v1
  assert support_pkg.DISPATCHERS[("get_credits", "1")] is account_mod.account_user_get_credits_v1
  assert support_pkg.DISPATCHERS[("set_credits", "1")] is account_mod.account_user_set_credits_v1
  assert support_pkg.DISPATCHERS[("reset_display", "1")] is account_mod.account_user_reset_display_v1



def test_account_user_services_call_user_admin():
  ua = DummyUserAdmin()
  state = DummyState(ua)
  req = DummyRequest(state)

  orig_helpers_unbox = helpers.unbox_request
  orig_account_unbox = account_mod.unbox_request

  try:
    async def fake_get_displayname(request):
      return _make_rpc("urn:support:users:get_displayname:1", {"userGuid": "u1"}), None, None

    helpers.unbox_request = fake_get_displayname
    account_mod.unbox_request = fake_get_displayname
    resp = asyncio.run(account_mod.account_user_get_displayname_v1(req))
    assert ("get_displayname", "u1") in ua.calls
    assert isinstance(resp, RPCResponse)

    async def fake_get_credits(request):
      return _make_rpc("urn:support:users:get_credits:1", {"userGuid": "u1"}), None, None

    helpers.unbox_request = fake_get_credits
    account_mod.unbox_request = fake_get_credits
    resp2 = asyncio.run(account_mod.account_user_get_credits_v1(req))
    assert ("get_credits", "u1") in ua.calls
    assert isinstance(resp2, RPCResponse)

    async def fake_set_credits(request):
      return _make_rpc(
        "urn:support:users:set_credits:1", {"userGuid": "u1", "credits": 5}
      ), None, None

    helpers.unbox_request = fake_set_credits
    account_mod.unbox_request = fake_set_credits
    asyncio.run(account_mod.account_user_set_credits_v1(req))
    assert ("set_credits", "u1", 5) in ua.calls

    async def fake_reset_display(request):
      return _make_rpc("urn:support:users:reset_display:1", {"userGuid": "u1"}), None, None

    helpers.unbox_request = fake_reset_display
    account_mod.unbox_request = fake_reset_display
    asyncio.run(account_mod.account_user_reset_display_v1(req))
    assert ("reset_display", "u1") in ua.calls
  finally:
    helpers.unbox_request = orig_helpers_unbox
    account_mod.unbox_request = orig_account_unbox

