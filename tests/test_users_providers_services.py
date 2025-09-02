import asyncio
import importlib.util
import pathlib
import sys
import types
from types import SimpleNamespace
import uuid
from datetime import datetime, timezone, timedelta
from server.modules.providers.auth.google_provider import GoogleAuthProvider
from server.modules.providers.auth.microsoft_provider import MicrosoftAuthProvider

import pytest
from fastapi import HTTPException

# stub rpc package
pkg = types.ModuleType("rpc")
pkg.__path__ = [str(pathlib.Path(__file__).resolve().parent.parent / "rpc")]
sys.modules.setdefault("rpc", pkg)

spec = importlib.util.spec_from_file_location("server.models", "server/models.py")
models = importlib.util.module_from_spec(spec)
spec.loader.exec_module(models)
RPCRequest = models.RPCRequest
RPCResponse = models.RPCResponse
sys.modules["server.models"] = models

# stub server packages
server_pkg = types.ModuleType("server")
modules_pkg = types.ModuleType("server.modules")
db_module_pkg = types.ModuleType("server.modules.db_module")
class DbModule: ...
db_module_pkg.DbModule = DbModule
modules_pkg.db_module = db_module_pkg
server_pkg.modules = modules_pkg
models_pkg = types.ModuleType("server.models")
class AuthContext:
  def __init__(self, **data):
    self.role_mask = 0
    self.__dict__.update(data)
models_pkg.AuthContext = AuthContext
server_pkg.models = models_pkg

sys.modules.setdefault("server", server_pkg)
sys.modules.setdefault("server.modules", modules_pkg)
sys.modules.setdefault("server.modules.db_module", db_module_pkg)
sys.modules.setdefault("server.models", models_pkg)

# load real helpers then override for service import
real_helpers_spec = importlib.util.spec_from_file_location("rpc.helpers", "rpc/helpers.py")
real_helpers = importlib.util.module_from_spec(real_helpers_spec)
real_helpers_spec.loader.exec_module(real_helpers)

helpers_stub = types.ModuleType("rpc.helpers")
async def _stub(request):
  raise NotImplementedError
helpers_stub.unbox_request = _stub
sys.modules["rpc.helpers"] = helpers_stub

# import services with stubbed helpers
svc_spec = importlib.util.spec_from_file_location("rpc.users.providers.services", "rpc/users/providers/services.py")
svc_mod = importlib.util.module_from_spec(svc_spec)
svc_spec.loader.exec_module(svc_mod)

# restore real helpers
sys.modules["rpc.helpers"] = real_helpers

users_providers_set_provider_v1 = svc_mod.users_providers_set_provider_v1
users_providers_link_provider_v1 = svc_mod.users_providers_link_provider_v1
users_providers_unlink_provider_v1 = svc_mod.users_providers_unlink_provider_v1

class DBRes:
  def __init__(self, rows=None, rowcount=0):
    self.rows = rows or []
    self.rowcount = rowcount

class DummyDb:
  def __init__(self):
    self.calls = []
  async def run(self, op, args):
    self.calls.append((op, args))
    return DBRes()

class DummyState:
  def __init__(self, db, auth=None, env=None):
    self.db = db
    if auth is not None:
      self.auth = auth
    if env is not None:
      self.env = env

class DummyApp:
  def __init__(self, state):
    self.state = state

class DummyRequest:
  def __init__(self, state):
    self.app = DummyApp(state)
    self.headers = {}


def test_set_provider_calls_db():
  async def fake_get(request):
    rpc = RPCRequest(
      op="urn:users:providers:set_provider:1",
      payload={"provider": "microsoft", "id_token": "id", "access_token": "acc"},
      version=1,
    )
    return rpc, SimpleNamespace(user_guid="u1"), None
  svc_mod.unbox_request = fake_get
  db = DummyDb()
  class DummyAuth:
    def __init__(self):
      self.providers = {"microsoft": SimpleNamespace(audience="client")}
    async def handle_auth_login(self, provider, id_token, access_token):
      return "pid", {"email": "e", "username": "n"}, {}
  req = DummyRequest(DummyState(db, auth=DummyAuth()))
  resp = asyncio.run(users_providers_set_provider_v1(req))
  assert ("urn:users:providers:set_provider:1", {"guid": "u1", "provider": "microsoft"}) in db.calls
  assert (
    "urn:users:profile:update_if_unedited:1",
    {"guid": "u1", "email": "e", "display_name": "n"},
  ) in db.calls
  assert isinstance(resp, RPCResponse)
  assert resp.payload["provider"] == "microsoft"


