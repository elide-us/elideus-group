import pytest
from fastapi import FastAPI
from server.modules.env_module import EnvironmentModule

@pytest.fixture
def app_with_env(monkeypatch):
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
  return app
