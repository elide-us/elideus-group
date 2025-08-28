import asyncio
from fastapi import FastAPI

from server.modules.db_module import DbModule
from server.modules.providers.database.mssql_provider import MssqlProvider


def test_init_uses_concrete_provider():
  app = FastAPI()
  db = DbModule(app)
  asyncio.run(db.init(provider="mssql"))
  assert isinstance(db._provider, MssqlProvider)
