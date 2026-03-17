import asyncio

from queryregistry.finance.staging import mssql as staging_mssql
from queryregistry.finance.staging_account_map import mssql as map_mssql


def test_resolve_account_prefers_exact_service_match_over_wildcard(monkeypatch):
  captured = {}

  async def fake_run_json_one(sql, params=()):
    captured['sql'] = sql
    captured['params'] = params
    return {'rows': [{'accounts_guid': 'exact-guid'}]}

  monkeypatch.setattr(map_mssql, 'run_json_one', fake_run_json_one)

  result = asyncio.run(
    map_mssql.resolve_account_v1({'service_name': 'Microsoft.Sql', 'meter_category': 'Databases'}),
  )

  assert 'map.element_service_pattern = ? OR map.element_service_pattern = ' in captured['sql']
  assert 'WHEN map.element_service_pattern = ? THEN 0' in captured['sql']
  assert "WHEN map.element_service_pattern = '*' THEN 1" in captured['sql']
  assert captured['params'] == ('Microsoft.Sql', 'Databases', 'Microsoft.Sql')
  assert result == {'rows': [{'accounts_guid': 'exact-guid'}]}


def test_resolve_account_falls_back_to_wildcard_when_no_exact_match(monkeypatch):
  captured = {}

  async def fake_run_json_one(sql, params=()):
    captured['sql'] = sql
    captured['params'] = params
    return {'rows': [{'accounts_guid': 'wildcard-guid'}]}

  monkeypatch.setattr(map_mssql, 'run_json_one', fake_run_json_one)

  result = asyncio.run(map_mssql.resolve_account_v1({'service_name': 'Microsoft.Cache'}))

  assert "map.element_service_pattern = '*'" in captured['sql']
  assert captured['params'] == ('Microsoft.Cache', '', 'Microsoft.Cache')
  assert result == {'rows': [{'accounts_guid': 'wildcard-guid'}]}


def test_aggregate_cost_by_service_groups_by_service_and_meter(monkeypatch):
  captured = {}

  async def fake_run_json_many(sql, params=()):
    captured['sql'] = sql
    captured['params'] = params
    return {'rows': []}

  monkeypatch.setattr(staging_mssql, 'run_json_many', fake_run_json_many)

  result = asyncio.run(staging_mssql.aggregate_cost_by_service_v1({'imports_recid': 42}))

  sql = captured['sql']
  assert 'GROUP BY element_ConsumedService, element_MeterCategory' in sql
  assert 'SUM(CAST(element_CostInBillingCurrency AS DECIMAL(19,5)))' in sql
  assert "LTRIM(RTRIM(element_CostInBillingCurrency)) <> ''" in sql
  assert captured['params'] == (42,)
  assert result == {'rows': []}
