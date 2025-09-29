import asyncio
import pytest
from fastapi import FastAPI

from server.modules.db_module import DbModule
from server.modules.providers import DbProviderBase
from server.modules.providers.database.mssql_provider import MssqlProvider
from server.modules.providers.database.mssql_provider.db_helpers import DBQueryError, QueryErrorDetail


def test_init_uses_concrete_provider():
  app = FastAPI()
  db = DbModule(app)
  asyncio.run(db.init(provider="mssql"))
  assert isinstance(db._provider, MssqlProvider)


def test_db_module_run_propagates_query_error():
  app = FastAPI()
  db = DbModule(app)
  detail = QueryErrorDetail(query="SELECT 1", params=(), message="boom")

  class FailingProvider(DbProviderBase):
    def __init__(self):
      super().__init__()

    async def startup(self):
      pass

    async def shutdown(self):
      pass

    async def run(self, op, args):
      raise DBQueryError(detail)

  db._provider = FailingProvider()

  with pytest.raises(DBQueryError) as exc:
    asyncio.run(db.run("db:test:error", {}))
  assert exc.value.detail == detail
