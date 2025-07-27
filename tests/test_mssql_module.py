import pytest
import asyncio
from fastapi import FastAPI
from types import SimpleNamespace
import server.modules.mssql_module as db_mod
from server.modules.mssql_module import MSSQLModule
from server.modules.env_module import EnvironmentModule

@pytest.fixture
def mssql_app(monkeypatch):
  monkeypatch.setenv("DISCORD_SECRET", "secret")
  monkeypatch.setenv("JWT_SECRET", "jwt")
  monkeypatch.setenv("AZURE_BLOB_CONNECTION_STRING", "cs")
  app = FastAPI()
  env = EnvironmentModule(app)
  app.state.env = env
  app.state.discord = SimpleNamespace()
  return app

def test_mssql_startup(monkeypatch, mssql_app):
  async def fake_pool(**kwargs):
    return "pool"
  monkeypatch.setattr(db_mod.aioodbc, "create_pool", fake_pool)
  dbm = MSSQLModule(mssql_app, dsn="sql://cs")
  asyncio.run(dbm.startup())
  assert dbm.pool == "pool"

def test_mssql_fetch_one_without_pool(mssql_app):
  dbm = MSSQLModule(mssql_app, dsn="sql://cs")
  with pytest.raises(RuntimeError):
    asyncio.run(dbm._fetch_one("SELECT 1"))

class DummyCursor:
  def __init__(self, row=None, column="value"):
    self.row = row
    self.column = column
    self.executed = []

  async def __aenter__(self):
    return self

  async def __aexit__(self, *exc):
    return False

  async def execute(self, query, params=None):
    self.executed.append((query, params))

  async def fetchone(self):
    return self.row

  async def fetchall(self):
    return [self.row] if self.row else []

  @property
  def description(self):
    if isinstance(self.row, dict):
      return [(k,) for k in self.row.keys()]
    return [(self.column,)] if self.row is not None else []

class DummyConn:
  def __init__(self, row=None, column="value"):
    self.row = row
    self.cur = DummyCursor(row, column)
  def cursor(self):
    return self.cur
  async def __aenter__(self):
    return self
  async def __aexit__(self, *exc):
    return False

class DummyAcquire:
  def __init__(self, conn):
    self.conn = conn
  async def __aenter__(self):
    return self.conn
  async def __aexit__(self, *exc):
    return False

class DummyPool:
  def __init__(self, row=None, column="value"):
    self.row = row
    self.column = column
  def acquire(self):
    return DummyAcquire(DummyConn(self.row, self.column))
  async def close(self):
    pass

def test_mssql_get_config_value(mssql_app):
  dbm = MSSQLModule(mssql_app, dsn="sql://cs")
  dbm.pool = DummyPool(('v',), column="element_value")
  result = asyncio.run(dbm.get_config_value('Version'))
  assert result == 'v'

def test_mssql_profile_image_ops(mssql_app):
  conn = DummyConn(('img',), column="element_base64")
  class Pool(DummyPool):
    def __init__(self, c):
      self.c = c
    def acquire(self):
      return DummyAcquire(self.c)
  dbm = MSSQLModule(mssql_app, dsn="sql://cs")
  dbm.pool = Pool(conn)
  img = asyncio.run(dbm.get_user_profile_image('uid'))
  assert img == 'img'
  asyncio.run(dbm.set_user_profile_image('uid', 'new'))
  assert any(e[0].startswith('SELECT 1 FROM users_profileimg') for e in conn.cur.executed)
