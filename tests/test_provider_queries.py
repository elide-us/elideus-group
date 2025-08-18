from uuid import uuid4
from server.modules.providers.mssql_provider.registry import get_handler as get_mssql_handler
from server.modules.providers.mssql_provider import db_helpers
import asyncio

def test_mssql_get_by_provider_identifier_uses_user_view():
  handler = get_mssql_handler("urn:users:providers:get_by_provider_identifier:1")
  _, sql, _ = handler({"provider": "microsoft", "provider_identifier": str(uuid4())})
  sql = sql.lower()
  assert "vw_account_user_profile" in sql
  assert "v.credits" in sql
  assert "users_credits" not in sql

def test_mssql_get_profile_uses_profile_view():
  handler = get_mssql_handler("urn:users:profile:get_profile:1")
  _, sql, _ = handler({"guid": "gid"})
  sql = sql.lower()
  assert "vw_account_user_profile" in sql
  assert "v.credits" in sql
  assert "users_credits" not in sql

def test_mssql_get_rotkey_uses_security_view():
  handler = get_mssql_handler("db:users:session:get_rotkey:1")
  _, sql, _ = handler({"guid": "gid"})
  assert "vw_account_user_security" in sql.lower()

def test_mssql_get_by_access_token_uses_security_view():
  handler = get_mssql_handler("db:auth:session:get_by_access_token:1")
  _, sql, _ = handler({"access_token": "tok"})
  assert "vw_account_user_security" in sql.lower()


def test_fetch_rows_returns_empty_on_error(monkeypatch):
  class Cur:
    async def execute(self, q, p):
      raise Exception("boom")

  class Conn:
    async def cursor(self):
      return Cur()

  class Pool:
    async def acquire(self):
      return Conn()

  monkeypatch.setattr(db_helpers.logic, "_pool", Pool())
  res = asyncio.run(db_helpers.fetch_rows("SELECT 1"))
  assert res.rows == []
  assert res.rowcount == 0


def test_fetch_json_returns_empty_on_error(monkeypatch):
  class Cur:
    async def execute(self, q, p):
      raise Exception("boom")
    async def fetchone(self):
      return None

  class Conn:
    async def cursor(self):
      return Cur()

  class Pool:
    async def acquire(self):
      return Conn()

  monkeypatch.setattr(db_helpers.logic, "_pool", Pool())
  res = asyncio.run(db_helpers.fetch_json("SELECT 1"))
  assert res.rows == []
  assert res.rowcount == 0


def test_exec_query_returns_empty_on_error(monkeypatch):
  class Cur:
    async def execute(self, q, p):
      raise Exception("boom")

  class Conn:
    async def cursor(self):
      return Cur()

  class Pool:
    async def acquire(self):
      return Conn()

  monkeypatch.setattr(db_helpers.logic, "_pool", Pool())
  res = asyncio.run(db_helpers.exec_query("UPDATE x SET y=1"))
  assert res.rows == []
  assert res.rowcount == 0


def test_fetch_rows_stream(monkeypatch):
  class Cur:
    async def __aenter__(self):
      return self
    async def __aexit__(self, exc_type, exc, tb):
      pass
    async def execute(self, q, p):
      pass
    async def fetchone(self):
      return None

  class Conn:
    async def __aenter__(self):
      return self
    async def __aexit__(self, exc_type, exc, tb):
      pass
    async def cursor(self):
      return Cur()

  class Pool:
    async def acquire(self):
      class _Ctx:
        async def __aenter__(self_inner):
          return Conn()
        async def __aexit__(self_inner, exc_type, exc, tb):
          pass
      return _Ctx()

  monkeypatch.setattr(db_helpers.logic, "_pool", Pool())

  async def run():
    gen = await db_helpers.fetch_rows("SELECT", stream=True)
    return hasattr(gen, "__aiter__")

  assert asyncio.run(run())
