import asyncio
from types import SimpleNamespace
from uuid import UUID
from fastapi import FastAPI, HTTPException
import pytest

from server.modules.database_module import (
  DatabaseModule,
  _maybe_loads_json,
  _stou,
  _utos,
)
from server.modules.auth_module import AuthModule
from server.modules.discord_module import DiscordModule
from server.modules.env_module import EnvironmentModule

class FakeRecord(dict):
  pass

class FakeConn:
  def __init__(self, data):
    self.data = data
    self.executed = []
  async def fetchrow(self, query, guid):
    credits = self.data.get(guid)
    return {"credits": credits} if credits is not None else None
  async def execute(self, query, *args):
    self.executed.append((query, args))
    self.data[args[1] if len(args) > 1 else args[0]] = args[0]
  def transaction(self):
    class Tx:
      async def __aenter__(self):
        return None
      async def __aexit__(self, exc_type, exc, tb):
        pass
    return Tx()

class FakePool:
  def __init__(self, data):
    self.data = data
  def acquire(self):
    conn = FakeConn(self.data)
    class Ctx:
      async def __aenter__(self):
        return conn
      async def __aexit__(self, exc_type, exc, tb):
        pass
    return Ctx()


def create_env(app: FastAPI):
  env = EnvironmentModule(app)
  env._env["DISCORD_SECRET"] = "secret"
  env._env["DISCORD_SYSCHAN"] = "1"
  return env


def test_maybe_loads_json(monkeypatch):
  import server.modules.database_module as dbm
  monkeypatch.setattr(dbm.asyncpg, "Record", FakeRecord, raising=False)
  assert _maybe_loads_json("{\"a\":1}") == {"a": 1}
  assert _maybe_loads_json("text") == "text"
  rec = FakeRecord({"k": "{\"n\":2}"})
  assert _maybe_loads_json(rec) == {"k": {"n": 2}}
  assert _maybe_loads_json(["{\"x\":3}"]) == [{"x": 3}]


def test_uuid_helpers():
  guid = "11111111-1111-1111-1111-111111111111"
  assert _utos(_stou(guid)) == guid


def test_update_user_credits(monkeypatch):
  app = FastAPI()
  db = DatabaseModule(app)
  guid = UUID("22222222-2222-2222-2222-222222222222")
  db.pool = FakePool({guid: 20})
  res = asyncio.run(db.update_user_credits(10, str(guid)))
  assert res == {"success": True, "guid": str(guid), "credits": 10}
  res = asyncio.run(db.update_user_credits(15, str(guid)))
  assert res["success"] is False
  assert res["error"] == "Insufficient credits"
  res = asyncio.run(db.update_user_credits(1, str(UUID("33333333-3333-3333-3333-333333333333"))))
  assert res["error"] == "User not found"


def test_update_user_credits_purchased():
  app = FastAPI()
  db = DatabaseModule(app)
  guid = UUID("44444444-4444-4444-4444-444444444444")
  db.pool = FakePool({guid: 5})
  res = asyncio.run(db.update_user_credits_purchased(10, str(guid)))
  assert res == {"success": True, "guid": str(guid), "credits": 15}
  res = asyncio.run(db.update_user_credits_purchased(5, str(UUID("55555555-5555-5555-5555-555555555555"))))
  assert res["error"] == "User not found"


def test_make_and_decode_bearer_token(monkeypatch):
  monkeypatch.setenv("JWT_SECRET", "s")
  auth = AuthModule(FastAPI())
  token = auth.make_bearer_token("guid")
  payload = asyncio.run(auth.decode_bearer_token(token))
  assert payload == {"guid": "guid"}


def test_decode_bearer_token_errors(monkeypatch):
  monkeypatch.setenv("JWT_SECRET", "s")
  auth = AuthModule(FastAPI())
  import jose.jwt as jwt
  expired = jwt.encode({"sub": "a", "exp": 0}, auth.jwt_secret, algorithm=auth.jwt_algo_int)
  with pytest.raises(HTTPException):
    asyncio.run(auth.decode_bearer_token(expired))
  bad = jwt.encode({"exp": 9999999999}, auth.jwt_secret, algorithm=auth.jwt_algo_int)
  with pytest.raises(HTTPException):
    asyncio.run(auth.decode_bearer_token(bad))


def test_handle_ms_auth_login(monkeypatch):
  auth = AuthModule(FastAPI())
  async def fake_verify(self, token):
    return {"sub": "g"}
  async def fake_profile(self, at):
    return {"u": 1}
  monkeypatch.setattr(AuthModule, "verify_ms_id_token", fake_verify)
  monkeypatch.setattr(AuthModule, "fetch_ms_user_profile", fake_profile)
  guid, profile = asyncio.run(auth.handle_ms_auth_login("id", "ac"))
  assert guid == "g"
  assert profile == {"u": 1}


def create_discord_module(monkeypatch):
  app = FastAPI()
  env = create_env(app)
  app.state.modules = SimpleNamespace(get_module=lambda k: env)
  module = DiscordModule(app)
  return module


def test_discord_bot_init():
  module = create_discord_module(lambda x: x)
  assert module.bot.command_prefix == '!'
  assert module.bot.intents.message_content is True


def test_discord_startup_shutdown(monkeypatch):
  module = create_discord_module(monkeypatch)
  async def fake_start(self):
    self.started = True
  monkeypatch.setattr(DiscordModule, "_start_discord_bot", fake_start)
  monkeypatch.setattr("server.modules.discord_module.configure_discord_logging", lambda m: setattr(m, "logged", True))
  monkeypatch.setattr("server.modules.discord_module.remove_discord_logging", lambda m: setattr(m, "removed", True))
  async def fake_close():
    module.closed = True
  module.bot.close = fake_close
  asyncio.run(module.startup())
  assert module.secret == "secret"
  assert module.syschan == 1
  assert module.logged
  asyncio.run(module.shutdown())
  assert module.closed
  assert module.removed
