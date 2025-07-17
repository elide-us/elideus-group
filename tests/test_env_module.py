import pytest
from server.modules.env_module import EnvironmentModule
from fastapi import FastAPI


def test_env_loads(app_with_env):
  env = app_with_env.state.env
  assert env.get("DISCORD_SECRET") == "secret"
  assert env.get("JWT_SECRET") == "jwt"

def test_env_missing_key(app_with_env):
  env = app_with_env.state.env
  with pytest.raises(RuntimeError):
    env.get("VERSION")

def test_env_defaults(monkeypatch):
  monkeypatch.delenv("MS_API_ID", raising=False)
  app = FastAPI()
  env = EnvironmentModule(app)
  with pytest.raises(RuntimeError):
    env.get("MS_API_ID")

def test_getenv_required(monkeypatch):
  app = FastAPI()
  env = EnvironmentModule(app)
  with pytest.raises(RuntimeError):
    env._getenv("NEW_VAR")

