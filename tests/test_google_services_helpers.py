from types import SimpleNamespace
from datetime import datetime, timezone, timedelta
import asyncio
import importlib.util
import pathlib
import sys
import types
import uuid
import logging

import pytest
from types import SimpleNamespace

# stub rpc and server packages
root_path = pathlib.Path(__file__).resolve().parent.parent
rpc_pkg = types.ModuleType("rpc")
rpc_pkg.__path__ = [str(root_path / "rpc")]
sys.modules["rpc"] = rpc_pkg

spec_models = importlib.util.spec_from_file_location(
  "rpc.models", root_path / "rpc/models.py"
)
models_mod = importlib.util.module_from_spec(spec_models)
spec_models.loader.exec_module(models_mod)
sys.modules["rpc.models"] = models_mod

helpers_stub = types.ModuleType("rpc.helpers")
async def _stub(request):
  raise NotImplementedError
helpers_stub.unbox_request = _stub
sys.modules["rpc.helpers"] = helpers_stub

server_pkg = types.ModuleType("server")
sys.modules["server"] = server_pkg
modules_pkg = types.ModuleType("server.modules")
sys.modules["server.modules"] = modules_pkg
auth_pkg = types.ModuleType("server.modules.auth_module")
class AuthModule: ...
auth_pkg.AuthModule = AuthModule
modules_pkg.auth_module = auth_pkg
sys.modules["server.modules.auth_module"] = auth_pkg
db_pkg = types.ModuleType("server.modules.db_module")
class DbModule: ...
db_pkg.DbModule = DbModule
modules_pkg.db_module = db_pkg
sys.modules["server.modules.db_module"] = db_pkg

auth_ns = types.ModuleType("rpc.auth")
auth_ns.__path__ = [str(root_path / "rpc/auth")]
sys.modules["rpc.auth"] = auth_ns
google_ns = types.ModuleType("rpc.auth.google")
google_ns.__path__ = [str(root_path / "rpc/auth/google")]
sys.modules["rpc.auth.google"] = google_ns

spec_services = importlib.util.spec_from_file_location(
  "rpc.auth.google.services", root_path / "rpc/auth/google/services.py"
)
services_mod = importlib.util.module_from_spec(spec_services)
sys.modules["rpc.auth.google.services"] = services_mod
spec_services.loader.exec_module(services_mod)

extract_identifiers = services_mod.extract_identifiers
lookup_user = services_mod.lookup_user
create_session = services_mod.create_session


def test_extract_identifiers_bad_base(caplog):
  caplog.set_level(logging.ERROR)
  ids = extract_identifiers("not-a-uuid", {})
  assert "not-a-uuid" in ids
  assert len(ids) == 1
  assert any("home_account_id generation failed" in r.message for r in caplog.records)


class DummyDb:
  def __init__(self):
    self.calls = []
  async def run(self, op, args):
    self.calls.append((op, args))
    return SimpleNamespace(rows=[])


def test_lookup_user_skips_invalid_identifier():
  db = DummyDb()
  user = asyncio.run(lookup_user(db, "google", ["bad-id"]))
  assert user is None
  assert db.calls == []


class DummyAuth:
  def make_rotation_token(self, guid):
    return "rot", datetime.now(timezone.utc) + timedelta(hours=1)
  def make_session_token(self, guid, rot, roles, provider):
    return "sess", datetime.now(timezone.utc) + timedelta(hours=1)
  async def get_user_roles(self, guid, refresh=False):
    return [], 0


def test_create_session_handles_missing_roles():
  db = DummyDb()
  auth = DummyAuth()
  token, exp = asyncio.run(
    create_session(auth, db, str(uuid.uuid4()), "google", None, None, None)
  )
  assert token == "sess"
  ops = [op for op, _ in db.calls]
  assert "db:auth:session:create_session:1" in ops
  args = [a for op, a in db.calls if op == "db:auth:session:create_session:1"][0]
  assert args["provider"] == "google"
