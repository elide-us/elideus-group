import types, sys, asyncio, pathlib, importlib

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

account_user_get_displayname_v1 = svc_mod.account_user_get_displayname_v1
account_user_get_credits_v1 = svc_mod.account_user_get_credits_v1
account_user_set_credits_v1 = svc_mod.account_user_set_credits_v1
account_user_reset_display_v1 = svc_mod.account_user_reset_display_v1
account_user_create_folder_v1 = svc_mod.account_user_create_folder_v1


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



class DummyStorage:
  def __init__(self):
    self.calls = []

  async def create_user_folder(self, guid, path):
    self.calls.append((guid, path))


class DummyState:
  def __init__(self, user_admin=None, storage=None):
    self.user_admin = user_admin
    self.storage = storage

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
  storage = DummyStorage()
  state = DummyState(ua, storage)
  req = DummyRequest(state)

  async def fake_get_displayname(request):
    return _make_rpc("urn:account:user:get_displayname:1", {"userGuid": "u1"}), None, None
  helpers.unbox_request = fake_get_displayname
  svc_mod.unbox_request = fake_get_displayname
  resp = asyncio.run(account_user_get_displayname_v1(req))
  assert ("get_displayname", "u1") in ua.calls
  assert resp.op == "urn:account:user:get_displayname:1"

  async def fake_get_credits(request):
    return _make_rpc("urn:account:user:get_credits:1", {"userGuid": "u1"}), None, None
  helpers.unbox_request = fake_get_credits
  svc_mod.unbox_request = fake_get_credits
  resp2 = asyncio.run(account_user_get_credits_v1(req))
  assert ("get_credits", "u1") in ua.calls
  assert resp2.op == "urn:account:user:get_credits:1"

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

  async def fake_create_folder(request):
    return _make_rpc(
      "urn:account:user:create_folder:1",
      {"userGuid": "u1", "path": "docs"},
    ), None, None
  helpers.unbox_request = fake_create_folder
  svc_mod.unbox_request = fake_create_folder
  asyncio.run(account_user_create_folder_v1(req))
  assert ("u1", "docs") in storage.calls

