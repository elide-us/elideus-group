from __future__ import annotations

import asyncio

import pytest

from queryregistry.models import DBResponse
from server.modules.finance_module import FinanceModule


def test_generate_calendar_creates_16_periods_for_standard_year():
  module = FinanceModule.__new__(FinanceModule)

  async def fake_list_periods_by_year(year: int):
    assert year == 2025
    return []

  generated_payloads: list[dict] = []

  async def fake_upsert_period(payload: dict):
    generated_payloads.append(dict(payload))
    return dict(payload)

  module.list_periods_by_year = fake_list_periods_by_year
  module.upsert_period = fake_upsert_period

  rows = asyncio.run(FinanceModule.generate_calendar(module, 2025))

  assert len(rows) == 16
  assert [row["period_name"] for row in rows[:4]] == ["Q1M1", "Q1M2", "Q1M3", "Q1MC"]
  assert rows[0]["start_date"] == "2024-12-29"
  assert rows[0]["end_date"] == "2025-01-25"
  assert rows[3]["days_in_period"] == 7
  assert rows[3]["close_type"] == 1
  assert rows[-1]["period_name"] == "Q4MC"
  assert rows[-1]["close_type"] == 2
  assert rows[-1]["days_in_period"] == 7
  assert rows[-1]["is_leap_adjustment"] is False
  assert sum(row["days_in_period"] for row in rows) == 364


def test_generate_calendar_marks_53_week_adjustment_on_last_period():
  module = FinanceModule.__new__(FinanceModule)

  async def fake_list_periods_by_year(year: int):
    assert year == 2028
    return []

  generated_payloads: list[dict] = []

  async def fake_upsert_period(payload: dict):
    generated_payloads.append(dict(payload))
    return dict(payload)

  module.list_periods_by_year = fake_list_periods_by_year
  module.upsert_period = fake_upsert_period

  rows = asyncio.run(FinanceModule.generate_calendar(module, 2028))

  assert len(rows) == 16
  assert rows[-1]["period_name"] == "Q4MC"
  assert rows[-1]["days_in_period"] == 14
  assert rows[-1]["is_leap_adjustment"] is True
  assert rows[-1]["close_type"] == 2
  assert sum(row["days_in_period"] for row in rows) == 371
  assert generated_payloads[-1]["end_date"] == "2028-12-30"


def test_generate_calendar_rejects_duplicate_year():
  module = FinanceModule.__new__(FinanceModule)

  async def fake_list_periods_by_year(year: int):
    return [{"year": year, "period_name": "Q1M1"}]

  module.list_periods_by_year = fake_list_periods_by_year

  with pytest.raises(ValueError, match="already has generated periods"):
    asyncio.run(FinanceModule.generate_calendar(module, 2025))


def test_delete_ledger_blocks_when_journals_reference_it():
  class FakeDb:
    async def run(self, request):
      assert request.op == "db:finance:ledgers:journal_reference_count:1"
      return DBResponse(op=request.op, rows=[{"journal_count": 2}])

  module = FinanceModule.__new__(FinanceModule)
  module.db = FakeDb()

  async def fake_get_ledger(recid: int):
    return {
      "recid": recid,
      "element_name": "General Ledger",
      "element_status": 1,
    }

  module.get_ledger = fake_get_ledger

  with pytest.raises(ValueError, match="journals already reference it"):
    asyncio.run(FinanceModule.delete_ledger(module, 42))


