import asyncio

import pytest

from server.modules.providers.database.mssql_provider import db_helpers


def test_fetch_rows_returns_empty_on_error(monkeypatch):
  class Cur:
    async def __aenter__(self):
      return self

    async def __aexit__(self, exc_type, exc, tb):
      pass

    async def execute(self, q, p):
      raise Exception("boom")

  class Conn:
    async def __aenter__(self):
      return self

    async def __aexit__(self, exc_type, exc, tb):
      pass

    def cursor(self):
      return Cur()

  class Pool:
    def acquire(self):
      class _Ctx:
        async def __aenter__(self_inner):
          return Conn()

        async def __aexit__(self_inner, exc_type, exc, tb):
          pass

      return _Ctx()

  monkeypatch.setattr(db_helpers.logic, "_pool", Pool())
  res = asyncio.run(db_helpers.fetch_rows("SELECT 1"))
  assert res.rows == []
  assert res.rowcount == 0


def test_fetch_json_raises_on_error(monkeypatch):
  class Cur:
    async def __aenter__(self):
      return self

    async def __aexit__(self, exc_type, exc, tb):
      pass

    async def execute(self, q, p):
      raise Exception("boom")

    async def fetchone(self):
      return None

  class Conn:
    async def __aenter__(self):
      return self

    async def __aexit__(self, exc_type, exc, tb):
      pass

    def cursor(self):
      return Cur()

  class Pool:
    def acquire(self):
      class _Ctx:
        async def __aenter__(self_inner):
          return Conn()

        async def __aexit__(self_inner, exc_type, exc, tb):
          pass

      return _Ctx()

  monkeypatch.setattr(db_helpers.logic, "_pool", Pool())
  with pytest.raises(Exception):
    asyncio.run(db_helpers.fetch_json("SELECT 1"))


def test_fetch_json_handles_multiple_rows(monkeypatch):
  class Cur:
    def __init__(self):
      self._rows = [("{\"a\":1,\"b\":\"",), ("two\"}",)]
      self._idx = 0

    async def __aenter__(self):
      return self

    async def __aexit__(self, exc_type, exc, tb):
      pass

    async def execute(self, q, p):
      pass

    async def fetchone(self):
      if self._idx < len(self._rows):
        row = self._rows[self._idx]
        self._idx += 1
        return row
      return None

  class Conn:
    async def __aenter__(self):
      return self

    async def __aexit__(self, exc_type, exc, tb):
      pass

    def cursor(self):
      return Cur()

  class Pool:
    def acquire(self):
      class _Ctx:
        async def __aenter__(self_inner):
          return Conn()

        async def __aexit__(self_inner, exc_type, exc, tb):
          pass

      return _Ctx()

  monkeypatch.setattr(db_helpers.logic, "_pool", Pool())
  res = asyncio.run(db_helpers.fetch_json("SELECT"))
  assert res.rows == [{"a": 1, "b": "two"}]
  assert res.rowcount == 1


def test_exec_query_raises_on_error(monkeypatch):
  class Cur:
    async def __aenter__(self):
      return self

    async def __aexit__(self, exc_type, exc, tb):
      pass

    async def execute(self, q, p):
      raise Exception("boom")

  class Conn:
    async def __aenter__(self):
      return self

    async def __aexit__(self, exc_type, exc, tb):
      pass

    def cursor(self):
      return Cur()

  class Pool:
    def acquire(self):
      class _Ctx:
        async def __aenter__(self_inner):
          return Conn()

        async def __aexit__(self_inner, exc_type, exc, tb):
          pass

      return _Ctx()

  monkeypatch.setattr(db_helpers.logic, "_pool", Pool())
  with pytest.raises(Exception):
    asyncio.run(db_helpers.exec_query("UPDATE x SET y=1"))


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
