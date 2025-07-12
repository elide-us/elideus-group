import pytest
import asyncio
from fastapi import FastAPI
from types import SimpleNamespace
import server.modules.auth_module as auth_mod
from server.modules.auth_module import AuthModule
from server.modules.env_module import EnvironmentModule

@pytest.fixture
def auth_app(monkeypatch):
  monkeypatch.setenv("VERSION", "1")
  monkeypatch.setenv("HOSTNAME", "host")
  monkeypatch.setenv("REPO", "repo")
  monkeypatch.setenv("DISCORD_SECRET", "secret")
  monkeypatch.setenv("DISCORD_SYSCHAN", "1")
  monkeypatch.setenv("JWT_SECRET", "jwt")
  monkeypatch.setenv("MS_API_ID", "msid")
  monkeypatch.setenv("POSTGRES_CONNECTION_STRING", "postgres://user@host/db")
  app = FastAPI()
  env = EnvironmentModule(app)
  app.state.env = env
  app.state.discord = SimpleNamespace()
  return app

def test_auth_startup(monkeypatch, auth_app):
  async def fake_uri():
    return "url"
  async def fake_jwks(uri):
    return {"keys": []}
  monkeypatch.setattr(auth_mod, "fetch_ms_jwks_uri", fake_uri)
  monkeypatch.setattr(auth_mod, "fetch_ms_jwks", fake_jwks)
  am = AuthModule(auth_app)
  asyncio.run(am.startup())
  assert am.ms_jwks == {"keys": []}
  assert am.ms_api_id == "msid"

def test_verify_ms_id_token_no_keys(auth_app):
  am = AuthModule(auth_app)
  with pytest.raises(Exception):
    asyncio.run(am.verify_ms_id_token("token"))

def test_bearer_token_roundtrip(auth_app):
  am = AuthModule(auth_app)
  token = am.make_bearer_token("uid")
  data = asyncio.run(am.decode_bearer_token(token))
  assert data["guid"] == "uid"

def test_decode_invalid_token(auth_app):
  am = AuthModule(auth_app)
  with pytest.raises(Exception):
    asyncio.run(am.decode_bearer_token("bad"))
