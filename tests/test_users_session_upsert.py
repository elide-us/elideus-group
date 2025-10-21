import asyncio
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from server.registry import get_handler
from server.registry.auth.session import mssql as session_mssql


def test_create_session_updates_existing(monkeypatch):
  executed: list[str] = []
  fetch_values = iter([("sess",), ("dev",)])

  class DummyCur:
    async def execute(self, sql, params):
      executed.append(sql.lower())

    async def fetchone(self):
      return next(fetch_values, None)

  @asynccontextmanager
  async def fake_transaction():
    yield DummyCur()

  async def fake_get_auth_provider_recid(provider, *, cursor=None):
    return 101

  monkeypatch.setattr(session_mssql, "transaction", fake_transaction)
  monkeypatch.setattr(session_mssql, "get_auth_provider_recid", fake_get_auth_provider_recid)

  handler = get_handler("db:auth:session:create_session:1")
  args = {
    "access_token": "tok",
    "expires": datetime.now(timezone.utc),
    "fingerprint": "fp",
    "user_agent": None,
    "ip_address": None,
    "user_guid": "user",
    "provider": "microsoft",
  }
  asyncio.run(handler(args))

  assert any("update users_sessions" in stmt for stmt in executed)
  assert not any("insert into users_sessions" in stmt for stmt in executed)
  assert any("update sessions_devices" in stmt for stmt in executed)
  assert not any("insert into sessions_devices" in stmt for stmt in executed)
