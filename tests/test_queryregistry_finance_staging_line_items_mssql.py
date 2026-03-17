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


def test_insert_line_items_batch_v1_sets_record_type_and_defaults_usage(monkeypatch):
  exec_calls = []

  async def fake_run_exec(sql, params=()):
    exec_calls.append((sql, params))
    return {"rows": []}

  monkeypatch.setattr(mssql, "run_exec", fake_run_exec)

  payload = {
    "imports_recid": 11,
    "vendors_recid": 22,
    "rows": [
      {
        "element_date": "2025-01-01",
        "element_service": "AzureServices",
        "element_category": "Invoice",
        "element_description": "Invoice row",
        "element_quantity": 1,
        "element_unit_price": "10.00",
        "element_amount": "10.00",
        "element_currency": "USD",
        "element_raw_json": "{}",
        "element_record_type": "invoice",
      },
      {
        "element_date": "2025-01-02",
        "element_service": "Compute",
        "element_category": "VM",
        "element_description": "Usage row",
        "element_quantity": 1,
        "element_unit_price": "2.00",
        "element_amount": "2.00",
        "element_currency": "USD",
        "element_raw_json": "{}",
      },
    ],
  }

  result = asyncio.run(mssql.insert_line_items_batch_v1(payload))

  assert result.rowcount == 2
  assert "element_record_type" in exec_calls[0][0]
  assert exec_calls[0][1][11] == "invoice"
  assert exec_calls[1][1][11] == "usage"