def test_set_provider_missing_provider_raises():
  async def fake_get(request):
    rpc = RPCRequest(op="urn:users:providers:set_provider:1", payload={}, version=1)
    return rpc, SimpleNamespace(user_guid="u1"), None
  svc_mod.unbox_request = fake_get
  db = DummyDb()
  req = DummyRequest(DummyState(db))
  with pytest.raises(HTTPException) as exc:
    asyncio.run(users_providers_set_provider_v1(req))
  assert exc.value.status_code == 400


def test_link_provider_google_normalizes_identifier():
  async def fake_get(request):
    rpc = RPCRequest(
      op="urn:users:providers:link_provider:1",
      payload={"provider": "google", "code": "authcode"},
      version=1,
    )
    return rpc, SimpleNamespace(user_guid="u1"), None
  svc_mod.unbox_request = fake_get

  async def fake_exchange(code, client_id, client_secret, redirect_uri):
    return "id", "acc"
  svc_mod.exchange_code_for_tokens = fake_exchange

  class DummyAuth:
    def __init__(self):
      provider = GoogleAuthProvider(api_id="client-id", jwks_uri="uri", jwks_expiry=timedelta(minutes=1))

      async def fake_fetch_jwks():
        provider._jwks = {"keys": []}
        provider._jwks_fetched_at = datetime.now(timezone.utc)

      provider.fetch_jwks = fake_fetch_jwks
      asyncio.run(provider.startup())
      self.providers = {"google": provider}

    async def handle_auth_login(self, provider, id_token, access_token):
      return "google-id", {}, {}

  class DummyDb:
    def __init__(self):
      self.calls = []
    async def run(self, op, args):
      self.calls.append((op, args))
      if op == "urn:system:config:get_config:1":
        key = args["key"]
        if key == "Hostname":
          return DBRes(rows=[{"value": "redirect"}])
      return DBRes()

    async def get_google_api_secret(self):
      return "secret"

  class DummyEnv:
    async def on_ready(self):
      return None
    def get(self, k):
      assert k == "GOOGLE_AUTH_SECRET"
      return "secret"

  db = DummyDb()
  auth = DummyAuth()
  env = DummyEnv()
  req = DummyRequest(DummyState(db, auth, env))
  asyncio.run(users_providers_link_provider_v1(req))
  expected = str(uuid.uuid5(uuid.NAMESPACE_URL, "google-id"))
  assert ("urn:users:providers:link_provider:1", {"guid": "u1", "provider": "google", "provider_identifier": expected}) in db.calls
  asyncio.run(auth.providers["google"].shutdown())


def test_link_provider_microsoft_normalizes_identifier():
  async def fake_get(request):
    rpc = RPCRequest(
      op="urn:users:providers:link_provider:1",
      payload={"provider": "microsoft", "id_token": "id", "access_token": "acc"},
      version=1,
    )
    return rpc, SimpleNamespace(user_guid="u1"), None
  svc_mod.unbox_request = fake_get

  class DummyAuth:
    def __init__(self):
      provider = MicrosoftAuthProvider(api_id="client-id", jwks_uri="uri", jwks_expiry=timedelta(minutes=1))

      async def fake_fetch_jwks():
        provider._jwks = {"keys": []}
        provider._jwks_fetched_at = datetime.now(timezone.utc)

      provider.fetch_jwks = fake_fetch_jwks
      asyncio.run(provider.startup())
      self.providers = {"microsoft": provider}

    async def handle_auth_login(self, provider, id_token, access_token):
      return "ms-id", {}, {}

  class DummyDb:
    def __init__(self):
      self.calls = []
    async def run(self, op, args):
      self.calls.append((op, args))
      return DBRes()

  db = DummyDb()
  auth = DummyAuth()
  req = DummyRequest(DummyState(db, auth))
  asyncio.run(users_providers_link_provider_v1(req))
  expected = str(uuid.uuid5(uuid.NAMESPACE_URL, "ms-id"))
  assert ("urn:users:providers:link_provider:1", {"guid": "u1", "provider": "microsoft", "provider_identifier": expected}) in db.calls
  asyncio.run(auth.providers["microsoft"].shutdown())