def test_create_journal_allows_open_month_close_period():
  module = FinanceModule.__new__(FinanceModule)
  module.db = None

  async def fake_get_period(guid: str):
    assert guid == "period-guid"
    return {"guid": guid, "status": 1, "close_type": 1}

  async def fake_db_run(request):
    if request.op == "db:finance:journals:get_by_posting_key:1":
      return DBResponse(op=request.op, rows=[])
    if request.op == "db:finance:journals:create:1":
      return DBResponse(
        op=request.op,
        rows=[{
          "recid": 10,
          "element_name": "AZURE-IMPORT-10",
          "element_description": "desc",
          "element_posting_key": "pk",
          "element_source_type": "azure_invoice",
          "element_source_id": "10",
          "periods_guid": "period-guid",
          "ledgers_recid": None,
          "numbers_recid": None,
          "element_status": 0,
          "element_posted_by": None,
          "element_posted_on": None,
          "element_reversed_by": None,
          "element_reversal_of": None,
        }],
      )
    if request.op == "db:finance:journal_lines:create_lines_batch:1":
      return DBResponse(op=request.op, rows=[])
    if request.op == "db:finance:journals:get:1":
      return DBResponse(
        op=request.op,
        rows=[{
          "recid": 10,
          "element_name": "AZURE-IMPORT-10",
          "element_description": "desc",
          "element_posting_key": "pk",
          "element_source_type": "azure_invoice",
          "element_source_id": "10",
          "periods_guid": "period-guid",
          "ledgers_recid": None,
          "numbers_recid": None,
          "element_status": 0,
          "element_posted_by": None,
          "element_posted_on": None,
          "element_reversed_by": None,
          "element_reversal_of": None,
        }],
      )
    if request.op == "db:finance:journal_lines:list_by_journal:1":
      return DBResponse(
        op=request.op,
        rows=[
          {
            "recid": 1,
            "journals_recid": 10,
            "element_line_number": 1,
            "accounts_guid": "expense-guid",
            "element_debit": "10.00000",
            "element_credit": "0.00000",
            "element_description": "line 1",
            "dimension_recids": [],
          },
          {
            "recid": 2,
            "journals_recid": 10,
            "element_line_number": 2,
            "accounts_guid": "ap-guid",
            "element_debit": "0.00000",
            "element_credit": "10.00000",
            "element_description": "line 2",
            "dimension_recids": [],
          },
        ],
      )
    if request.op == "db:finance:journals:update_status:1":
      return DBResponse(
        op=request.op,
        rows=[{
          "recid": 10,
          "element_name": "AZURE-IMPORT-10",
          "element_description": "desc",
          "element_posting_key": "pk",
          "element_source_type": "azure_invoice",
          "element_source_id": "10",
          "periods_guid": "period-guid",
          "ledgers_recid": None,
          "numbers_recid": None,
          "element_status": 2,
          "element_posted_by": None,
          "element_posted_on": "2026-03-18T00:00:00+00:00",
          "element_reversed_by": None,
          "element_reversal_of": None,
        }],
      )
    raise AssertionError(f"Unhandled op: {request.op}")

  module.get_period = fake_get_period

  class FakeDb:
    async def run(self, request):
      return await fake_db_run(request)

  module.db = FakeDb()

  journal = asyncio.run(
    FinanceModule.create_and_post_system_journal(
      module,
      name="AZURE-IMPORT-10",
      description="desc",
      posting_key="pk",
      source_type="azure_invoice",
      source_id="10",
      periods_guid="period-guid",
      lines=[
        {"line_number": 1, "accounts_guid": "expense-guid", "debit": "10", "credit": "0", "dimension_recids": []},
        {"line_number": 2, "accounts_guid": "ap-guid", "debit": "0", "credit": "10", "dimension_recids": []},
      ],
    )
  )

  assert journal["status"] == 2


def test_create_and_post_system_journal_blocks_non_open_period_status():
  module = FinanceModule.__new__(FinanceModule)
  module.db = object()

  async def fake_create_journal(**kwargs):
    return {"recid": 10}

  async def fake_get_journal(recid: int):
    assert recid == 10
    return {"recid": 10, "status": 0, "periods_guid": "period-guid"}

  async def fake_get_period(guid: str):
    assert guid == "period-guid"
    return {"guid": guid, "status": 2, "close_type": 0}

  async def fake_get_journal_lines(recid: int):
    assert recid == 10
    return [
      {"debit": "10.00000", "credit": "0.00000"},
      {"debit": "0.00000", "credit": "10.00000"},
    ]

  module.create_journal = fake_create_journal
  module.get_journal = fake_get_journal
  module.get_period = fake_get_period
  module.get_journal_lines = fake_get_journal_lines

  with pytest.raises(ValueError, match="Cannot post to closed period"):
    asyncio.run(
      FinanceModule.create_and_post_system_journal(
        module,
        name="AZURE-IMPORT-10",
        posting_key="pk",
        periods_guid="period-guid",
        lines=[
          {"line_number": 1, "accounts_guid": "expense-guid", "debit": "10", "credit": "0", "dimension_recids": []},
          {"line_number": 2, "accounts_guid": "ap-guid", "debit": "0", "credit": "10", "dimension_recids": []},
        ],
      )
    )


