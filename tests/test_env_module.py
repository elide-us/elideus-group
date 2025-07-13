import pytest
from server.modules.env_module import EnvironmentModule
from fastapi import FastAPI


def test_env_loads(app_with_env):
  env = app_with_env.state.env
  assert env.get("VERSION") == "1"
  assert env.get_as_int("DISCORD_SYSCHAN") == 1

def test_env_missing_key(app_with_env):
  env = app_with_env.state.env
  with pytest.raises(RuntimeError):
    env.get("NOPE")

def test_env_defaults(monkeypatch):
  monkeypatch.delenv("HOSTNAME", raising=False)
  app = FastAPI()
  env = EnvironmentModule(app)
  assert env.get("HOSTNAME") == "MISSING_ENV_HOSTNAME"

def test_getenv_required(monkeypatch):
  app = FastAPI()
  env = EnvironmentModule(app)
  with pytest.raises(RuntimeError):
    env._getenv("NEW_VAR")

