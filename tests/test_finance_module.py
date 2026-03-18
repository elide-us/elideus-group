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

  async def fake_get_number_by_prefix_account(prefix: str, account_number: str):
    assert prefix == "FP"
    assert account_number == "2025"
    return {"recid": 77}

  generated_payloads: list[dict] = []

  async def fake_upsert_period(payload: dict):
    generated_payloads.append(dict(payload))
    return dict(payload)

  module.list_periods_by_year = fake_list_periods_by_year
  module.get_number_by_prefix_account = fake_get_number_by_prefix_account
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
  assert all(row["numbers_recid"] == 77 for row in generated_payloads)


def test_generate_calendar_marks_53_week_adjustment_on_last_period():
  module = FinanceModule.__new__(FinanceModule)

  async def fake_list_periods_by_year(year: int):
    assert year == 2028
    return []

  async def fake_get_number_by_prefix_account(prefix: str, account_number: str):
    return None

  async def fake_upsert_number(payload: dict):
    assert payload["display_format"] == "FY2028"
    return {"recid": 91}

  generated_payloads: list[dict] = []

  async def fake_upsert_period(payload: dict):
    generated_payloads.append(dict(payload))
    return dict(payload)

  module.list_periods_by_year = fake_list_periods_by_year
  module.get_number_by_prefix_account = fake_get_number_by_prefix_account
  module.upsert_number = fake_upsert_number
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
