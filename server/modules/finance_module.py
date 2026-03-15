from __future__ import annotations

import calendar
import logging
import uuid
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Any

from fastapi import FastAPI

from . import BaseModule
from .db_module import DbModule
from queryregistry.finance.accounts import (
  delete_account_request,
  get_account_request,
  list_account_children_request,
  list_accounts_request,
  upsert_account_request,
)
from queryregistry.finance.accounts.models import (
  DeleteAccountParams,
  GetAccountParams,
  ListAccountsParams,
  ListChildrenParams,
  UpsertAccountParams,
)
from queryregistry.finance.dimensions import (
  delete_dimension_request,
  get_dimension_request,
  list_dimensions_by_name_request,
  list_dimensions_request,
  upsert_dimension_request,
)
from queryregistry.finance.dimensions.models import (
  DeleteDimensionParams,
  GetDimensionParams,
  ListDimensionsByNameParams,
  ListDimensionsParams,
  UpsertDimensionParams,
)
from queryregistry.finance.numbers import (
  delete_number_request,
  get_by_prefix_account_number_request,
  get_number_request,
  list_numbers_request,
  next_number_request,
  upsert_number_request,
)
from queryregistry.finance.numbers.models import (
  DeleteNumberParams,
  GetByPrefixAndAccountNumberParams,
  GetNumberParams,
  ListNumbersParams,
  NextNumberParams,
  UpsertNumberParams,
)
from queryregistry.finance.periods import (
  delete_period_request,
  get_period_request,
  list_periods_by_year_request,
  list_periods_request,
  upsert_period_request,
)
from queryregistry.finance.periods.models import (
  DeletePeriodParams,
  GetPeriodParams,
  ListPeriodsByYearParams,
  ListPeriodsParams,
  UpsertPeriodParams,
)
from queryregistry.finance.journal_lines import (
  create_lines_batch_request,
  delete_lines_by_journal_request,
  list_lines_by_journal_request,
)
from queryregistry.finance.journal_lines.models import (
  CreateLineParams,
  CreateLinesBatchParams,
  DeleteLinesByJournalParams,
  ListLinesByJournalParams,
)
from queryregistry.finance.journals import (
  create_journal_request,
  get_by_posting_key_request,
  get_journal_request,
  list_journals_request,
  update_journal_status_request,
)
from queryregistry.finance.journals.models import (
  CreateJournalParams,
  GetByPostingKeyParams,
  GetJournalParams,
  ListJournalsParams,
  UpdateJournalStatusParams,
)


_FISCAL_PERIODS_ACCOUNTS_GUID = "00000000-0000-0000-0000-000000000000"
_FIVE_PLACES = Decimal("0.00001")
_FOUR_PLACES = Decimal("0.0001")


