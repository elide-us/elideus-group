import asyncio

from queryregistry.finance.staging_line_items import mssql


def test_aggregate_line_items_v1_groups_by_record_type(monkeypatch):
  captured = {}

  async def fake_run_json_many(sql, params=()):
    captured["sql"] = sql
    captured["params"] = params
    return {"rows": []}

  monkeypatch.setattr(mssql, "run_json_many", fake_run_json_many)

  result = asyncio.run(mssql.aggregate_line_items_v1({"imports_recid": 5}))

  assert "element_record_type" in captured["sql"]
  assert "GROUP BY element_service, element_category, element_record_type" in captured["sql"]
  assert "ORDER BY element_record_type, element_service, element_category" in captured["sql"]
  assert captured["params"] == (5,)
  assert result == {"rows": []}
