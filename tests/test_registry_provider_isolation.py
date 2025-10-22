from __future__ import annotations

import asyncio
import ast
from pathlib import Path
import sys
import types

import pytest
from fastapi import FastAPI

from server.modules.db_module import DbModule
from server.modules.env_module import EnvModule
from server.modules.providers import DbProviderBase
from server.registry.types import DBRequest, DBResponse


REGISTRY_ROOT = Path("server/registry")


def _registry_python_files() -> list[Path]:
  files: list[Path] = []
  for path in REGISTRY_ROOT.rglob("*.py"):
    relative_parts = path.relative_to(REGISTRY_ROOT).parts
    if "providers" in relative_parts:
      continue
    files.append(path)
  return files


def test_registry_modules_do_not_import_provider_dependencies():
  forbidden_prefix = "server.modules.providers"
  for path in _registry_python_files():
    tree = ast.parse(path.read_text(), filename=str(path))
    for node in ast.walk(tree):
      if isinstance(node, ast.Import):
        for alias in node.names:
          assert not alias.name.startswith(forbidden_prefix), (
            f"{path} illegally imports {alias.name}"
          )
      elif isinstance(node, ast.ImportFrom):
        if node.module and node.module.startswith(forbidden_prefix):
          raise AssertionError(f"{path} illegally imports {node.module}")


def test_db_module_uses_provider_specific_configuration(monkeypatch):
  monkeypatch.setenv("DISCORD_SECRET", "x")
  monkeypatch.setenv("DISCORD_AUTH_SECRET", "x")
  monkeypatch.setenv("JWT_SECRET", "x")
  monkeypatch.setenv("GOOGLE_AUTH_SECRET", "x")
  monkeypatch.setenv("DATABASE_PROVIDER", "mock")
  monkeypatch.setenv("AZURE_BLOB_CONNECTION_STRING", "blob")

  def configure(env: EnvModule) -> dict[str, str]:
    return {"dsn": "mock://dsn", "blob": env.get("AZURE_BLOB_CONNECTION_STRING")}

  class MockProvider(DbProviderBase):
    def __init__(self, **config):
      super().__init__(**config)
      self.started = False
      self.stopped = False
      self.requests: list[DBRequest] = []

    async def startup(self) -> None:
      self.started = True

    async def shutdown(self) -> None:
      self.stopped = True

    async def _run(self, request: DBRequest) -> DBResponse:
      self.requests.append(request)
      if request.payload.get("key") == "LoggingLevel":
        return DBResponse(op=request.op, rows=[{"value": "3"}])
      return DBResponse(op=request.op, payload={"payload": request.payload}, rowcount=1)

  mock_provider_module = types.ModuleType("server.modules.providers.database.mock_provider")
  mock_provider_module.MockProvider = MockProvider
  monkeypatch.setitem(
    sys.modules,
    "server.modules.providers.database.mock_provider",
    mock_provider_module,
  )

  mock_registry_module = types.ModuleType("server.registry.providers.mock")
  mock_registry_module.configure = configure
  monkeypatch.setitem(sys.modules, "server.registry.providers.mock", mock_registry_module)

  async def run_scenario():
    app = FastAPI()
    env_module = EnvModule(app)
    app.state.env = env_module
    db_module = DbModule(app)
    app.state.db = db_module

    await env_module.startup()
    await db_module.startup()

    provider = db_module._provider
    assert isinstance(provider, MockProvider)
    assert provider.started is True
    assert provider.config["dsn"] == "mock://dsn"
    assert provider.config["blob"] == "blob"

    response = await db_module.run("db:test:echo:1", {"foo": "bar"})
    assert response.op == "db:test:echo:1"
    assert response.payload == {"payload": {"foo": "bar"}}
    assert provider.requests and provider.requests[-1].payload == {"foo": "bar"}

    await db_module.shutdown()
    assert provider.stopped is True
    await env_module.shutdown()

  asyncio.run(run_scenario())