class FinanceModule(BaseModule):
  def __init__(self, app: FastAPI):
    super().__init__(app)
    self.db: DbModule | None = None

  async def startup(self):
    self.db = self.app.state.db
    await self.db.on_ready()
    self.app.state.finance = self
    logging.debug("[FinanceModule] loaded")
    self.mark_ready()

  async def shutdown(self):
    logging.info("[FinanceModule] shutdown")
    self.db = None

  def _map_period(self, row: dict[str, Any]) -> dict[str, Any]:
    return {
      "guid": row.get("element_guid"),
      "year": row.get("element_year"),
      "period_number": row.get("element_period_number"),
      "period_name": row.get("element_period_name"),
      "start_date": row.get("element_start_date"),
      "end_date": row.get("element_end_date"),
      "days_in_period": row.get("element_days_in_period"),
      "quarter_number": row.get("element_quarter_number"),
      "has_closing_week": row.get("element_has_closing_week"),
      "is_leap_adjustment": row.get("element_is_leap_adjustment"),
      "anchor_event": row.get("element_anchor_event"),
      "close_type": row.get("element_close_type"),
      "status": row.get("element_status"),
      "numbers_recid": row.get("numbers_recid"),
      "element_display_format": row.get("element_display_format"),
    }

  def _map_account(self, row: dict[str, Any]) -> dict[str, Any]:
    return {
      "guid": row.get("element_guid"),
      "number": row.get("element_number"),
      "name": row.get("element_name"),
      "account_type": row.get("element_type"),
      "parent": row.get("element_parent"),
      "is_posting": row.get("is_posting"),
      "status": row.get("element_status"),
    }

  def _map_number(self, row: dict[str, Any]) -> dict[str, Any]:
    return {
      "recid": row.get("recid"),
      "accounts_guid": row.get("accounts_guid"),
      "prefix": row.get("element_prefix"),
      "account_number": row.get("element_account_number"),
      "last_number": row.get("element_last_number"),
      "allocation_size": row.get("element_allocation_size"),
      "reset_policy": row.get("element_reset_policy"),
      "pattern": row.get("element_pattern"),
      "display_format": row.get("element_display_format"),
      "account_name": row.get("account_name"),
    }

  def _map_dimension(self, row: dict[str, Any]) -> dict[str, Any]:
    return {
      "recid": row.get("recid"),
      "name": row.get("element_name"),
      "value": row.get("element_value"),
      "description": row.get("element_description"),
      "status": row.get("element_status"),
    }

  def _map_journal(self, row: dict[str, Any]) -> dict[str, Any]:
    return {
      "recid": row.get("recid"),
      "name": row.get("element_name"),
      "description": row.get("element_description"),
      "posting_key": row.get("element_posting_key"),
      "source_type": row.get("element_source_type"),
      "source_id": row.get("element_source_id"),
      "periods_guid": row.get("periods_guid"),
      "ledgers_recid": row.get("ledgers_recid"),
      "numbers_recid": row.get("numbers_recid"),
      "status": row.get("element_status"),
      "posted_by": row.get("element_posted_by"),
      "posted_on": row.get("element_posted_on"),
      "reversed_by": row.get("element_reversed_by"),
      "reversal_of": row.get("element_reversal_of"),
    }

  def _map_journal_line(self, row: dict[str, Any]) -> dict[str, Any]:
    return {
      "recid": row.get("recid"),
      "journals_recid": row.get("journals_recid"),
      "line_number": row.get("element_line_number"),
      "accounts_guid": row.get("accounts_guid"),
      "debit": row.get("element_debit"),
      "credit": row.get("element_credit"),
      "description": row.get("element_description"),
      "dimension_recids": row.get("dimension_recids", []),
    }

  @staticmethod
  def _to_decimal(value: Any) -> Decimal:
    """Parse a value to Decimal. Accepts str, int, float, Decimal."""
    if isinstance(value, Decimal):
      return value
    try:
      return Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
      return Decimal("0")

  @staticmethod
  def _quantize_4dp(value: Decimal) -> Decimal:
    """Quantize to 4 decimal places, half-up, per precision policy."""
    return value.quantize(_FOUR_PLACES, rounding=ROUND_HALF_UP)

  @staticmethod
  def _quantize_5dp(value: Decimal) -> Decimal:
    """Quantize to 5 decimal places for storage."""
    return value.quantize(_FIVE_PLACES, rounding=ROUND_HALF_UP)

  async def list_periods(self) -> list[dict[str, Any]]:
    assert self.db
    res = await self.db.run(list_periods_request(ListPeriodsParams()))
    return [self._map_period(row) for row in res.rows]

  async def list_periods_by_year(self, year: int) -> list[dict[str, Any]]:
    assert self.db
    res = await self.db.run(list_periods_by_year_request(ListPeriodsByYearParams(year=year)))
    return [self._map_period(row) for row in res.rows]

  async def get_period(self, guid: str) -> dict[str, Any] | None:
    assert self.db
    res = await self.db.run(get_period_request(GetPeriodParams(guid=guid)))
    if not res.rows:
      return None
    return self._map_period(dict(res.rows[0]))

  async def upsert_period(self, data: dict[str, Any]) -> dict[str, Any]:
    assert self.db
    params = UpsertPeriodParams(**data)
    res = await self.db.run(upsert_period_request(params))
    row = dict(res.rows[0]) if res.rows else params.model_dump()
    return self._map_period(row)

  async def delete_period(self, guid: str) -> dict[str, Any]:
    assert self.db
    await self.db.run(delete_period_request(DeletePeriodParams(guid=guid)))
    return {"guid": guid}

  async def generate_calendar(self, fiscal_year: int, start_date: str) -> list[dict[str, Any]]:
    start = datetime.fromisoformat(start_date).date()
    if start.weekday() != 6:
      raise ValueError("start_date must be a Sunday")

    assert self.db
    lookup_res = await self.db.run(
      get_by_prefix_account_number_request(
        GetByPrefixAndAccountNumberParams(prefix="FP", account_number=str(fiscal_year))
      )
    )
    lookup_row = dict(lookup_res.rows[0]) if lookup_res.rows else None

    if lookup_row and lookup_row.get("recid") is not None:
      numbers_recid = int(lookup_row["recid"])
    else:
      upsert_res = await self.db.run(
        upsert_number_request(
          UpsertNumberParams(
            accounts_guid=_FISCAL_PERIODS_ACCOUNTS_GUID,
            prefix="FP",
            account_number=str(fiscal_year),
            last_number=0,
            allocation_size=1,
            reset_policy="Never",
            display_format=f"FY{fiscal_year}",
          )
        )
      )
      upsert_row = dict(upsert_res.rows[0]) if upsert_res.rows else None
      if not upsert_row or upsert_row.get("recid") is None:
        raise ValueError(f"Failed to create number sequence for fiscal year {fiscal_year}")
      numbers_recid = int(upsert_row["recid"])

    fiscal_end = start + timedelta(days=365)
    has_leap_adjustment = calendar.isleap(fiscal_year) and start <= date(fiscal_year, 2, 29) < fiscal_end

    generated: list[dict[str, Any]] = []
    cursor = start
    period_number = 1

    for quarter in range(1, 5):
      for month_idx in range(1, 5):
        days_in_period = 28
        is_leap_adjustment = False
        if quarter == 1 and month_idx == 4 and has_leap_adjustment:
          days_in_period = 8
          is_leap_adjustment = True
        end = cursor + timedelta(days=days_in_period - 1)
        name = f"Q{quarter}M{month_idx}"
        payload = {
          "guid": None,
          "year": fiscal_year,
          "period_number": period_number,
          "period_name": name,
          "start_date": cursor.isoformat(),
          "end_date": end.isoformat(),
          "days_in_period": days_in_period,
          "quarter_number": quarter,
          "has_closing_week": False,
          "is_leap_adjustment": is_leap_adjustment,
          "anchor_event": None,
          "close_type": 0,
          "status": 1,
          "numbers_recid": numbers_recid,
        }
        row = await self.upsert_period(payload)
        generated.append(row)
        cursor = end + timedelta(days=1)
        period_number += 1

      m4 = generated[-1]
      closing_payload = {
        "guid": None,
        "year": fiscal_year,
        "period_number": period_number,
        "period_name": f"Q{quarter}MC",
        "start_date": m4["start_date"],
        "end_date": m4["end_date"],
        "days_in_period": 0,
        "quarter_number": quarter,
        "has_closing_week": True,
        "is_leap_adjustment": False,
        "anchor_event": "period_close",
        "close_type": 0,
        "status": 1,
        "numbers_recid": numbers_recid,
      }
      row = await self.upsert_period(closing_payload)
      generated.append(row)
      period_number += 1

    return generated

  async def list_accounts(self) -> list[dict[str, Any]]:
    assert self.db
    res = await self.db.run(list_accounts_request(ListAccountsParams()))
    return [self._map_account(row) for row in res.rows]

  async def get_account(self, guid: str) -> dict[str, Any] | None:
    assert self.db
    res = await self.db.run(get_account_request(GetAccountParams(guid=guid)))
    if not res.rows:
      return None
    return self._map_account(dict(res.rows[0]))

  async def upsert_account(self, data: dict[str, Any]) -> dict[str, Any]:
    assert self.db
    next_data = dict(data)
    if not next_data.get("guid"):
      next_data["guid"] = str(uuid.uuid4())
    params = UpsertAccountParams(**next_data)
    res = await self.db.run(upsert_account_request(params))
    row = dict(res.rows[0]) if res.rows else params.model_dump()
    return self._map_account(row)

  async def delete_account(self, guid: str) -> dict[str, Any]:
    assert self.db
    await self.db.run(delete_account_request(DeleteAccountParams(guid=guid)))
    return {"guid": guid}

  async def list_account_children(self, parent_guid: str) -> list[dict[str, Any]]:
    assert self.db
    res = await self.db.run(
      list_account_children_request(ListChildrenParams(parent_guid=parent_guid)),
    )
    return [self._map_account(row) for row in res.rows]

  async def list_numbers(self) -> list[dict[str, Any]]:
    assert self.db
    res = await self.db.run(list_numbers_request(ListNumbersParams()))
    return [self._map_number(row) for row in res.rows]

  async def get_number(self, recid: int) -> dict[str, Any] | None:
    assert self.db
    res = await self.db.run(get_number_request(GetNumberParams(recid=recid)))
    if not res.rows:
      return None
    return self._map_number(dict(res.rows[0]))

  async def upsert_number(self, data: dict[str, Any]) -> dict[str, Any]:
    assert self.db
    params = UpsertNumberParams(**data)
    res = await self.db.run(upsert_number_request(params))
    row = dict(res.rows[0]) if res.rows else params.model_dump()
    return self._map_number(row)

  async def delete_number(self, recid: int) -> dict[str, Any]:
    assert self.db
    await self.db.run(delete_number_request(DeleteNumberParams(recid=recid)))
    return {"recid": recid}

  async def next_number(self, recid: int) -> dict[str, Any] | None:
    assert self.db
    res = await self.db.run(next_number_request(NextNumberParams(recid=recid)))
    if not res.rows:
      return None
    return self._map_number(dict(res.rows[0]))

  async def list_dimensions(self) -> list[dict[str, Any]]:
    assert self.db
    res = await self.db.run(list_dimensions_request(ListDimensionsParams()))
    return [self._map_dimension(row) for row in res.rows]

  async def list_dimensions_by_name(self, name: str) -> list[dict[str, Any]]:
    assert self.db
    res = await self.db.run(list_dimensions_by_name_request(ListDimensionsByNameParams(name=name)))
    return [self._map_dimension(row) for row in res.rows]

  async def get_dimension(self, recid: int) -> dict[str, Any] | None:
    assert self.db
    res = await self.db.run(get_dimension_request(GetDimensionParams(recid=recid)))
    if not res.rows:
      return None
    return self._map_dimension(dict(res.rows[0]))

  async def upsert_dimension(self, data: dict[str, Any]) -> dict[str, Any]:
    assert self.db
    params = UpsertDimensionParams(**data)
    res = await self.db.run(upsert_dimension_request(params))
    row = dict(res.rows[0]) if res.rows else params.model_dump()
    return self._map_dimension(row)

  async def delete_dimension(self, recid: int) -> dict[str, Any]:
    assert self.db
    await self.db.run(delete_dimension_request(DeleteDimensionParams(recid=recid)))
    return {"recid": recid}

  async def list_journals(
    self,
    status: int | None = None,
    periods_guid: str | None = None,
  ) -> list[dict[str, Any]]:
    assert self.db
    res = await self.db.run(list_journals_request(ListJournalsParams(status=status, periods_guid=periods_guid)))
    return [self._map_journal(row) for row in res.rows]

  async def get_journal(self, recid: int) -> dict[str, Any] | None:
    assert self.db
    res = await self.db.run(get_journal_request(GetJournalParams(recid=recid)))
    if not res.rows:
      return None
    return self._map_journal(dict(res.rows[0]))

  async def get_journal_lines(self, journals_recid: int) -> list[dict[str, Any]]:
    assert self.db
    res = await self.db.run(list_lines_by_journal_request(ListLinesByJournalParams(journals_recid=journals_recid)))
    return [self._map_journal_line(row) for row in res.rows]

  async def delete_journal_lines(self, journals_recid: int) -> dict[str, Any]:
    assert self.db
    await self.db.run(delete_lines_by_journal_request(DeleteLinesByJournalParams(journals_recid=journals_recid)))
    return {"journals_recid": journals_recid}

  async def create_journal(
    self,
    *,
    name: str,
    description: str | None = None,
    posting_key: str | None = None,
    source_type: str | None = None,
    source_id: str | None = None,
    periods_guid: str | None = None,
    ledgers_recid: int | None = None,
    lines: list[dict[str, Any]],
    post: bool = False,
    posted_by: str | None = None,
  ) -> dict[str, Any]:
    assert self.db

    if posting_key:
      existing = await self.db.run(get_by_posting_key_request(GetByPostingKeyParams(posting_key=posting_key)))
      if existing.rows:
        logging.debug("[FinanceModule] create_journal idempotency hit for posting_key=%s", posting_key)
        return self._map_journal(dict(existing.rows[0]))

    if periods_guid and post:
      period = await self.get_period(periods_guid)
      if not period:
        raise ValueError("Period not found")
      if period["close_type"] != 0:
        raise ValueError("Cannot post to closed period")

    quantified_lines: list[CreateLineParams] = []
    total_debits = Decimal("0")
    total_credits = Decimal("0")
    for line in lines:
      debit = self._quantize_4dp(self._to_decimal(line.get("debit", "0")))
      credit = self._quantize_4dp(self._to_decimal(line.get("credit", "0")))
      debit_5dp = self._quantize_5dp(debit)
      credit_5dp = self._quantize_5dp(credit)
      total_debits += debit_5dp
      total_credits += credit_5dp
      quantified_lines.append(
        CreateLineParams(
          journals_recid=0,
          line_number=int(line["line_number"]),
          accounts_guid=str(line["accounts_guid"]),
          debit=str(debit_5dp),
          credit=str(credit_5dp),
          description=line.get("description"),
          dimension_recids=[int(x) for x in line.get("dimension_recids", [])],
        )
      )

    if abs(total_debits - total_credits) > Decimal("0.00001"):
      raise ValueError(f"Journal is unbalanced: debits={total_debits} credits={total_credits}")

    create_res = await self.db.run(
      create_journal_request(
        CreateJournalParams(
          name=name,
          description=description,
          posting_key=posting_key,
          source_type=source_type,
          source_id=source_id,
          periods_guid=periods_guid,
          ledgers_recid=ledgers_recid,
          status=0,
        )
      )
    )
    created = self._map_journal(dict(create_res.rows[0]))
    journal_recid = int(created["recid"])
    lines_payload = [line.model_copy(update={"journals_recid": journal_recid}) for line in quantified_lines]
    await self.db.run(
      create_lines_batch_request(CreateLinesBatchParams(journals_recid=journal_recid, lines=lines_payload))
    )

    if post:
      return await self.post_journal(journal_recid, posted_by)
    return created

  async def post_journal(self, recid: int, posted_by: str | None = None) -> dict[str, Any]:
    assert self.db
    journal = await self.get_journal(recid)
    if not journal:
      raise ValueError("Journal not found")
    if journal["status"] != 0:
      raise ValueError("Only unposted journals can be posted")

    periods_guid = journal.get("periods_guid")
    if periods_guid:
      period = await self.get_period(periods_guid)
      if not period:
        raise ValueError("Period not found")
      if period["close_type"] != 0:
        raise ValueError("Cannot post to closed period")

    lines = await self.get_journal_lines(recid)
    if not lines:
      raise ValueError("Cannot post a journal with no lines")

    total_debits = Decimal("0")
    total_credits = Decimal("0")
    for line in lines:
      total_debits += self._quantize_5dp(self._to_decimal(line.get("debit", "0")))
      total_credits += self._quantize_5dp(self._to_decimal(line.get("credit", "0")))

    if abs(total_debits - total_credits) > Decimal("0.00001"):
      raise ValueError(f"Journal is unbalanced: debits={total_debits} credits={total_credits}")

    res = await self.db.run(
      update_journal_status_request(
        UpdateJournalStatusParams(
          recid=recid,
          status=1,
          posted_by=posted_by,
          posted_on=datetime.now(timezone.utc).isoformat(),
        )
      )
    )
    return self._map_journal(dict(res.rows[0]))

  async def reverse_journal(self, recid: int, posted_by: str | None = None) -> dict[str, Any]:
    assert self.db
    original = await self.get_journal(recid)
    if not original:
      raise ValueError("Journal not found")
    if original["status"] != 1:
      raise ValueError("Only posted journals can be reversed")

    periods_guid = original.get("periods_guid")
    if periods_guid:
      period = await self.get_period(periods_guid)
      if not period:
        raise ValueError("Period not found")
      if period["close_type"] != 0:
        raise ValueError("Cannot reverse journal into a closed period")

    original_lines = await self.get_journal_lines(recid)
    if not original_lines:
      raise ValueError("Cannot reverse a journal with no lines")

    reversal_lines: list[dict[str, Any]] = []
    for line in original_lines:
      reversal_lines.append(
        {
          "line_number": line["line_number"],
          "accounts_guid": line["accounts_guid"],
          "debit": line.get("credit", "0"),
          "credit": line.get("debit", "0"),
          "description": line.get("description"),
          "dimension_recids": line.get("dimension_recids", []),
        }
      )

    reversal = await self.create_journal(
      name=f"REV-{original['name']}",
      description=f"Reversal of journal {recid}",
      posting_key=f"REV-{original['posting_key']}" if original.get("posting_key") else None,
      source_type="reversal",
      source_id=str(recid),
      periods_guid=periods_guid,
      ledgers_recid=original.get("ledgers_recid"),
      lines=reversal_lines,
      post=True,
      posted_by=posted_by,
    )

    reversal_recid = int(reversal["recid"])
    await self.db.run(
      update_journal_status_request(
        UpdateJournalStatusParams(
          recid=recid,
          status=2,
          reversed_by=reversal_recid,
        )
      )
    )
    res = await self.db.run(
      update_journal_status_request(
        UpdateJournalStatusParams(
          recid=reversal_recid,
          status=1,
          reversal_of=recid,
        )
      )
    )
    return self._map_journal(dict(res.rows[0]))
