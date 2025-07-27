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
  monkeypatch.setenv("POSTGRES_CONNECTION_STRING", "postgres://user@host/db")
  monkeypatch.setenv("AZURE_SQL_CONNECTION_STRING", "Driver={ODBC};Server=server;Database=db;Uid=user;Pwd=pw;")
  monkeypatch.setenv("AZURE_BLOB_CONNECTION_STRING", "DefaultEndpointsProtocol=https;AccountName=dev;AccountKey=key;")
  app = FastAPI()
  env = EnvironmentModule(app)
  app.state.env = env
  return app
