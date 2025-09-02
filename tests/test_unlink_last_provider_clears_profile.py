import asyncio
from contextlib import asynccontextmanager

from server.modules.providers.database.mssql_provider import registry

class FakeCursor:
  def __init__(self, fetches, log):
    self._fetches = fetches
    self.log = log
  async def execute(self, sql, params):
    self.log.append((sql.strip(), params))
  async def fetchone(self):
    return self._fetches.pop(0)

@asynccontextmanager
async def fake_transaction(fetches, log):
  cur = FakeCursor(fetches, log)
  yield cur

def test_unlink_last_provider_clears_profile(monkeypatch):
  log = []
  fetches = [
    (1,),  # current providers_recid
    (1,),  # provider recid lookup
    (0,),  # remaining linked providers
  ]
  monkeypatch.setattr(
    registry,
    "transaction",
    lambda: fake_transaction(fetches, log),
  )
  res = asyncio.run(
    registry._users_unlink_provider({
      "guid": "00000000-0000-0000-0000-000000000001",
      "provider": "google",
    })
  )
  assert res["rows"][0]["providers_remaining"] == 0
  assert any(
    "element_display = ''" in sql and "element_email = ''" in sql
    for sql, _ in log
  )