def test_next_formatted_number_rolls_over_to_next_series():
  calls: list[str] = []

  class FakeDb:
    async def run(self, request):
      calls.append(request.op)
      if request.op == "db:finance:numbers:next_number_by_scope:1":
        if calls.count(request.op) == 1:
          return DBResponse(op=request.op, rows=[])
        return DBResponse(
          op=request.op,
          rows=[{
            "recid": 22,
            "accounts_guid": "account-guid",
            "element_prefix": "JRN",
            "element_account_number": "JRN-CRP",
            "element_block_start": 1,
            "element_last_number": 1,
            "element_max_number": 99999999,
            "element_allocation_size": 1,
            "element_sequence_status": 1,
            "element_sequence_type": "continuous",
            "element_series_number": 2,
            "element_scope": "credit_purchase",
            "element_pattern": "JRN-CRP-{series:03d}-{number:08d}",
            "element_display_format": "JRN-CRP-###-########",
          }],
        )
      if request.op == "db:finance:numbers:get_by_scope:1":
        return DBResponse(
          op=request.op,
          rows=[{
            "recid": 21,
            "accounts_guid": "account-guid",
            "element_prefix": "JRN",
            "element_account_number": "JRN-CRP",
            "element_last_number": 99999999,
            "element_max_number": 99999999,
            "element_allocation_size": 1,
            "element_reset_policy": "Never",
            "element_sequence_status": 1,
            "element_sequence_type": "continuous",
            "element_series_number": 1,
            "element_scope": "credit_purchase",
            "element_pattern": "JRN-CRP-{series:03d}-{number:08d}",
            "element_display_format": "JRN-CRP-###-########",
          }],
        )
      if request.op == "db:finance:numbers:close_sequence:1":
        return DBResponse(op=request.op, rows=[{"recid": 21}])
      if request.op == "db:finance:numbers:upsert:1":
        assert request.payload["series_number"] == 2
        assert request.payload["scope"] == "credit_purchase"
        return DBResponse(
          op=request.op,
          rows=[{
            "recid": 22,
            "accounts_guid": "account-guid",
            "element_prefix": "JRN",
            "element_account_number": "JRN-CRP",
            "element_last_number": 0,
            "element_max_number": 99999999,
            "element_allocation_size": 1,
            "element_reset_policy": "Never",
            "element_sequence_status": 1,
            "element_sequence_type": "continuous",
            "element_series_number": 2,
            "element_scope": "credit_purchase",
            "element_pattern": "JRN-CRP-{series:03d}-{number:08d}",
            "element_display_format": "JRN-CRP-###-########",
          }],
        )
      raise AssertionError(f"Unhandled op: {request.op}")

  module = FinanceModule.__new__(FinanceModule)
  module.db = FakeDb()

  formatted, recid = asyncio.run(
    FinanceModule._next_formatted_number(module, "JRN", "credit_purchase")
  )

  assert formatted == "JRN-CRP-002-00000001"
  assert recid == 22


def test_create_journal_uses_scope_based_sequence_lookup():
  class FakeDb:
    async def run(self, request):
      if request.op == "db:finance:journals:get_by_posting_key:1":
        return DBResponse(op=request.op, rows=[])
      if request.op == "db:finance:journals:create:1":
        return DBResponse(
          op=request.op,
          rows=[{
            "recid": 10,
            "element_name": "JRN-IMP-001-00000001",
            "element_description": "desc",
            "element_posting_key": "JRN-IMP-001-00000001",
            "element_source_type": "azure_invoice",
            "element_source_id": "10",
            "periods_guid": None,
            "ledgers_recid": None,
            "numbers_recid": 15,
            "element_status": 0,
            "element_posted_by": None,
            "element_posted_on": None,
            "element_reversed_by": None,
            "element_reversal_of": None,
          }],
        )
      if request.op == "db:finance:journal_lines:create_lines_batch:1":
        return DBResponse(op=request.op, rows=[])
      raise AssertionError(f"Unhandled op: {request.op}")

  module = FinanceModule.__new__(FinanceModule)
  module.db = FakeDb()

  async def fake_next_formatted_number(prefix: str, scope: str):
    assert prefix == "JRN"
    assert scope == "billing_import"
    return "JRN-IMP-001-00000001", 15

  module._next_formatted_number = fake_next_formatted_number

  journal = asyncio.run(
    FinanceModule.create_journal(
      module,
      name="ignored",
      description="desc",
      source_type="azure_invoice",
      source_id="10",
      lines=[
        {"line_number": 1, "accounts_guid": "expense-guid", "debit": "10", "credit": "0", "dimension_recids": []},
        {"line_number": 2, "accounts_guid": "ap-guid", "debit": "0", "credit": "10", "dimension_recids": []},
      ],
    )
  )

  assert journal["posting_key"] == "JRN-IMP-001-00000001"
  assert journal["numbers_recid"] == 15


