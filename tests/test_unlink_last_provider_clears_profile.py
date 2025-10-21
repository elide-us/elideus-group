import asyncio
from contextlib import asynccontextmanager
from typing import Any, Iterable

from server.registry.account.providers import mssql as users_providers_mssql


class FakeCursor:
  def __init__(self, fetches: Iterable[Any], log: list[tuple[str, tuple[Any, ...]]]):
    self._fetches = iter(fetches)
    self.log = log

  async def execute(self, sql, params):
    self.log.append((sql.strip().lower(), params))

  async def fetchone(self):
    return next(self._fetches, None)


@asynccontextmanager
async def fake_transaction(fetches, log):
  cur = FakeCursor(fetches, log)
  yield cur


def test_unlink_last_provider_clears_profile(monkeypatch):
  log: list[tuple[str, tuple[Any, ...]]] = []
  fetches = [(1,), (0,)]

  monkeypatch.setattr(
    users_providers_mssql,
    "transaction",
    lambda: fake_transaction(fetches, log),
  )

  async def fake_get_auth_provider_recid(provider, *, cursor=None):
    return 1

  monkeypatch.setattr(
    users_providers_mssql,
    "get_auth_provider_recid",
    fake_get_auth_provider_recid,
  )

  res = asyncio.run(
    users_providers_mssql.unlink_provider_v1({
      "guid": "00000000-0000-0000-0000-000000000001",
      "provider": "google",
    })
  )
  assert res.rows[0]["providers_remaining"] == 0
  assert any(
    "update account_users set providers_recid = null, element_display = '', element_email = ''" in sql
    for sql, _ in log
  )