def test_unlink_non_default_provider_retains_tokens():
  async def fake_get(request):
    rpc = RPCRequest(op="urn:users:providers:unlink_provider:1", payload={"provider": "google"}, version=1)
    return rpc, SimpleNamespace(user_guid="u1"), None
  svc_mod.unbox_request = fake_get

  class LocalDb(DummyDb):
    async def run(self, op, args):
      self.calls.append((op, args))
      if op == "urn:users:profile:get_profile:1":
        return DBRes(rows=[{"default_provider": "microsoft"}])
      if op == "urn:users:providers:unlink_provider:1":
        return DBRes(rows=[{"providers_remaining": 1}], rowcount=1)
      return DBRes()

  db = LocalDb()
  req = DummyRequest(DummyState(db))
  asyncio.run(users_providers_unlink_provider_v1(req))
  assert ("db:auth:session:revoke_provider_tokens:1", {"guid": "u1", "provider": "google"}) not in db.calls
  assert not any(op == "db:auth:session:revoke_all_device_tokens:1" for op, _ in db.calls)
  assert not any(op == "urn:users:providers:soft_delete_account:1" for op, _ in db.calls)



def test_unlink_default_provider_without_new_default_raises():
  async def fake_get(request):
    rpc = RPCRequest(op="urn:users:providers:unlink_provider:1", payload={"provider": "google"}, version=1)
    return rpc, SimpleNamespace(user_guid="u1"), None
  svc_mod.unbox_request = fake_get

  class LocalDb(DummyDb):
    async def run(self, op, args):
      self.calls.append((op, args))
      if op == "urn:users:profile:get_profile:1":
        return DBRes(rows=[{"default_provider": "google"}])
      if op == "urn:users:providers:unlink_provider:1":
        return DBRes(rows=[{"providers_remaining": 1}], rowcount=1)
      return DBRes()

  db = LocalDb()
  req = DummyRequest(DummyState(db))
  with pytest.raises(HTTPException):
    asyncio.run(users_providers_unlink_provider_v1(req))
  assert not any(op == "urn:users:providers:set_provider:1" for op, _ in db.calls)
  assert not any(op == "db:auth:session:revoke_provider_tokens:1" for op, _ in db.calls)


def test_unlink_default_provider_sets_new_default_and_revokes_tokens():
  async def fake_get(request):
    rpc = RPCRequest(op="urn:users:providers:unlink_provider:1", payload={"provider": "google", "new_default": "microsoft"}, version=1)
    return rpc, SimpleNamespace(user_guid="u1"), None
  svc_mod.unbox_request = fake_get

  class LocalDb(DummyDb):
    async def run(self, op, args):
      self.calls.append((op, args))
      if op == "urn:users:profile:get_profile:1":
        return DBRes(rows=[{"default_provider": "google"}])
      if op == "urn:users:providers:unlink_provider:1":
        return DBRes(rows=[{"providers_remaining": 1}], rowcount=1)
      return DBRes()

  db = LocalDb()
  req = DummyRequest(DummyState(db))
  asyncio.run(users_providers_unlink_provider_v1(req))
  assert ("urn:users:providers:set_provider:1", {"guid": "u1", "provider": "microsoft"}) in db.calls
  assert ("db:auth:session:revoke_provider_tokens:1", {"guid": "u1", "provider": "google"}) in db.calls
  assert not any(op == "db:auth:session:revoke_all_device_tokens:1" for op, _ in db.calls)
  assert not any(op == "urn:users:providers:soft_delete_account:1" for op, _ in db.calls)


def test_unlink_last_provider_soft_deletes_and_revokes():
  async def fake_get(request):
    rpc = RPCRequest(op="urn:users:providers:unlink_provider:1", payload={"provider": "google"}, version=1)
    return rpc, SimpleNamespace(user_guid="u1"), None
  svc_mod.unbox_request = fake_get

  class LocalDb(DummyDb):
    async def run(self, op, args):
      self.calls.append((op, args))
      if op == "urn:users:profile:get_profile:1":
        return DBRes(rows=[{"default_provider": "google"}])
      if op == "urn:users:providers:unlink_provider:1":
        return DBRes(rows=[{"providers_remaining": 0}], rowcount=1)
      if op == "urn:auth:providers:unlink_last_provider:1":
        return DBRes([], 1)
      return DBRes()

  db = LocalDb()
  req = DummyRequest(DummyState(db))
  asyncio.run(users_providers_unlink_provider_v1(req))
  assert ("urn:auth:providers:unlink_last_provider:1", {"guid": "u1", "provider": "google"}) in db.calls
  assert not any(op == "db:auth:session:revoke_provider_tokens:1" for op, _ in db.calls)