def test_purchase_credit_product_creates_lot_and_journal_lines():
  module = FinanceModule.__new__(FinanceModule)
  module.db = object()

  appended: dict[str, object] = {}

  async def fake_get_product(recid=None, sku=None):
    assert sku == "CRED-5K"
    return {
      "sku": "CRED-5K",
      "name": "Purchase 5,000 AI Credits",
      "category": "credit_purchase",
      "price": "50.00000",
      "currency": "USD",
      "credits": 5000,
      "status": 1,
    }

  async def fake_process_payment_stub(product, users_guid):
    assert product["sku"] == "CRED-5K"
    assert users_guid == "user-guid"
    return {"success": True, "transaction_token": "STUB-123"}

  async def fake_get_active_config(category: str, periods_guid: str):
    assert category == "credit_purchase"
    assert periods_guid == "period-guid"
    return {"journals_recid": 99}

  async def fake_create_lot(**kwargs):
    assert kwargs["users_guid"] == "user-guid"
    assert kwargs["credits"] == 5000
    assert kwargs["source_id"] == "STUB-123"
    return {"lot_number": "LOT-0001"}

  async def fake_get_pipeline_config(pipeline: str, key: str):
    values = {
      ("credit_purchase", "payment_clearing_account_number"): "1300",
      ("credit_purchase", "deferred_revenue_account_number"): "2100",
    }
    return values[(pipeline, key)]

  async def fake_get_account_guid_by_number(number: str):
    return f"acct-{number}"

  async def fake_append_balanced_journal_lines(**kwargs):
    appended.update(kwargs)
    return []

  module.get_product = fake_get_product
  module._process_payment_stub = fake_process_payment_stub
  module.get_active_product_journal_config = fake_get_active_config
  module.create_lot = fake_create_lot
  module.get_pipeline_config = fake_get_pipeline_config
  module._get_account_guid_by_number = fake_get_account_guid_by_number
  module._append_balanced_journal_lines = fake_append_balanced_journal_lines

  result = asyncio.run(
    FinanceModule.purchase_product(
      module,
      users_guid="user-guid",
      sku="CRED-5K",
      actor_guid="actor-guid",
      periods_guid="period-guid",
    )
  )

  assert result == {
    "product": "CRED-5K",
    "credits_granted": 5000,
    "lot_number": "LOT-0001",
    "transaction_token": "STUB-123",
    "journal_lines_added": True,
  }
  assert appended["journals_recid"] == 99
  assert appended["debit_account_guid"] == "acct-1300"
  assert appended["credit_account_guid"] == "acct-2100"
  assert appended["amount"] == "50.00000"
  assert "STUB-123" in str(appended["description"])



def test_purchase_credit_product_requires_active_config():
  module = FinanceModule.__new__(FinanceModule)
  module.db = object()

  async def fake_get_product(recid=None, sku=None):
    return {
      "sku": "CRED-5K",
      "category": "credit_purchase",
      "price": "50.00000",
      "currency": "USD",
      "credits": 5000,
      "status": 1,
    }

  async def fake_process_payment_stub(product, users_guid):
    return {"success": True, "transaction_token": "STUB-123"}

  async def fake_get_active_config(category: str, periods_guid: str):
    return None

  module.get_product = fake_get_product
  module._process_payment_stub = fake_process_payment_stub
  module.get_active_product_journal_config = fake_get_active_config

  with pytest.raises(ValueError, match="No active journal configuration"):
    asyncio.run(
      FinanceModule.purchase_product(
        module,
        users_guid="user-guid",
        sku="CRED-5K",
        periods_guid="period-guid",
      )
    )



def test_purchase_enablement_updates_user_enablements():
  module = FinanceModule.__new__(FinanceModule)
  module.db = object()
  calls: list[tuple[str, int]] = []

  async def fake_get_product(recid=None, sku=None):
    return {
      "sku": "STOR-ENABLE",
      "category": "enablement",
      "price": "0.00000",
      "currency": "USD",
      "credits": 0,
      "enablement_key": "ROLE_STORAGE",
      "status": 1,
    }

  async def fake_process_payment_stub(product, users_guid):
    return {"success": True, "transaction_token": "STUB-999"}

  async def fake_get_user_enablements(users_guid: str):
    return 0

  async def fake_set_user_enablements(users_guid: str, enablements: int):
    calls.append((users_guid, enablements))
    return {"users_guid": users_guid, "element_enablements": str(enablements)}

  module.get_product = fake_get_product
  module._process_payment_stub = fake_process_payment_stub
  module.get_user_enablements = fake_get_user_enablements
  module.set_user_enablements = fake_set_user_enablements

  result = asyncio.run(
    FinanceModule.purchase_product(
      module,
      users_guid="user-guid",
      sku="STOR-ENABLE",
      periods_guid="period-guid",
    )
  )

  assert result == {
    "product": "STOR-ENABLE",
    "enablement_granted": "ROLE_STORAGE",
    "transaction_token": "STUB-999",
  }
  assert calls == [("user-guid", 1)]
