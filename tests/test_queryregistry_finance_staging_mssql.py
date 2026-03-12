import asyncio

from queryregistry.finance.staging import mssql


def test_list_imports_v1_maps_element_columns_to_rpc_shape(monkeypatch):
  captured = {}

  async def fake_run_json_many(sql, params=()):
    captured['sql'] = sql
    captured['params'] = params
    return {'rows': []}

  monkeypatch.setattr(mssql, 'run_json_many', fake_run_json_many)

  asyncio.run(mssql.list_imports_v1({}))

  sql = captured['sql']
  assert 'element_source AS source' in sql
  assert 'element_metric AS metric' in sql
  assert 'element_period_start AS period_start' in sql
  assert captured['params'] == ()


def test_create_import_v1_returns_json_payload(monkeypatch):
  captured = {}

  async def fake_run_json_one(sql, params=()):
    captured['sql'] = sql
    captured['params'] = params
    return {'rows': [{'recid': 1}]}

  monkeypatch.setattr(mssql, 'run_json_one', fake_run_json_one)

  args = {
    'source': 'azure_cost_details',
    'scope': 'subscriptions/sub-id',
    'metric': 'ActualCost',
    'period_start': '2024-01-01',
    'period_end': '2024-01-31',
  }

  result = asyncio.run(mssql.create_import_v1(args))

  sql = captured['sql']
  assert 'FOR JSON PATH, WITHOUT_ARRAY_WRAPPER, INCLUDE_NULL_VALUES' in sql
  assert 'INTO @inserted' in sql
  assert captured['params'] == (
    'azure_cost_details',
    'subscriptions/sub-id',
    'ActualCost',
    '2024-01-01',
    '2024-01-31',
  )
  assert result == {'rows': [{'recid': 1}]}
