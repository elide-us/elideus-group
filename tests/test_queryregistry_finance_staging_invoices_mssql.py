import asyncio

from queryregistry.finance.staging_invoices import mssql


def test_get_invoice_by_name_v1_uses_single_object_json_pattern(monkeypatch):
  captured = {}

  async def fake_run_json_one(sql, params=()):
    captured["sql"] = sql
    captured["params"] = params
    return {"rows": None}

  monkeypatch.setattr(mssql, "run_json_one", fake_run_json_one)

  result = asyncio.run(mssql.get_invoice_by_name_v1({"invoice_name": "E000000001"}))

  assert "WHERE element_invoice_name = ?" in captured["sql"]
  assert "FOR JSON PATH, WITHOUT_ARRAY_WRAPPER, INCLUDE_NULL_VALUES" in captured["sql"]
  assert captured["params"] == ("E000000001",)
  assert result == {"rows": None}


def test_insert_invoice_batch_and_list_by_import_round_trip_shape(monkeypatch):
  exec_calls = []
  captured_list = {}

  async def fake_run_exec(sql, params=()):
    exec_calls.append((sql, params))
    return {"rows": []}

  async def fake_run_json_many(sql, params=()):
    captured_list["sql"] = sql
    captured_list["params"] = params
    return {"rows": [{"element_invoice_name": "E000000001"}]}

  monkeypatch.setattr(mssql, "run_exec", fake_run_exec)
  monkeypatch.setattr(mssql, "run_json_many", fake_run_json_many)

  payload = {
    "imports_recid": 42,
    "rows": [
      {
        "element_invoice_name": "E000000001",
        "element_invoice_date": "2024-01-31",
        "element_invoice_period_start": "2024-01-01",
        "element_invoice_period_end": "2024-01-31",
        "element_due_date": "2024-02-15",
        "element_invoice_type": "AzureServices",
        "element_status": "Due",
        "element_billed_amount": "100.00000",
        "element_amount_due": "80.00000",
        "element_currency": "USD",
        "element_subscription_id": "sub-1",
        "element_subscription_name": "Prod",
        "element_purchase_order": "PO-1",
        "element_raw_json": '{"id":"E000000001"}',
      },
    ],
  }

  inserted = asyncio.run(mssql.insert_invoice_batch_v1(payload))
  listed = asyncio.run(mssql.list_invoices_by_import_v1({"imports_recid": 42}))

  assert inserted.rowcount == 1
  assert "SET NOCOUNT ON;" in exec_calls[0][0]
  assert exec_calls[0][1][0] == 42
  assert "ORDER BY element_invoice_date" in captured_list["sql"]
  assert captured_list["params"] == (42,)
  assert listed == {"rows": [{"element_invoice_name": "E000000001"}]}
