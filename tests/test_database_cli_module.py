import asyncio
import sys
import types

from fastapi import FastAPI


fake_mssql_cli = types.SimpleNamespace(
  connect=None,
  reconnect=None,
  list_tables=None,
)
sys.modules.setdefault("server.modules.database_cli.mssql_cli", fake_mssql_cli)

from server.modules.database_cli_module import DatabaseCliModule


class _FakeEnv:
  def __init__(self, dsn=None):
    self._dsn = dsn

  async def on_ready(self):
    return None

  def get(self, key: str):
    if key == "AZURE_SQL_CONNECTION_STRING":
      return self._dsn
    return None


def test_startup_without_dsn_keeps_metadata_apis_available():
  app = FastAPI()
  app.state.env = _FakeEnv(dsn=None)
  module = DatabaseCliModule(app)

  async def run_scenario():
    await module.startup()
    namespace = await module.get_database_rpc_namespace()
    models = await module.list_queryregistry_models()

    assert namespace["namespace"] == "db"
    assert namespace["operationCount"] == len(namespace["operations"])
    assert namespace["operationCount"] > 0
    assert isinstance(models, list)
    assert len(models) > 0

  asyncio.run(run_scenario())


def test_connect_requires_configured_dsn():
  app = FastAPI()
  app.state.env = _FakeEnv(dsn=None)
  module = DatabaseCliModule(app)

  async def run_scenario():
    await module.startup()
    try:
      await module.connect()
      assert False, "connect should fail without DSN"
    except RuntimeError as exc:
      assert "AZURE_SQL_CONNECTION_STRING not configured" in str(exc)

  asyncio.run(run_scenario())
