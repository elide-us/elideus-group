import pytest
import asyncio
from fastapi import FastAPI
from types import SimpleNamespace
import server.modules.database_module as db_mod
from server.modules.database_module import DatabaseModule
from server.modules.env_module import EnvironmentModule

@pytest.fixture
def db_app(monkeypatch):
  monkeypatch.setenv("DISCORD_SECRET", "secret")
  monkeypatch.setenv("JWT_SECRET", "jwt")
  monkeypatch.setenv("POSTGRES_CONNECTION_STRING", "postgres://user@host/db")
  monkeypatch.setenv("AZURE_BLOB_CONNECTION_STRING", "cs")
  app = FastAPI()
  env = EnvironmentModule(app)
  app.state.env = env
  app.state.discord = SimpleNamespace()
  return app

def test_db_startup(monkeypatch, db_app):
  async def fake_pool(**kwargs):
    return "pool"
  monkeypatch.setattr(db_mod.asyncpg, "create_pool", fake_pool)
  dbm = DatabaseModule(db_app, dsn="postgres://user@host/db")
  asyncio.run(dbm.startup())
  assert dbm.pool == "pool"

def test_db_fetch_one_without_pool(db_app):
  dbm = DatabaseModule(db_app, dsn="postgres://user@host/db")
  with pytest.raises(RuntimeError):
    asyncio.run(dbm._fetch_one("SELECT 1"))

class DummyConn:
  def __init__(self, row=None):
    self.row = row
    self.executed = []
  async def fetchrow(self, query, *args):
    self.fetched = (query, args)
    return self.row
  async def fetchval(self, query, *args):
    self.fetched = (query, args)
    return self.row
  async def execute(self, query, *args):
    self.executed.append((query, args))
  def transaction(self):
    class T:
      async def __aenter__(self2):
        return None
      async def __aexit__(self2, *exc):
        return False
    return T()
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
  def __init__(self, row=None):
    self.row = row
  def acquire(self):
    return DummyAcquire(DummyConn(self.row))
  async def close(self):
    pass

def test_select_user_new_schema(db_app):
  captured = {}

  class Conn(DummyConn):
    async def fetchrow(self, query, *args):
      captured['args'] = args
      return {
        'guid': 'uid',
        'display_name': 'u',
        'email': 'e',
        'credits': 0,
        'provider_name': 'microsoft',
      }

  class Pool(DummyPool):
    def acquire(self):
      return DummyAcquire(Conn())

  dbm = DatabaseModule(db_app, dsn="postgres://user@host/db")
  dbm.pool = Pool()
  result = asyncio.run(dbm.select_user('microsoft', 'pid'))
  assert captured['args'] == ('microsoft', 'pid')
  assert result['provider_name'] == 'microsoft'


def test_get_config_value(db_app):
  class Pool(DummyPool):
    def __init__(self):
      self.row = {'value': 'v'}
    def acquire(self):
      return DummyAcquire(DummyConn(self.row))

  dbm = DatabaseModule(db_app, dsn="postgres://user@host/db")
  dbm.pool = Pool()
  result = asyncio.run(dbm.get_config_value('Version'))
  assert result == 'v'

def test_profile_image_ops(db_app):
  conn = DummyConn({'image_b64': 'img'})

  class Pool(DummyPool):
    def __init__(self, c):
      self.c = c
    def acquire(self):
      return DummyAcquire(self.c)

  dbm = DatabaseModule(db_app, dsn="postgres://user@host/db")
  dbm.pool = Pool(conn)
  img = asyncio.run(dbm.get_user_profile_image('uid'))
  assert img == 'img'
  asyncio.run(dbm.set_user_profile_image('uid', 'new'))
  assert conn.executed[0][0].startswith('INSERT INTO users_profileimg')


#def test_secure_fetch_one(monkeypatch, db_app):
#  dbm = DatabaseModule(db_app)
#  dbm.pool = DummyPool(row={"a": 1})
#  result = asyncio.run(dbm._secure_fetch_one("Q", "00000000-0000-0000-0000-000000000000"))
#  assert result == {"a": 1}


# def test_select_user(monkeypatch, db_app):
 # dbm = DatabaseModule(db_app)
 # async def fake_fetch(query, *args):
 #   return {
 #     "guid": "uid",
 #     "display_name": "u",
 #     "email": "e",
 #     "credits": 10,
 #     "provider_name": "microsoft",
 #   }
 # monkeypatch.setattr(dbm, "_fetch_one", fake_fetch)
 # result = asyncio.run(dbm.select_user("microsoft", "pid"))
 # assert result["provider_name"] == "microsoft"


#def test_insert_user_unknown_provider(monkeypatch, db_app):
#  dbm = DatabaseModule(db_app)

#  class InsertConn:
#    async def fetchrow(self, query, *args):
#      return None
#    async def fetchval(self, query, *args):
#      if "SELECT id FROM auth_providers" in query:
#        return None
#      return None
#    async def execute(self, query, *args):
#      pass
#    def transaction(self):
#      class T:
#        async def __aenter__(self2):
#          return None
#        async def __aexit__(self2, *exc):
#          return False
#      return T()
#    async def __aenter__(self):
#      return self
#    async def __aexit__(self, *exc):
#      return False

#  class InsertPool:
#    def __init__(self, conn):
#      self.conn = conn
#    def acquire(self):
#      class A:
#        def __init__(self, c):
#          self.c = c
#        async def __aenter__(self):
#          return self.c
#        async def __aexit__(self, *exc):
#          return False
#      return A(self.conn)
#    async def close(self):
#      pass

#  dbm.pool = InsertPool(InsertConn())

#  with pytest.raises(RuntimeError):
#    asyncio.run(dbm.insert_user("microsoft", "pid", "e", "u"))

