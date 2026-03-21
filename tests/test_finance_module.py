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
