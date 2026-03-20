import asyncio

from queryregistry.finance.staging import mssql


def test_list_imports_v1_maps_element_columns_to_rpc_shape(monkeypatch):
  captured = {}

  async def fake_run_json_many(sql, params=()):
    captured["sql"] = sql
    captured["params"] = params
    return {"rows": []}

  monkeypatch.setattr(mssql, "run_json_many", fake_run_json_many)

  asyncio.run(mssql.list_imports_v1({}))

  sql = captured["sql"]
  assert "element_source" in sql
  assert "AS source" not in sql
  assert "element_metric" in sql
  assert "AS metric" not in sql
  assert "element_period_start" in sql
  assert "AS period_start" not in sql
  assert "element_requested_by" in sql
  assert "element_approved_by" in sql
  assert "element_approved_on" in sql
  assert captured["params"] == ()


def test_list_imports_v1_filters_by_status_when_requested(monkeypatch):
  captured = {}

  async def fake_run_json_many(sql, params=()):
    captured["sql"] = sql
    captured["params"] = params
    return {"rows": []}

  monkeypatch.setattr(mssql, "run_json_many", fake_run_json_many)

  asyncio.run(mssql.list_imports_v1({"status": 4}))

  assert "WHERE element_status = ?" in captured["sql"]
  assert captured["params"] == (4,)


def test_create_import_v1_returns_json_payload(monkeypatch):
  captured = {}

  async def fake_run_json_one(sql, params=()):
    captured["sql"] = sql
    captured["params"] = params
    return {"rows": [{"recid": 1}]}

  monkeypatch.setattr(mssql, "run_json_one", fake_run_json_one)

  args = {
    "source": "azure_cost_details",
    "scope": "subscriptions/sub-id",
    "metric": "ActualCost",
    "period_start": "2024-01-01",
    "period_end": "2024-01-31",
    "requested_by": "user-guid",
    "initial_status": 4,
  }

  result = asyncio.run(mssql.create_import_v1(args))

  sql = captured["sql"]
  assert "FOR JSON PATH, WITHOUT_ARRAY_WRAPPER, INCLUDE_NULL_VALUES" in sql
  assert "INTO @inserted" in sql
  assert "element_requested_by" in sql
  assert captured["params"] == (
    "azure_cost_details",
    "subscriptions/sub-id",
    "ActualCost",
    "2024-01-01",
    "2024-01-31",
    4,
    "user-guid",
  )
  assert result == {"rows": [{"recid": 1}]}


def test_approve_import_v1_updates_only_pending_approval_rows(monkeypatch):
  captured = {}

  async def fake_run_exec(sql, params=()):
    captured["sql"] = sql
    captured["params"] = params
    return {"rows": []}

  monkeypatch.setattr(mssql, "run_exec", fake_run_exec)

  asyncio.run(mssql.approve_import_v1({"imports_recid": 77, "approved_by": "mgr-guid"}))

  assert "element_status = 1" in captured["sql"]
  assert "element_approved_by = ?" in captured["sql"]
  assert "WHERE recid = ? AND element_status = 4" in captured["sql"]
  assert captured["params"] == ("mgr-guid", 77)


def test_reject_import_v1_updates_error_reason(monkeypatch):
  captured = {}

  async def fake_run_exec(sql, params=()):
    captured["sql"] = sql
    captured["params"] = params
    return {"rows": []}

  monkeypatch.setattr(mssql, "run_exec", fake_run_exec)

  asyncio.run(
    mssql.reject_import_v1(
      {"imports_recid": 77, "approved_by": "mgr-guid", "reason": "Needs backup"},
    ),
  )

  assert "element_status = 5" in captured["sql"]
  assert "element_error = ?" in captured["sql"]
  assert "WHERE recid = ? AND element_status = 4" in captured["sql"]
  assert captured["params"] == ("mgr-guid", "Needs backup", 77)


def test_delete_import_v1_deletes_all_staging_children_before_import(monkeypatch):
  captured = {}

  async def fake_run_exec(sql, params=()):
    captured["sql"] = sql
    captured["params"] = params
    return {"rows": []}

  monkeypatch.setattr(mssql, "run_exec", fake_run_exec)

  asyncio.run(mssql.delete_import_v1({"imports_recid": 77}))

  assert "DELETE FROM finance_staging_line_items" in captured["sql"]
  assert "DELETE FROM finance_staging_azure_invoices" in captured["sql"]
  assert "DELETE FROM finance_staging_azure_cost_details" in captured["sql"]
  assert captured["params"] == (77, 77, 77, 77)


def test_insert_cost_detail_batch_v1_uses_api_field_names_as_element_columns(monkeypatch):
  captured = []

  async def fake_run_exec(sql, params=()):
    captured.append((sql, params))
    return {"rows": []}

  monkeypatch.setattr(mssql, "run_exec", fake_run_exec)

  result = asyncio.run(
    mssql.insert_cost_detail_batch_v1(
      {
        "imports_recid": 77,
        "rows": [
          {
            "consumedService": "Microsoft.Sql",
            "meterCategory": "Databases",
            "costInBillingCurrency": "12.34",
          },
        ],
      },
    ),
  )

  sql, params = captured[0]
  assert "[element_consumedService]" in sql
  assert "[element_meterCategory]" in sql
  assert "[element_costInBillingCurrency]" in sql
  assert params == (77, "Microsoft.Sql", "Databases", "12.34")
  assert result.rowcount == 1
