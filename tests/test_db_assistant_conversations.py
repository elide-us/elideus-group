import asyncio

from server.modules.providers.database.mssql_provider import MssqlProvider
import server.modules.providers.database.mssql_provider as mssql_provider
from server.modules.providers import DBResult


def test_assistant_conversations_list_by_time(monkeypatch):
  provider = MssqlProvider()
  personas_recid = 1
  start = '2024-01-01'
  end = '2024-01-02'

  async def fake_fetch_json(sql, params, *, many=False):
    assert many
    assert "FROM assistant_conversations" in sql
    assert params == (personas_recid, start, end)
    return DBResult(rows=[{"recid": 1}], rowcount=1)

  monkeypatch.setattr(mssql_provider, 'fetch_json', fake_fetch_json)

  res = asyncio.run(provider.run(
    'db:assistant:conversations:list_by_time:1',
    {'personas_recid': personas_recid, 'start': start, 'end': end},
  ))
  assert isinstance(res, DBResult)
  assert res.rows == [{"recid": 1}]

