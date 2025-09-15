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
    assert "element_modified_on" in sql
    assert "element_user_id" in sql
    assert "element_tokens" in sql
    assert params == (personas_recid, start, end)
    return DBResult(rows=[{"recid": 1}], rowcount=1)

  monkeypatch.setattr(mssql_provider, 'fetch_json', fake_fetch_json)

  res = asyncio.run(provider.run(
    'db:assistant:conversations:list_by_time:1',
    {'personas_recid': personas_recid, 'start': start, 'end': end},
  ))
  assert isinstance(res, DBResult)
  assert res.rows == [{"recid": 1}]


def test_assistant_conversations_insert(monkeypatch):
  provider = MssqlProvider()
  args = {
    'personas_recid': 1,
    'models_recid': 2,
    'guild_id': '1',
    'channel_id': '2',
    'user_id': '3',
    'input_data': 'hi',
    'output_data': '',
    'tokens': 5,
  }

  async def fake_fetch_rows(sql, params, *, one=False, stream=False):
    assert one
    assert "INSERT INTO assistant_conversations" in sql
    assert params == (1, 2, '1', '2', '3', 'hi', '', 5)
    return DBResult(rows=[{'recid': 9}], rowcount=1)

  monkeypatch.setattr(mssql_provider, 'fetch_rows', fake_fetch_rows)

  res = asyncio.run(provider.run('db:assistant:conversations:insert:1', args))
  assert res.rows == [{'recid': 9}]


def test_assistant_conversations_update_output(monkeypatch):
  provider = MssqlProvider()
  args = {'recid': 9, 'output_data': 'out'}

  async def fake_exec(sql, params):
    assert "element_modified_on" not in sql
    assert params == ('out', 9)
    return DBResult(rowcount=1)

  monkeypatch.setattr(mssql_provider, 'exec_query', fake_exec)

  res = asyncio.run(provider.run('db:assistant:conversations:update_output:1', args))
  assert res.rowcount == 1

