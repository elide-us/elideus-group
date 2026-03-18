from __future__ import annotations

import logging
import uuid
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Any

from fastapi import FastAPI

from . import BaseModule
from .db_module import DbModule
from queryregistry.finance.ledgers import (
  create_ledger_request,
  delete_ledger_request,
  get_ledger_by_name_request,
  get_ledger_request,
  journal_reference_count_request,
  list_ledgers_request,
  update_ledger_request,
)
from queryregistry.finance.ledgers.models import (
  CreateLedgerParams,
  DeleteLedgerParams,
  GetLedgerByNameParams,
  GetLedgerParams,
  JournalReferenceCountParams,
  ListLedgersParams,
  UpdateLedgerParams,
)
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
  close_sequence_request,
  delete_number_request,
  get_by_prefix_account_number_request,
  get_number_request,
  list_numbers_request,
  next_number_request,
  upsert_number_request,
)
from queryregistry.finance.numbers.models import (
  CloseSequenceParams,
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
from queryregistry.finance.credit_lots import (
  create_event_request,
  create_lot_request,
  consume_credits_request,
  expire_lot_request,
  get_lot_request,
  list_events_by_lot_request,
  list_lots_by_user_request,
  sum_remaining_by_user_request,
)
from queryregistry.finance.credit_lots.models import (
  CreateEventParams,
  CreateLotParams,
  ConsumeCreditsParams,
  ExpireLotParams,
  GetLotParams,
  ListEventsByLotParams,
  ListLotsByUserParams,
  SumRemainingByUserParams,
)
from queryregistry.finance.credits import (
  set_credits_request,
)
from queryregistry.finance.credits.models import (
  SetCreditsParams,
)


_FIVE_PLACES = Decimal("0.00001")
_FOUR_PLACES = Decimal("0.0001")
_UPSERT_NUMBER_STRIP = frozenset({"account_name", "remaining"})


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

  def _map_ledger(self, row: dict[str, Any]) -> dict[str, Any]:
    return {
      "recid": row.get("recid"),
      "element_name": row.get("element_name"),
      "element_description": row.get("element_description"),
      "element_chart_of_accounts_guid": row.get("element_chart_of_accounts_guid"),
      "element_status": row.get("element_status"),
      "element_created_on": row.get("element_created_on"),
      "element_modified_on": row.get("element_modified_on"),
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
      "max_number": row.get("element_max_number"),
      "allocation_size": row.get("element_allocation_size"),
      "reset_policy": row.get("element_reset_policy"),
      "sequence_status": row.get("element_sequence_status"),
      "pattern": row.get("element_pattern"),
      "display_format": row.get("element_display_format"),
      "account_name": row.get("account_name"),
      "remaining": row.get("remaining"),
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

  def _map_lot(self, row: dict[str, Any]) -> dict[str, Any]:
    return {
      "recid": row.get("recid"),
      "users_guid": row.get("users_guid"),
      "lot_number": row.get("element_lot_number"),
      "source_type": row.get("element_source_type"),
      "credits_original": row.get("element_credits_original"),
      "credits_remaining": row.get("element_credits_remaining"),
      "unit_price": row.get("element_unit_price"),
      "total_paid": row.get("element_total_paid"),
      "currency": row.get("element_currency"),
      "expires_at": row.get("element_expires_at"),
      "expired": row.get("element_expired"),
      "source_id": row.get("element_source_id"),
      "numbers_recid": row.get("numbers_recid"),
      "status": row.get("element_status"),
    }

  def _map_lot_event(self, row: dict[str, Any]) -> dict[str, Any]:
    return {
      "recid": row.get("recid"),
      "lots_recid": row.get("lots_recid"),
      "event_type": row.get("element_event_type"),
      "credits": row.get("element_credits"),
      "unit_price": row.get("element_unit_price"),
      "description": row.get("element_description"),
      "actor_guid": row.get("element_actor_guid"),
      "journals_recid": row.get("journals_recid"),
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
    next_data = dict(data)
    next_data["status"] = self._validate_period_status(int(next_data.get("status", 1)))
    params = UpsertPeriodParams(**next_data)
    res = await self.db.run(upsert_period_request(params))
    row = dict(res.rows[0]) if res.rows else params.model_dump()
    return self._map_period(row)

  async def delete_period(self, guid: str) -> dict[str, Any]:
    assert self.db
    await self.db.run(delete_period_request(DeletePeriodParams(guid=guid)))
    return {"guid": guid}

  @staticmethod
  def _nearest_sunday_for_fiscal_year(fiscal_year: int) -> date:
    target = date(fiscal_year - 1, 12, 28)
    nearest: date | None = None
    nearest_distance: int | None = None

    for offset in range(-6, 7):
      candidate = target + timedelta(days=offset)
      if candidate.weekday() != 6:
        continue
      distance = abs(offset)
      if nearest is None or nearest_distance is None or distance < nearest_distance or (distance == nearest_distance and candidate < nearest):
        nearest = candidate
        nearest_distance = distance

    if nearest is None:
      raise ValueError(f"Unable to resolve fiscal year start for {fiscal_year}")
    return nearest

  async def list_ledgers(self) -> list[dict[str, Any]]:
    assert self.db
    res = await self.db.run(list_ledgers_request(ListLedgersParams()))
    return [self._map_ledger(row) for row in res.rows]

  async def get_ledger(self, recid: int) -> dict[str, Any] | None:
    assert self.db
    res = await self.db.run(get_ledger_request(GetLedgerParams(recid=recid)))
    if not res.rows:
      return None
    return self._map_ledger(dict(res.rows[0]))

  async def _get_ledger_by_name(self, element_name: str) -> dict[str, Any] | None:
    assert self.db
    res = await self.db.run(
      get_ledger_by_name_request(GetLedgerByNameParams(element_name=element_name))
    )
    if not res.rows:
      return None
    return self._map_ledger(dict(res.rows[0]))

  async def _validate_ledger_name(self, element_name: str, recid: int | None = None) -> str:
    normalized_name = element_name.strip()
    if not normalized_name:
      raise ValueError("Ledger name is required")

    existing = await self._get_ledger_by_name(normalized_name)
    if existing and existing.get("recid") != recid:
      raise ValueError(f"Ledger '{normalized_name}' already exists")
    return normalized_name

  async def _validate_chart_of_accounts_guid(self, chart_of_accounts_guid: str | None) -> str | None:
    if not chart_of_accounts_guid:
      return None

    account = await self.get_account(chart_of_accounts_guid)
    if not account:
      raise ValueError("Selected chart of accounts account was not found")
    return chart_of_accounts_guid

  @staticmethod
  def _validate_period_status(status: int) -> int:
    if status not in {1, 2, 3}:
      raise ValueError("Period status must be Open (1), Closed (2), or Locked (3)")
    return status

  async def create_ledger(self, data: dict[str, Any]) -> dict[str, Any]:
    assert self.db
    params = CreateLedgerParams(
      element_name=await self._validate_ledger_name(data.get("element_name", "")),
      element_description=(data.get("element_description") or None),
      element_chart_of_accounts_guid=await self._validate_chart_of_accounts_guid(
        data.get("element_chart_of_accounts_guid")
      ),
      element_status=1,
    )
    res = await self.db.run(create_ledger_request(params))
    if not res.rows:
      raise ValueError("Ledger create did not return a row")
    return self._map_ledger(dict(res.rows[0]))

  async def update_ledger(self, data: dict[str, Any]) -> dict[str, Any]:
    assert self.db
    recid = int(data["recid"])
    existing = await self.get_ledger(recid)
    if not existing:
      raise ValueError("Ledger not found")

    params = UpdateLedgerParams(
      recid=recid,
      element_name=await self._validate_ledger_name(data.get("element_name", ""), recid=recid),
      element_description=(data.get("element_description") or None),
      element_chart_of_accounts_guid=await self._validate_chart_of_accounts_guid(
        data.get("element_chart_of_accounts_guid")
      ),
      element_status=int(data.get("element_status", existing.get("element_status") or 1)),
    )
    res = await self.db.run(update_ledger_request(params))
    if not res.rows:
      raise ValueError("Ledger update did not return a row")
    return self._map_ledger(dict(res.rows[0]))

  async def delete_ledger(self, recid: int) -> dict[str, Any]:
    assert self.db
    existing = await self.get_ledger(recid)
    if not existing:
      raise ValueError("Ledger not found")

    reference_res = await self.db.run(
      journal_reference_count_request(JournalReferenceCountParams(recid=recid))
    )
    journal_count = 0
    if reference_res.rows:
      journal_count = int(reference_res.rows[0].get("journal_count") or 0)
    if journal_count > 0:
      raise ValueError("Ledger cannot be deleted because journals already reference it")

    await self.db.run(delete_ledger_request(DeleteLedgerParams(recid=recid)))
    return {**existing, "element_status": 0}

  async def generate_calendar(self, fiscal_year: int, start_date: str | None = None) -> list[dict[str, Any]]:
    existing = await self.list_periods_by_year(fiscal_year)
    if existing:
      raise ValueError(f"Fiscal year {fiscal_year} already has generated periods")

    fy_start = datetime.fromisoformat(start_date).date() if start_date else self._nearest_sunday_for_fiscal_year(fiscal_year)
    if fy_start.weekday() != 6:
      raise ValueError("start_date must be a Sunday")

    next_fy_start = self._nearest_sunday_for_fiscal_year(fiscal_year + 1)
    fiscal_year_days = (next_fy_start - fy_start).days
    if fiscal_year_days not in {364, 371}:
      raise ValueError(f"Fiscal year {fiscal_year} produced unsupported length {fiscal_year_days}")

    generated: list[dict[str, Any]] = []
    cursor = fy_start
    period_number = 1

    for quarter in range(1, 5):
      for month_idx in range(1, 4):
        end = cursor + timedelta(days=27)
        payload = {
          "guid": None,
          "year": fiscal_year,
          "period_number": period_number,
          "period_name": f"Q{quarter}M{month_idx}",
          "start_date": cursor.isoformat(),
          "end_date": end.isoformat(),
          "days_in_period": 28,
          "quarter_number": quarter,
          "has_closing_week": False,
          "is_leap_adjustment": False,
          "anchor_event": None,
          "close_type": 0,
          "status": 1,
          "numbers_recid": None,
        }
        row = await self.upsert_period(payload)
        generated.append(row)
        cursor = end + timedelta(days=1)
        period_number += 1

      closing_days = 14 if quarter == 4 and fiscal_year_days == 371 else 7
      closing_end = cursor + timedelta(days=closing_days - 1)
      closing_payload = {
        "guid": None,
        "year": fiscal_year,
        "period_number": period_number,
        "period_name": f"Q{quarter}MC",
        "start_date": cursor.isoformat(),
        "end_date": closing_end.isoformat(),
        "days_in_period": closing_days,
        "quarter_number": quarter,
        "has_closing_week": True,
        "is_leap_adjustment": quarter == 4 and fiscal_year_days == 371,
        "anchor_event": "period_close",
        "close_type": 2 if quarter == 4 else 1,
        "status": 1,
        "numbers_recid": None,
      }
      row = await self.upsert_period(closing_payload)
      generated.append(row)
      cursor = closing_end + timedelta(days=1)
      period_number += 1

    if cursor != fy_start + timedelta(days=fiscal_year_days):
      raise ValueError(f"Generated fiscal year {fiscal_year} length {(cursor - fy_start).days} instead of {fiscal_year_days}")

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
    clean = {key: value for key, value in data.items() if key not in _UPSERT_NUMBER_STRIP}
    if clean.get("recid") and clean.get("max_number") is not None:
      existing = await self.get_number(clean["recid"])
      if existing and clean["max_number"] < existing["last_number"]:
        raise ValueError(
          f"Cannot set max_number ({clean['max_number']}) below "
          f"last_number ({existing['last_number']})"
        )
    params = UpsertNumberParams(**clean)
    res = await self.db.run(upsert_number_request(params))
    row = dict(res.rows[0]) if res.rows else params.model_dump()
    return self._map_number(row)

  async def shift_sequence(self, data: dict[str, Any]) -> dict[str, Any]:
    """Close the current active sequence and create a new one for the same account.

    The old sequence is preserved with its consumed numbers.
    The new sequence starts at 0 with a max derived from the display format.
    """
    assert self.db
    current_recid = data["current_recid"]

    current = await self.get_number(current_recid)
    if not current:
      raise ValueError(f"Sequence {current_recid} not found")
    if current.get("sequence_status") != 1:
      raise ValueError(f"Sequence {current_recid} is not active")

    close_res = await self.db.run(
      close_sequence_request(CloseSequenceParams(recid=current_recid))
    )
    if not close_res.rows:
      raise ValueError(f"Failed to close sequence {current_recid}")

    new_data = {
      "accounts_guid": current["accounts_guid"],
      "prefix": data.get("new_prefix") or current.get("prefix"),
      "account_number": data["new_account_number"],
      "last_number": 0,
      "allocation_size": data.get("new_allocation_size", 1),
      "reset_policy": "Never",
      "sequence_status": 1,
      "pattern": data.get("new_pattern") or current.get("pattern"),
      "display_format": data.get("new_display_format") or current.get("display_format"),
    }
    new_sequence = await self.upsert_number(new_data)

    return {
      "closed_sequence": self._map_number(dict(close_res.rows[0])) if close_res.rows else None,
      "new_sequence": new_sequence,
    }


  async def delete_number(self, recid: int) -> dict[str, Any]:
    assert self.db
    await self.db.run(delete_number_request(DeleteNumberParams(recid=recid)))
    return {"recid": recid}

  async def next_number(self, recid: int) -> dict[str, Any] | None:
    assert self.db
    res = await self.db.run(next_number_request(NextNumberParams(recid=recid)))
    if not res.rows:
      raise ValueError(f"Number sequence {recid} is exhausted or inactive")
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

  async def _next_formatted_number(self, prefix: str, account_number: str) -> tuple[str, int]:
    """Get next number from a sequence and format it using the configured pattern."""
    assert self.db
    lookup_res = await self.db.run(
      get_by_prefix_account_number_request(
        GetByPrefixAndAccountNumberParams(prefix=prefix, account_number=account_number)
      )
    )
    if not lookup_res.rows:
      raise ValueError(f"Number sequence not found: prefix={prefix} account_number={account_number}")

    seq_row = dict(lookup_res.rows[0])
    numbers_recid = int(seq_row["recid"])

    next_res = await self.db.run(next_number_request(NextNumberParams(recid=numbers_recid)))
    if not next_res.rows:
      raise ValueError(f"Number sequence {numbers_recid} is exhausted or inactive")

    result = dict(next_res.rows[0])
    next_val = int(result.get("element_block_start", result.get("element_last_number", 0)))
    pattern = seq_row.get("element_pattern") or seq_row.get("element_display_format")

    if pattern and "{number" in pattern:
      formatted = pattern.format(number=next_val)
    elif pattern:
      formatted = f"{pattern}{next_val}"
    else:
      prefix_str = seq_row.get("element_prefix") or ""
      formatted = f"{prefix_str}{next_val:06d}"

    return formatted, numbers_recid

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

    journal_number = None
    journal_numbers_recid = None
    if not posting_key:
      journal_number, journal_numbers_recid = await self._next_formatted_number("JRN", "JRN-SEQ")
      posting_key = journal_number

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
          name=journal_number or name,
          description=description,
          posting_key=posting_key,
          source_type=source_type,
          source_id=source_id,
          periods_guid=periods_guid,
          ledgers_recid=ledgers_recid,
          numbers_recid=journal_numbers_recid,
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

  async def list_lots_by_user(self, users_guid: str) -> list[dict[str, Any]]:
    assert self.db
    res = await self.db.run(list_lots_by_user_request(ListLotsByUserParams(users_guid=users_guid)))
    return [self._map_lot(row) for row in res.rows]

  async def get_lot(self, recid: int) -> dict[str, Any] | None:
    assert self.db
    res = await self.db.run(get_lot_request(GetLotParams(recid=recid)))
    if not res.rows:
      return None
    return self._map_lot(dict(res.rows[0]))

  async def list_lot_events(self, lots_recid: int) -> list[dict[str, Any]]:
    assert self.db
    res = await self.db.run(list_events_by_lot_request(ListEventsByLotParams(lots_recid=lots_recid)))
    return [self._map_lot_event(row) for row in res.rows]

  async def get_wallet_balance(self, users_guid: str) -> int:
    """Get total remaining credits across all active lots for a user."""
    assert self.db
    res = await self.db.run(sum_remaining_by_user_request(SumRemainingByUserParams(users_guid=users_guid)))
    row = dict(res.rows[0]) if res.rows else {}
    total = row.get("total_remaining", 0)
    return int(total or 0)

  async def _get_account_guid_by_number(self, account_number: str) -> str:
    """Look up an account GUID by its account number."""
    accounts = await self.list_accounts()
    for acct in accounts:
      if acct["number"] == account_number:
        return acct["guid"]
    raise ValueError(f"Account {account_number} not found")

  async def _sync_wallet(self, users_guid: str) -> None:
    """Sync the users_credits wallet balance from lot totals."""
    assert self.db
    total = await self.get_wallet_balance(users_guid)
    await self.db.run(set_credits_request(SetCreditsParams(guid=users_guid, credits=total)))

  async def create_lot(
    self,
    *,
    users_guid: str,
    source_type: str,
    credits: int,
    total_paid: str = "0",
    currency: str = "USD",
    expires_at: str | None = None,
    source_id: str | None = None,
    actor_guid: str | None = None,
  ) -> dict[str, Any]:
    assert self.db

    total_paid_decimal = self._to_decimal(total_paid)
    unit_price = Decimal("0")
    if credits > 0 and total_paid_decimal > Decimal("0"):
      unit_price = self._quantize_5dp(total_paid_decimal / Decimal(credits))

    lot_number, numbers_recid = await self._next_formatted_number("LOT", "LOT-SEQ")
    lot_res = await self.db.run(
      create_lot_request(
        CreateLotParams(
          users_guid=users_guid,
          lot_number=lot_number,
          source_type=source_type,
          credits_original=credits,
          credits_remaining=credits,
          unit_price=str(unit_price),
          total_paid=str(total_paid_decimal),
          currency=currency,
          expires_at=expires_at,
          source_id=source_id,
          numbers_recid=numbers_recid,
          status=1,
        )
      )
    )
    if not lot_res.rows:
      raise ValueError("Failed to create credit lot")

    created = self._map_lot(dict(lot_res.rows[0]))
    await self.db.run(
      create_event_request(
        CreateEventParams(
          lots_recid=int(created["recid"]),
          event_type="Purchase" if source_type == "purchase" else "Grant",
          credits=credits,
          unit_price=str(unit_price),
          actor_guid=actor_guid,
        )
      )
    )
    await self._sync_wallet(users_guid)
    return created

  async def expire_lot(self, recid: int, actor_guid: str | None = None) -> dict[str, Any] | None:
    assert self.db
    lot = await self.get_lot(recid)
    if not lot:
      return None

    expired_res = await self.db.run(expire_lot_request(ExpireLotParams(recid=recid)))
    if expired_res.rowcount == 0:
      return None

    expired_lot = await self.get_lot(recid)
    if not expired_lot:
      return None
    expired = self._map_lot(expired_lot) if isinstance(expired_lot, dict) else expired_lot
    remaining_before = int(lot.get("credits_remaining") or 0)
    if remaining_before > 0:
      await self.db.run(
        create_event_request(
          CreateEventParams(
            lots_recid=recid,
            event_type="Expire",
            credits=remaining_before,
            unit_price=str(lot.get("unit_price") or "0"),
            actor_guid=actor_guid,
          )
        )
      )
    await self._sync_wallet(str(expired["users_guid"]))
    return expired

  async def consume_credits(
    self,
    *,
    users_guid: str,
    credits_needed: int,
    service_type: str | None = None,
    description: str | None = None,
    actor_guid: str | None = None,
    periods_guid: str | None = None,
  ) -> dict[str, Any]:
    assert self.db

    if credits_needed <= 0:
      raise ValueError("credits_needed must be greater than zero")

    lots_res = await self.db.run(list_lots_by_user_request(ListLotsByUserParams(users_guid=users_guid)))
    lots = [self._map_lot(row) for row in lots_res.rows]

    remaining_need = credits_needed
    consumed_lots: list[tuple[dict[str, Any], int]] = []
    for lot in lots:
      if remaining_need <= 0:
        break
      available = int(lot.get("credits_remaining") or 0)
      if available <= 0:
        continue
      take = min(available, remaining_need)
      consume_res = await self.db.run(
        consume_credits_request(ConsumeCreditsParams(recid=int(lot["recid"]), credits_to_consume=take))
      )
      if consume_res.rowcount == 0:
        continue
      consumed_lots.append((lot, take))
      remaining_need -= take

    if remaining_need > 0:
      available = credits_needed - remaining_need
      raise ValueError(f"Insufficient credits: needed {credits_needed}, available {available}")

    recognized_revenue = Decimal("0")
    for lot, take in consumed_lots:
      if lot.get("source_type") == "purchase":
        recognized_revenue += self._quantize_5dp(Decimal(take) * self._to_decimal(lot.get("unit_price", "0")))

    journal: dict[str, Any] | None = None
    if recognized_revenue > Decimal("0"):
      deferred_revenue_guid = await self._get_account_guid_by_number("2100")
      recognized_revenue_guid = await self._get_account_guid_by_number("4010")
      journal = await self.create_journal(
        name=f"REV-{users_guid[:8]}-{credits_needed}",
        source_type="credit_consumption",
        source_id=users_guid,
        periods_guid=periods_guid,
        lines=[
          {
            "line_number": 1,
            "accounts_guid": deferred_revenue_guid,
            "debit": str(recognized_revenue),
            "credit": "0",
            "description": description or service_type,
          },
          {
            "line_number": 2,
            "accounts_guid": recognized_revenue_guid,
            "debit": "0",
            "credit": str(recognized_revenue),
            "description": description or service_type,
          },
        ],
        post=True,
        posted_by=actor_guid,
      )

    for lot, take in consumed_lots:
      event_journal_recid = None
      if journal and lot.get("source_type") == "purchase":
        event_journal_recid = int(journal["recid"])
      await self.db.run(
        create_event_request(
          CreateEventParams(
            lots_recid=int(lot["recid"]),
            event_type="Consume",
            credits=take,
            unit_price=str(lot.get("unit_price") or "0"),
            description=description or service_type,
            actor_guid=actor_guid,
            journals_recid=event_journal_recid,
          )
        )
      )

    await self._sync_wallet(users_guid)
    return {
      "credits_consumed": credits_needed,
      "lots_affected": len(consumed_lots),
      "journal_recid": int(journal["recid"]) if journal else None,
    }
