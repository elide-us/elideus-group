from __future__ import annotations

import logging
import json
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
  get_by_scope_request,
  get_number_request,
  list_numbers_request,
  next_number_by_scope_request,
  next_number_request,
  upsert_number_request,
)
from queryregistry.finance.numbers.models import (
  CloseSequenceParams,
  DeleteNumberParams,
  GetByScopeParams,
  GetNumberParams,
  ListNumbersParams,
  NextNumberByScopeParams,
  NextNumberParams,
  UpsertNumberParams,
)
from queryregistry.finance.periods import (
  close_period_request,
  delete_period_request,
  get_period_request,
  list_period_close_blockers_request,
  list_periods_by_year_request,
  list_periods_request,
  lock_period_request,
  reopen_period_request,
  unlock_period_request,
  upsert_period_request,
)
from queryregistry.finance.periods.models import (
  ClosePeriodParams,
  DeletePeriodParams,
  GetPeriodParams,
  ListPeriodCloseBlockersParams,
  ListPeriodsByYearParams,
  ListPeriodsParams,
  LockPeriodParams,
  ReopenPeriodParams,
  UnlockPeriodParams,
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
  get_credits_request,
  set_credits_request,
)
from queryregistry.finance.credits.models import (
  GetCreditsParams,
  SetCreditsParams,
)
from queryregistry.finance.pipeline_config import (
  delete_pipeline_config_request,
  get_pipeline_config_request,
  list_pipeline_configs_request,
  upsert_pipeline_config_request,
)
from queryregistry.finance.pipeline_config.models import (
  DeletePipelineConfigParams,
  GetPipelineConfigParams,
  ListPipelineConfigsParams,
  UpsertPipelineConfigParams,
)
from queryregistry.finance.products import (
  delete_product_request,
  get_product_request,
  list_products_request,
  upsert_product_request,
)
from queryregistry.finance.products.models import (
  DeleteProductParams,
  GetProductParams,
  ListProductsParams,
  UpsertProductParams,
)
from queryregistry.finance.product_journal_config import (
  activate_product_journal_config_request,
  approve_product_journal_config_request,
  close_product_journal_config_request,
  get_active_product_journal_config_request,
  get_product_journal_config_request,
  list_product_journal_config_request,
  upsert_product_journal_config_request,
)
from queryregistry.finance.product_journal_config.models import (
  ActivateProductJournalConfigParams,
  ApproveProductJournalConfigParams,
  CloseProductJournalConfigParams,
  GetActiveConfigParams,
  GetProductJournalConfigParams,
  ListProductJournalConfigParams,
  UpsertProductJournalConfigParams,
)
from queryregistry.finance.reporting import (
  credit_lot_summary_request,
  journal_summary_request,
  period_status_request,
  trial_balance_request,
)
from queryregistry.finance.reporting.models import (
  CreditLotSummaryParams,
  JournalSummaryParams,
  PeriodStatusParams,
  TrialBalanceParams,
)
from queryregistry.finance.staging import (
  approve_import_request,
  create_import_request,
  delete_import_request,
  list_cost_details_by_import_request,
  list_imports_request,
  reject_import_request,
  update_import_status_request,
)
from queryregistry.finance.staging.models import (
  ApproveImportParams,
  CreateImportParams,
  DeleteImportParams,
  ListCostDetailsByImportParams,
  ListImportsParams,
  RejectImportParams,
  UpdateImportStatusParams,
)
from queryregistry.finance.staging_account_map import (
  delete_account_map_request,
  list_account_map_request,
  upsert_account_map_request,
)
from queryregistry.finance.staging_account_map.models import (
  DeleteAccountMapParams,
  ListAccountMapParams,
  UpsertAccountMapParams,
)
from queryregistry.finance.staging_line_items import (
  insert_line_items_batch_request,
  list_line_items_by_import_request,
)
from queryregistry.finance.staging_line_items.models import (
  InsertLineItemsBatchParams,
  ListLineItemsByImportParams,
)
from queryregistry.finance.staging_purge_log import list_purge_logs_request
from queryregistry.finance.staging_purge_log.models import ListPurgeLogsParams
from queryregistry.finance.status import get_status_code_request, list_status_codes_request
from queryregistry.finance.status.models import GetStatusCodeParams, ListStatusCodesParams
from queryregistry.finance.vendors import (
  delete_vendor_request,
  get_vendor_by_name_request,
  list_vendors_request,
  upsert_vendor_request,
)
from queryregistry.finance.vendors.models import (
  GetVendorByNameParams,
  DeleteVendorParams,
  ListVendorsParams,
  UpsertVendorParams,
)
from queryregistry.identity.enablements import (
  get_user_enablements_request,
  upsert_user_enablements_request,
)
from queryregistry.identity.enablements.models import (
  GetUserEnablementsParams,
  UpsertUserEnablementsParams,
)
from queryregistry.identity.profiles import get_roles_request, set_roles_request
from queryregistry.identity.profiles.models import GuidParams, SetRolesParams

from .models.finance_statuses import (
  CLOSE_TYPE_ANNUAL,
  CLOSE_TYPE_NONE,
  CLOSE_TYPE_QUARTERLY,
  CREDIT_LOT_ACTIVE,
  ELEMENT_ACTIVE,
  ELEMENT_INACTIVE,
  IMPORT_APPROVED,
  IMPORT_FAILED,
  IMPORT_PENDING,
  IMPORT_PENDING_APPROVAL,
  IMPORT_PROMOTED,
  IMPORT_REJECTED,
  JOURNAL_DRAFT,
  JOURNAL_PENDING_APPROVAL,
  JOURNAL_POSTED,
  JOURNAL_REVERSED,
  PERIOD_CLOSED,
  PERIOD_LOCKED,
  PERIOD_OPEN,
)


_FIVE_PLACES = Decimal("0.00001")
_FOUR_PLACES = Decimal("0.0001")
_UPSERT_NUMBER_STRIP = frozenset({"account_name", "remaining"})


class FinanceModule(BaseModule):
  def __init__(self, app: FastAPI):
    super().__init__(app)
    self.db: DbModule | None = None
    self._pipeline_config_cache: dict[tuple[str, str], str] = {}

  async def startup(self):
    self.db = self.app.state.db
    await self.db.on_ready()
    self.app.state.finance = self
    logging.debug("[FinanceModule] loaded")
    self.mark_ready()

  async def shutdown(self):
    logging.info("[FinanceModule] shutdown")
    self.db = None
    self._pipeline_config_cache = {}

  async def get_user_credits(self, guid: str) -> dict[str, Any]:
    assert self.db
    res = await self.db.run(get_credits_request(GetCreditsParams(guid=guid)))
    return dict(res.rows[0]) if res.rows else {}

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
      "closed_by": row.get("element_closed_by"),
      "closed_on": row.get("element_closed_on"),
      "locked_by": row.get("element_locked_by"),
      "locked_on": row.get("element_locked_on"),
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
      "sequence_type": row.get("element_sequence_type"),
      "series_number": row.get("element_series_number"),
      "scope": row.get("element_scope"),
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

  def _map_product(self, row: dict[str, Any]) -> dict[str, Any]:
    return {
      "recid": row.get("recid"),
      "sku": row.get("element_sku"),
      "name": row.get("element_name"),
      "description": row.get("element_description"),
      "category": row.get("element_category"),
      "price": str(row.get("element_price") or "0"),
      "currency": row.get("element_currency"),
      "credits": int(row.get("element_credits") or 0),
      "enablement_key": row.get("element_enablement_key"),
      "is_recurring": bool(row.get("element_is_recurring") or False),
      "sort_order": int(row.get("element_sort_order") or 0),
      "status": int(row.get("element_status") or 0),
      "created_on": row.get("element_created_on"),
      "modified_on": row.get("element_modified_on"),
    }

  def _map_product_journal_config(self, row: dict[str, Any]) -> dict[str, Any]:
    return {
      "recid": int(row.get("recid") or 0),
      "category": row.get("element_category"),
      "journal_scope": row.get("element_journal_scope"),
      "journals_recid": int(row.get("journals_recid") or 0),
      "periods_guid": str(row.get("periods_guid") or ""),
      "approved_by": row.get("element_approved_by"),
      "approved_on": row.get("element_approved_on"),
      "activated_by": row.get("element_activated_by"),
      "activated_on": row.get("element_activated_on"),
      "status": int(row.get("element_status") or 0),
      "created_on": row.get("element_created_on"),
      "modified_on": row.get("element_modified_on"),
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

  async def list_period_close_blockers(self, period_guid: str) -> list[dict[str, Any]]:
    assert self.db
    res = await self.db.run(
      list_period_close_blockers_request(ListPeriodCloseBlockersParams(period_guid=period_guid))
    )
    return [dict(row) for row in res.rows]

  async def close_period(self, guid: str, closed_by: str) -> dict[str, Any]:
    assert self.db
    period = await self.get_period(guid)
    if not period:
      raise ValueError("Period not found")
    if int(period.get("status") or ELEMENT_INACTIVE) != PERIOD_OPEN:
      raise ValueError("Only open periods can be closed")

    blockers = await self.list_period_close_blockers(guid)
    if blockers:
      label_map = {
        "journal": "journal blocker(s)",
        "import": "import blocker(s)",
        "credit_lot_revrec": "credit lot revenue recognition blocker(s)",
      }
      counts: dict[str, int] = {}
      for blocker in blockers:
        blocker_type = str(blocker.get("blocker_type") or "unknown")
        counts[blocker_type] = counts.get(blocker_type, 0) + 1
      summary = ", ".join(
        f"{count} {label_map.get(blocker_type, blocker_type)}"
        for blocker_type, count in sorted(counts.items())
      )
      raise ValueError(f"Cannot close period: {summary}")

    res = await self.db.run(close_period_request(ClosePeriodParams(guid=guid, closed_by=closed_by)))
    if not res.rows:
      raise ValueError("Period status was modified concurrently")
    return self._map_period(dict(res.rows[0]))

  async def reopen_period(self, guid: str) -> dict[str, Any]:
    assert self.db
    period = await self.get_period(guid)
    if not period:
      raise ValueError("Period not found")
    if int(period.get("status") or ELEMENT_INACTIVE) != PERIOD_CLOSED:
      raise ValueError("Only closed periods can be reopened")

    res = await self.db.run(reopen_period_request(ReopenPeriodParams(guid=guid)))
    if not res.rows:
      raise ValueError("Period status was modified concurrently")
    return self._map_period(dict(res.rows[0]))

  async def lock_period(self, guid: str, locked_by: str) -> dict[str, Any]:
    assert self.db
    period = await self.get_period(guid)
    if not period:
      raise ValueError("Period not found")
    if int(period.get("status") or ELEMENT_INACTIVE) != PERIOD_CLOSED:
      raise ValueError("Only closed periods can be locked")

    res = await self.db.run(lock_period_request(LockPeriodParams(guid=guid, locked_by=locked_by)))
    if not res.rows:
      raise ValueError("Period status was modified concurrently")
    return self._map_period(dict(res.rows[0]))

  async def unlock_period(self, guid: str) -> dict[str, Any]:
    assert self.db
    period = await self.get_period(guid)
    if not period:
      raise ValueError("Period not found")
    if int(period.get("status") or ELEMENT_INACTIVE) != PERIOD_LOCKED:
      raise ValueError("Only locked periods can be unlocked")

    res = await self.db.run(unlock_period_request(UnlockPeriodParams(guid=guid)))
    if not res.rows:
      raise ValueError("Period status was modified concurrently")
    return self._map_period(dict(res.rows[0]))

  async def upsert_period(self, data: dict[str, Any]) -> dict[str, Any]:
    assert self.db
    next_data = dict(data)
    next_data["status"] = self._validate_period_status(int(next_data.get("status", PERIOD_OPEN)))
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
    if status not in {PERIOD_OPEN, PERIOD_CLOSED, PERIOD_LOCKED}:
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
      element_status=ELEMENT_ACTIVE,
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
      element_status=int(data.get("element_status", existing.get("element_status") or ELEMENT_ACTIVE)),
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
    return {**existing, "element_status": ELEMENT_INACTIVE}

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
          "close_type": CLOSE_TYPE_NONE,
          "status": PERIOD_OPEN,
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
        "close_type": CLOSE_TYPE_ANNUAL if quarter == 4 else CLOSE_TYPE_QUARTERLY,
        "status": PERIOD_OPEN,
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
    """Close the current active sequence and create the next series entry."""
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
      "sequence_type": current.get("sequence_type") or "continuous",
      "series_number": int(current.get("series_number") or 1) + 1,
      "scope": current.get("scope"),
      "pattern": data.get("new_pattern") or current.get("pattern"),
      "display_format": data.get("new_display_format") or current.get("display_format"),
      "max_number": current.get("max_number"),
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

  @staticmethod
  def _journal_sequence_scope(source_type: str | None) -> str:
    scope_map = {
      "azure_invoice": "billing_import",
      "azure_billing_import": "billing_import",
      "billing_import": "billing_import",
      "equity_contribution": "equity_contribution",
      "credit_purchase": "credit_purchase",
      "credit_consumption": "credit_consumption",
      "reversal": "reversal",
      "refund": "refund",
      "chargeback": "refund",
    }
    return scope_map.get(str(source_type or "").strip(), "general")

  async def _get_number_by_scope(self, prefix: str, scope: str) -> dict[str, Any] | None:
    assert self.db
    res = await self.db.run(
      get_by_scope_request(GetByScopeParams(prefix=prefix, scope=scope))
    )
    if not res.rows:
      return None
    return dict(res.rows[0])

  async def _rollover_number_sequence(self, prefix: str, scope: str, current: dict[str, Any]) -> dict[str, Any]:
    assert self.db
    close_res = await self.db.run(
      close_sequence_request(CloseSequenceParams(recid=int(current["recid"])))
    )
    if not close_res.rows:
      replacement = await self._get_number_by_scope(prefix, scope)
      if replacement:
        return replacement
      raise ValueError(
        f"Failed to close exhausted number sequence {current['recid']} for prefix={prefix} scope={scope}"
      )

    next_series = int(current.get("element_series_number", 1) or 1) + 1
    new_sequence = await self.upsert_number(
      {
        "accounts_guid": current["accounts_guid"],
        "prefix": current.get("element_prefix") or prefix,
        "account_number": current["element_account_number"],
        "last_number": 0,
        "max_number": current.get("element_max_number"),
        "allocation_size": current.get("element_allocation_size", 1),
        "reset_policy": current.get("element_reset_policy") or "Never",
        "sequence_status": 1,
        "sequence_type": current.get("element_sequence_type") or "continuous",
        "series_number": next_series,
        "scope": current.get("element_scope") or scope,
        "pattern": current.get("element_pattern"),
        "display_format": current.get("element_display_format"),
      }
    )
    rolled = await self._get_number_by_scope(prefix, scope)
    if rolled:
      return rolled
    return {
      "recid": new_sequence["recid"],
      "accounts_guid": new_sequence["accounts_guid"],
      "element_prefix": new_sequence.get("prefix"),
      "element_account_number": new_sequence["account_number"],
      "element_last_number": new_sequence["last_number"],
      "element_max_number": new_sequence.get("max_number"),
      "element_allocation_size": new_sequence["allocation_size"],
      "element_reset_policy": new_sequence["reset_policy"],
      "element_sequence_status": new_sequence["sequence_status"],
      "element_sequence_type": new_sequence.get("sequence_type"),
      "element_series_number": new_sequence.get("series_number"),
      "element_scope": new_sequence.get("scope"),
      "element_pattern": new_sequence.get("pattern"),
      "element_display_format": new_sequence.get("display_format"),
    }

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

  async def list_imports(self, status: int | None = None) -> list[dict[str, Any]]:
    assert self.db
    res = await self.db.run(list_imports_request(ListImportsParams(status=status)))
    return [dict(row) for row in res.rows]

  async def get_import(self, recid: int) -> dict[str, Any] | None:
    rows = await self.list_imports()
    for row in rows:
      if int(row.get("recid") or 0) == recid:
        return row
    return None

  async def list_cost_details_by_import(self, imports_recid: int) -> list[dict[str, Any]]:
    assert self.db
    res = await self.db.run(
      list_cost_details_by_import_request(
        ListCostDetailsByImportParams(imports_recid=imports_recid),
      )
    )
    return [dict(row) for row in res.rows]

  async def list_line_items_by_import(self, imports_recid: int) -> list[dict[str, Any]]:
    assert self.db
    import_row = await self.get_import(imports_recid)
    if not import_row:
      raise ValueError("Import not found")
    res = await self.db.run(
      list_line_items_by_import_request(ListLineItemsByImportParams(imports_recid=imports_recid))
    )
    return [dict(row) for row in res.rows]

  async def delete_import(self, recid: int) -> dict[str, Any]:
    assert self.db
    import_row = await self.get_import(recid)
    if not import_row:
      raise ValueError("Import not found")
    if int(import_row.get("element_status") or IMPORT_PENDING) == IMPORT_PROMOTED:
      raise ValueError("Promoted imports cannot be deleted")
    await self.db.run(delete_import_request(DeleteImportParams(imports_recid=recid)))
    return {"imports_recid": recid, "deleted": True}

  async def approve_import(self, imports_recid: int, approved_by: str) -> dict[str, Any]:
    assert self.db
    import_row = await self.get_import(imports_recid)
    if not import_row:
      raise ValueError("Import not found")
    if int(import_row.get("element_status") or IMPORT_PENDING) != IMPORT_PENDING_APPROVAL:
      raise ValueError("Only imports pending approval can be approved")
    await self.db.run(
      approve_import_request(
        ApproveImportParams(imports_recid=imports_recid, approved_by=approved_by)
      )
    )
    updated = await self.get_import(imports_recid)
    if not updated:
      raise ValueError("Approved import could not be reloaded")
    return updated

  async def reject_import(
    self,
    imports_recid: int,
    approved_by: str,
    reason: str | None = None,
  ) -> dict[str, Any]:
    assert self.db
    import_row = await self.get_import(imports_recid)
    if not import_row:
      raise ValueError("Import not found")
    if int(import_row.get("element_status") or IMPORT_PENDING) != IMPORT_PENDING_APPROVAL:
      raise ValueError("Only imports pending approval can be rejected")
    await self.db.run(
      reject_import_request(
        RejectImportParams(
          imports_recid=imports_recid,
          approved_by=approved_by,
          reason=reason,
        )
      )
    )
    updated = await self.get_import(imports_recid)
    if not updated:
      raise ValueError("Rejected import could not be reloaded")
    return updated

  async def trial_balance(

    self,
    fiscal_year: int | None = None,
    period_guid: str | None = None,
  ) -> list[dict[str, Any]]:
    assert self.db
    res = await self.db.run(
      trial_balance_request(
        TrialBalanceParams(fiscal_year=fiscal_year, period_guid=period_guid)
      )
    )
    return [dict(row) for row in res.rows]

  async def journal_summary(
    self,
    journal_status: int | None = None,
    fiscal_year: int | None = None,
    periods_guid: str | None = None,
  ) -> list[dict[str, Any]]:
    assert self.db
    res = await self.db.run(
      journal_summary_request(
        JournalSummaryParams(
          journal_status=journal_status,
          fiscal_year=fiscal_year,
          periods_guid=periods_guid,
        )
      )
    )
    return [dict(row) for row in res.rows]

  async def period_status(self, fiscal_year: int | None = None) -> list[dict[str, Any]]:
    assert self.db
    res = await self.db.run(period_status_request(PeriodStatusParams(fiscal_year=fiscal_year)))
    return [dict(row) for row in res.rows]

  async def credit_lot_summary(self, users_guid: str | None = None) -> list[dict[str, Any]]:
    assert self.db
    res = await self.db.run(
      credit_lot_summary_request(CreditLotSummaryParams(users_guid=users_guid))
    )
    return [dict(row) for row in res.rows]

  async def list_account_mappings(self) -> list[dict[str, Any]]:
    assert self.db
    res = await self.db.run(list_account_map_request(ListAccountMapParams()))
    return [dict(row) for row in res.rows]

  async def upsert_account_mapping(self, data: dict[str, Any]) -> dict[str, Any]:
    assert self.db
    params = UpsertAccountMapParams(**data)
    res = await self.db.run(upsert_account_map_request(params))
    return dict(res.rows[0]) if res.rows else params.model_dump()

  async def delete_account_mapping(self, recid: int) -> dict[str, Any]:
    assert self.db
    await self.db.run(delete_account_map_request(DeleteAccountMapParams(recid=recid)))
    return {"recid": recid, "deleted": True}

  async def list_vendors(self) -> list[dict[str, Any]]:
    assert self.db
    res = await self.db.run(list_vendors_request(ListVendorsParams()))
    return [dict(row) for row in res.rows]

  async def upsert_vendor(self, data: dict[str, Any]) -> dict[str, Any]:
    assert self.db
    params = UpsertVendorParams(**data)
    res = await self.db.run(upsert_vendor_request(params))
    return dict(res.rows[0]) if res.rows else params.model_dump()

  async def delete_vendor(self, recid: int) -> dict[str, Any]:
    assert self.db
    await self.db.run(delete_vendor_request(DeleteVendorParams(recid=recid)))
    return {"recid": recid, "deleted": True}

  async def create_payment_request(self, payload: dict[str, Any], requested_by: str) -> dict[str, Any]:
    assert self.db
    vendor_name = str(payload.get("vendor_name") or "").strip()
    if not vendor_name:
      raise ValueError("vendor_name is required")

    vendor_result = await self.db.run(
      get_vendor_by_name_request(GetVendorByNameParams(element_name=vendor_name)),
    )
    if not vendor_result.rows:
      raise ValueError(f"Unknown vendor: {vendor_name}")
    vendor_recid = int(vendor_result.rows[0]["recid"])

    create_result = await self.db.run(
      create_import_request(
        CreateImportParams(
          source="payment_request",
          scope=f"vendor/{vendor_name}",
          metric="PaymentRequest",
          period_start=payload.get("period_start"),
          period_end=payload.get("period_end"),
          requested_by=requested_by,
          initial_status=IMPORT_PENDING_APPROVAL,
        ),
      ),
    )
    if not create_result.rows:
      raise RuntimeError("Failed to create staging import record")
    import_recid = int(create_result.rows[0]["recid"])

    raw_data = {
      "vendor_name": vendor_name,
      "description": payload.get("description"),
    }
    if payload.get("renewal_recid") is not None:
      raw_data["renewal_recid"] = payload.get("renewal_recid")

    line_item = {
      "element_date": payload.get("period_start"),
      "element_service": payload.get("service") or vendor_name,
      "element_category": payload.get("category") or "PaymentRequest",
      "element_description": payload.get("description"),
      "element_quantity": "1.0",
      "element_unit_price": payload.get("amount"),
      "element_amount": payload.get("amount"),
      "element_currency": payload.get("currency"),
      "element_raw_json": json.dumps(raw_data),
      "element_record_type": "payment_request",
    }
    await self.db.run(
      insert_line_items_batch_request(
        InsertLineItemsBatchParams(
          imports_recid=import_recid,
          vendors_recid=vendor_recid,
          rows=[line_item],
        ),
      ),
    )
    await self.db.run(
      update_import_status_request(
        UpdateImportStatusParams(
          recid=import_recid,
          status=IMPORT_PENDING_APPROVAL,
          row_count=1,
          error=None,
        ),
      ),
    )
    return {
      "import_recid": import_recid,
      "status": "pending_approval",
      "message": f"Payment request for {vendor_name} ({payload.get('amount')} {payload.get('currency')}) submitted for approval.",
    }

  async def list_purge_logs(self) -> list[dict[str, Any]]:
    assert self.db
    res = await self.db.run(list_purge_logs_request(ListPurgeLogsParams()))
    return [dict(row) for row in res.rows]

  async def list_status_codes(self, domain: str | None = None) -> list[dict[str, Any]]:
    assert self.db
    res = await self.db.run(
      list_status_codes_request(ListStatusCodesParams(element_domain=domain))
    )
    return [dict(row) for row in res.rows]

  async def get_status_code(self, domain: str, code: int) -> dict[str, Any] | None:
    assert self.db
    res = await self.db.run(
      get_status_code_request(
        GetStatusCodeParams(element_domain=domain, element_code=code)
      )
    )
    if not res.rows:
      return None
    return dict(res.rows[0])

  async def get_pipeline_config(self, pipeline: str, key: str) -> str:
    cache_key = (pipeline, key)
    if cache_key in self._pipeline_config_cache:
      return self._pipeline_config_cache[cache_key]

    row = await self.get_pipeline_config_record(pipeline, key)
    if not row:
      raise ValueError(f"Missing finance pipeline config: {pipeline}.{key}")

    value = str(row.get("element_value") or "")
    self._pipeline_config_cache[cache_key] = value
    return value

  async def get_pipeline_config_record(
    self,
    pipeline: str,
    key: str,
  ) -> dict[str, Any] | None:
    assert self.db
    res = await self.db.run(
      get_pipeline_config_request(
        GetPipelineConfigParams(element_pipeline=pipeline, element_key=key)
      )
    )
    if not res.rows:
      return None
    return dict(res.rows[0])

  async def list_pipeline_configs(
    self,
    pipeline: str | None = None,
  ) -> list[dict[str, Any]]:
    assert self.db
    res = await self.db.run(
      list_pipeline_configs_request(ListPipelineConfigsParams(element_pipeline=pipeline))
    )
    return [dict(row) for row in res.rows]

  async def upsert_pipeline_config(self, data: dict[str, Any]) -> dict[str, Any]:
    assert self.db
    params = UpsertPipelineConfigParams(**data)
    res = await self.db.run(upsert_pipeline_config_request(params))
    row = dict(res.rows[0]) if res.rows else params.model_dump()
    self._pipeline_config_cache[(row["element_pipeline"], row["element_key"])] = str(row["element_value"])
    return row

  async def delete_pipeline_config(self, recid: int) -> dict[str, Any]:
    existing = await self.list_pipeline_configs()
    deleted_key = None
    for row in existing:
      if int(row.get("recid") or 0) == recid:
        deleted_key = (str(row["element_pipeline"]), str(row["element_key"]))
        break

    assert self.db
    await self.db.run(delete_pipeline_config_request(DeletePipelineConfigParams(recid=recid)))
    if deleted_key is not None:
      self._pipeline_config_cache.pop(deleted_key, None)
    return {"recid": recid, "deleted": True}

  async def list_products(self, category: str | None = None, status: int | None = None) -> list[dict[str, Any]]:
    assert self.db
    res = await self.db.run(list_products_request(ListProductsParams(category=category, status=status)))
    return [self._map_product(dict(row)) for row in res.rows]

  async def list_products_with_enablement(self, users_guid: str) -> list[dict[str, Any]]:
    products = await self.list_products(status=1)
    user_enablements = await self.get_user_enablements(users_guid)
    user_roles = await self.get_user_roles_mask(users_guid)
    out: list[dict[str, Any]] = []
    for product in products:
      already_enabled = False
      enablement_key = product.get("enablement_key")
      if enablement_key == "ROLE_STORAGE":
        already_enabled = bool(user_enablements & 1)
      elif enablement_key == "ROLE_DISCORD_BOT":
        already_enabled = bool(user_roles & 0x10)
      out.append({**product, "already_enabled": already_enabled})
    return out

  async def get_product(self, recid: int | None = None, sku: str | None = None) -> dict[str, Any] | None:
    assert self.db
    res = await self.db.run(get_product_request(GetProductParams(recid=recid, sku=sku)))
    if not res.rows:
      return None
    return self._map_product(dict(res.rows[0]))

  async def upsert_product(self, data: dict[str, Any]) -> dict[str, Any]:
    assert self.db
    params = UpsertProductParams(**data)
    res = await self.db.run(upsert_product_request(params))
    row = dict(res.rows[0]) if res.rows else params.model_dump()
    return self._map_product(row)

  async def delete_product(self, recid: int) -> dict[str, Any]:
    assert self.db
    await self.db.run(delete_product_request(DeleteProductParams(recid=recid)))
    return {"recid": recid, "deleted": True}

  async def list_product_journal_configs(
    self,
    category: str | None = None,
    periods_guid: str | None = None,
    status: int | None = None,
  ) -> list[dict[str, Any]]:
    assert self.db
    res = await self.db.run(
      list_product_journal_config_request(
        ListProductJournalConfigParams(category=category, periods_guid=periods_guid, status=status)
      )
    )
    return [self._map_product_journal_config(dict(row)) for row in res.rows]

  async def get_product_journal_config(self, recid: int) -> dict[str, Any] | None:
    assert self.db
    res = await self.db.run(
      get_product_journal_config_request(GetProductJournalConfigParams(recid=recid))
    )
    if not res.rows:
      return None
    return self._map_product_journal_config(dict(res.rows[0]))

  async def get_active_product_journal_config(self, category: str, periods_guid: str) -> dict[str, Any] | None:
    assert self.db
    res = await self.db.run(
      get_active_product_journal_config_request(
        GetActiveConfigParams(category=category, periods_guid=periods_guid)
      )
    )
    if not res.rows:
      return None
    return self._map_product_journal_config(dict(res.rows[0]))

  async def upsert_product_journal_config(self, data: dict[str, Any]) -> dict[str, Any]:
    assert self.db
    params = UpsertProductJournalConfigParams(**data)
    res = await self.db.run(upsert_product_journal_config_request(params))
    if not res.rows:
      raise ValueError("Failed to upsert product journal configuration")
    return self._map_product_journal_config(dict(res.rows[0]))

  async def approve_product_journal_config(self, recid: int, approved_by: str) -> dict[str, Any]:
    assert self.db
    res = await self.db.run(
      approve_product_journal_config_request(
        ApproveProductJournalConfigParams(recid=recid, approved_by=approved_by)
      )
    )
    if not res.rows:
      raise ValueError("Only draft product journal configs can be approved")
    return self._map_product_journal_config(dict(res.rows[0]))

  async def activate_product_journal_config(self, recid: int, activated_by: str) -> dict[str, Any]:
    assert self.db
    config = await self.get_product_journal_config(recid)
    if not config:
      raise ValueError("Product journal config not found")

    active_configs = await self.list_product_journal_configs(
      category=config["category"],
      periods_guid=config["periods_guid"],
      status=2,
    )
    for row in active_configs:
      if int(row["recid"]) != recid:
        raise ValueError("An active configuration already exists for this category and period")

    res = await self.db.run(
      activate_product_journal_config_request(
        ActivateProductJournalConfigParams(recid=recid, activated_by=activated_by)
      )
    )
    if not res.rows:
      raise ValueError("Only approved product journal configs can be activated")
    return self._map_product_journal_config(dict(res.rows[0]))

  async def close_product_journal_config(self, recid: int) -> dict[str, Any]:
    assert self.db
    res = await self.db.run(
      close_product_journal_config_request(CloseProductJournalConfigParams(recid=recid))
    )
    if not res.rows:
      raise ValueError("Only active product journal configs can be closed")
    return self._map_product_journal_config(dict(res.rows[0]))

  async def get_user_enablements(self, users_guid: str) -> int:
    assert self.db
    res = await self.db.run(
      get_user_enablements_request(GetUserEnablementsParams(users_guid=users_guid))
    )
    if not res.rows:
      return 0
    row = dict(res.rows[0])
    return int(str(row.get("element_enablements") or "0") or 0)

  async def set_user_enablements(self, users_guid: str, enablements: int) -> dict[str, Any]:
    assert self.db
    res = await self.db.run(
      upsert_user_enablements_request(
        UpsertUserEnablementsParams(users_guid=users_guid, element_enablements=str(enablements))
      )
    )
    return dict(res.rows[0]) if res.rows else {"users_guid": users_guid, "element_enablements": str(enablements)}

  async def get_user_roles_mask(self, users_guid: str) -> int:
    assert self.db
    res = await self.db.run(get_roles_request(GuidParams(guid=users_guid)))
    if not res.rows:
      return 0
    row = dict(res.rows[0])
    return int(row.get("roles") or 0)

  async def set_user_roles_mask(self, users_guid: str, roles: int) -> int:
    assert self.db
    await self.db.run(set_roles_request(SetRolesParams(guid=users_guid, roles=roles)))
    auth = getattr(self.app.state, "auth", None)
    if auth is not None:
      await auth.refresh_user_roles(users_guid)
    return roles

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

  async def _next_formatted_number(self, prefix: str, scope: str) -> tuple[str, int]:
    """Get the next sequence value by scope and return the formatted identifier."""
    assert self.db
    next_res = await self.db.run(
      next_number_by_scope_request(NextNumberByScopeParams(prefix=prefix, scope=scope))
    )

    if next_res.rows:
      result = dict(next_res.rows[0])
    else:
      current = await self._get_number_by_scope(prefix, scope)
      if not current:
        raise ValueError(f"Number sequence not found: prefix={prefix} scope={scope}")
      await self._rollover_number_sequence(prefix, scope, current)
      retry_res = await self.db.run(
        next_number_by_scope_request(NextNumberByScopeParams(prefix=prefix, scope=scope))
      )
      if not retry_res.rows:
        raise ValueError(f"Number sequence rollover failed: prefix={prefix} scope={scope}")
      result = dict(retry_res.rows[0])

    next_val = int(result.get("element_block_start", result.get("element_last_number", 0)))
    pattern = result.get("element_pattern") or result.get("element_display_format")
    series = int(result.get("element_series_number", 1) or 1)

    if pattern and "{number" in pattern:
      formatted = pattern.format(series=series, number=next_val)
    elif pattern:
      formatted = f"{pattern}{next_val}"
    else:
      prefix_str = result.get("element_prefix") or prefix
      formatted = f"{prefix_str}-{series:03d}-{next_val:08d}"

    return formatted, int(result["recid"])

  async def _validate_journal_period_open(self, periods_guid: str | None) -> None:
    if not periods_guid:
      return
    period = await self.get_period(periods_guid)
    if not period:
      raise ValueError("Period not found")
    if int(period["status"] or ELEMENT_INACTIVE) != PERIOD_OPEN:
      raise ValueError("Cannot post to closed period")

  async def _validate_balanced_journal_lines(self, lines: list[dict[str, Any]]) -> None:
    if not lines:
      raise ValueError("Cannot post a journal with no lines")

    total_debits = Decimal("0")
    total_credits = Decimal("0")
    for line in lines:
      total_debits += self._quantize_5dp(self._to_decimal(line.get("debit", "0")))
      total_credits += self._quantize_5dp(self._to_decimal(line.get("credit", "0")))

    if abs(total_debits - total_credits) > Decimal("0.00001"):
      raise ValueError(f"Journal is unbalanced: debits={total_debits} credits={total_credits}")

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
      scope = self._journal_sequence_scope(source_type)
      journal_number, journal_numbers_recid = await self._next_formatted_number("JRN", scope)
      posting_key = journal_number

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
          status=JOURNAL_DRAFT,
        )
      )
    )
    created = self._map_journal(dict(create_res.rows[0]))
    journal_recid = int(created["recid"])
    lines_payload = [line.model_copy(update={"journals_recid": journal_recid}) for line in quantified_lines]
    await self.db.run(
      create_lines_batch_request(CreateLinesBatchParams(journals_recid=journal_recid, lines=lines_payload))
    )
    return created

  async def create_and_post_system_journal(
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
    posted_by: str = "SYSTEM",
  ) -> dict[str, Any]:
    created = await self.create_journal(
      name=name,
      description=description,
      posting_key=posting_key,
      source_type=source_type,
      source_id=source_id,
      periods_guid=periods_guid,
      ledgers_recid=ledgers_recid,
      lines=lines,
    )
    return await self.post_journal(int(created["recid"]), posted_by=posted_by)

  async def submit_journal_for_approval(
    self,
    recid: int,
    submitted_by: str | None = None,
  ) -> dict[str, Any]:
    del submitted_by
    assert self.db
    journal = await self.get_journal(recid)
    if not journal:
      raise ValueError("Journal not found")
    if journal["status"] != JOURNAL_DRAFT:
      raise ValueError("Only draft journals can be submitted for approval")

    lines = await self.get_journal_lines(recid)
    await self._validate_balanced_journal_lines(lines)

    res = await self.db.run(
      update_journal_status_request(
        UpdateJournalStatusParams(
          recid=recid,
          status=JOURNAL_PENDING_APPROVAL,
        )
      )
    )
    return self._map_journal(dict(res.rows[0]))

  async def post_journal(self, recid: int, posted_by: str | None = None) -> dict[str, Any]:
    assert self.db
    journal = await self.get_journal(recid)
    if not journal:
      raise ValueError("Journal not found")
    if journal["status"] not in {JOURNAL_DRAFT, JOURNAL_PENDING_APPROVAL}:
      raise ValueError("Only draft or pending approval journals can be posted")

    await self._validate_journal_period_open(journal.get("periods_guid"))
    lines = await self.get_journal_lines(recid)
    await self._validate_balanced_journal_lines(lines)

    res = await self.db.run(
      update_journal_status_request(
        UpdateJournalStatusParams(
          recid=recid,
          status=JOURNAL_POSTED,
          posted_by=posted_by,
          posted_on=datetime.now(timezone.utc).isoformat(),
        )
      )
    )
    return self._map_journal(dict(res.rows[0]))

  async def approve_journal(
    self,
    recid: int,
    approved_by: str | None = None,
  ) -> dict[str, Any]:
    journal = await self.get_journal(recid)
    if not journal:
      raise ValueError("Journal not found")
    if journal["status"] != JOURNAL_PENDING_APPROVAL:
      raise ValueError("Only journals pending approval can be approved")
    return await self.post_journal(recid, posted_by=approved_by)

  async def reject_journal(
    self,
    recid: int,
    rejected_by: str | None = None,
    reason: str | None = None,
  ) -> dict[str, Any]:
    del rejected_by
    if reason:
      logging.info("[FinanceModule] journal %s rejected: %s", recid, reason)
    assert self.db
    journal = await self.get_journal(recid)
    if not journal:
      raise ValueError("Journal not found")
    if journal["status"] != JOURNAL_PENDING_APPROVAL:
      raise ValueError("Only journals pending approval can be rejected")

    res = await self.db.run(
      update_journal_status_request(
        UpdateJournalStatusParams(
          recid=recid,
          status=JOURNAL_DRAFT,
        )
      )
    )
    return self._map_journal(dict(res.rows[0]))

  async def reverse_journal(self, recid: int, posted_by: str | None = None) -> dict[str, Any]:
    assert self.db
    original = await self.get_journal(recid)
    if not original:
      raise ValueError("Journal not found")
    if original["status"] != JOURNAL_POSTED:
      raise ValueError("Only posted journals can be reversed")

    periods_guid = original.get("periods_guid")
    await self._validate_journal_period_open(periods_guid)

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

    reversal = await self.create_and_post_system_journal(
      name=f"REV-{original['name']}",
      description=f"Reversal of journal {recid}",
      posting_key=f"REV-{original['posting_key']}" if original.get("posting_key") else None,
      source_type="reversal",
      source_id=str(recid),
      periods_guid=periods_guid,
      ledgers_recid=original.get("ledgers_recid"),
      lines=reversal_lines,
      posted_by=posted_by or "SYSTEM",
    )

    reversal_recid = int(reversal["recid"])
    await self.db.run(
      update_journal_status_request(
        UpdateJournalStatusParams(
          recid=recid,
          status=JOURNAL_REVERSED,
          reversed_by=reversal_recid,
        )
      )
    )
    res = await self.db.run(
      update_journal_status_request(
        UpdateJournalStatusParams(
          recid=reversal_recid,
          status=JOURNAL_POSTED,
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

  async def _process_payment_stub(self, product: dict[str, Any], users_guid: str) -> dict[str, Any]:
    del users_guid
    return {
      "success": True,
      "transaction_token": f"STUB-{uuid.uuid4()}",
      "amount": product["price"],
      "currency": product["currency"],
    }

  async def _get_current_open_period_guid(self) -> str:
    today = date.today().isoformat()
    periods = await self.list_periods()
    for period in periods:
      if int(period.get("status") or ELEMENT_INACTIVE) != PERIOD_OPEN:
        continue
      start_date = str(period.get("start_date") or "")
      end_date = str(period.get("end_date") or "")
      if start_date and end_date and start_date <= today <= end_date:
        return str(period["guid"])
    raise ValueError("No open accounting period covers today's date")

  async def _append_balanced_journal_lines(
    self,
    *,
    journals_recid: int,
    debit_account_guid: str,
    credit_account_guid: str,
    amount: str,
    description: str,
  ) -> list[dict[str, Any]]:
    assert self.db
    existing_lines = await self.get_journal_lines(journals_recid)
    next_line = max((int(line.get("line_number") or 0) for line in existing_lines), default=0) + 1
    lines = [
      CreateLineParams(
        journals_recid=journals_recid,
        line_number=next_line,
        accounts_guid=debit_account_guid,
        debit=str(self._quantize_5dp(self._to_decimal(amount))),
        credit="0.00000",
        description=description,
      ),
      CreateLineParams(
        journals_recid=journals_recid,
        line_number=next_line + 1,
        accounts_guid=credit_account_guid,
        debit="0.00000",
        credit=str(self._quantize_5dp(self._to_decimal(amount))),
        description=description,
      ),
    ]
    await self.db.run(
      create_lines_batch_request(CreateLinesBatchParams(journals_recid=journals_recid, lines=lines))
    )
    return [line.model_dump() for line in lines]

  async def purchase_product(
    self,
    *,
    users_guid: str,
    sku: str,
    actor_guid: str | None = None,
    periods_guid: str | None = None,
  ) -> dict[str, Any]:
    product = await self.get_product(sku=sku)
    if not product or int(product.get("status") or 0) != ELEMENT_ACTIVE:
      raise ValueError("Product is not available for purchase")

    payment = await self._process_payment_stub(product, users_guid)
    if not payment.get("success"):
      raise ValueError("Payment processing failed")

    resolved_period_guid = periods_guid or await self._get_current_open_period_guid()
    transaction_token = str(payment["transaction_token"])
    amount = str(product["price"])
    category = str(product.get("category") or "")

    if category == "credit_purchase":
      config = await self.get_active_product_journal_config("credit_purchase", resolved_period_guid)
      if not config:
        raise ValueError("No active journal configuration for credit purchases in the current period")

      lot = await self.create_lot(
        users_guid=users_guid,
        source_type="purchase",
        credits=int(product.get("credits") or 0),
        total_paid=amount,
        source_id=transaction_token,
        actor_guid=actor_guid,
      )

      payment_clearing_account = await self.get_pipeline_config(
        "credit_purchase",
        "payment_clearing_account_number",
      )
      deferred_revenue_account = await self.get_pipeline_config(
        "credit_purchase",
        "deferred_revenue_account_number",
      )
      payment_clearing_guid = await self._get_account_guid_by_number(payment_clearing_account)
      deferred_revenue_guid = await self._get_account_guid_by_number(deferred_revenue_account)
      description = (
        f"Credit purchase: {sku} - {int(product.get('credits') or 0)} credits - {transaction_token}"
      )
      await self._append_balanced_journal_lines(
        journals_recid=int(config["journals_recid"]),
        debit_account_guid=payment_clearing_guid,
        credit_account_guid=deferred_revenue_guid,
        amount=amount,
        description=description,
      )
      return {
        "product": sku,
        "credits_granted": int(product.get("credits") or 0),
        "lot_number": lot["lot_number"],
        "transaction_token": transaction_token,
        "journal_lines_added": True,
      }

    if category == "enablement":
      enablement_key = str(product.get("enablement_key") or "")
      if enablement_key == "ROLE_STORAGE":
        current_enablements = await self.get_user_enablements(users_guid)
        if current_enablements & 1:
          raise ValueError("Feature already enabled")
        await self.set_user_enablements(users_guid, current_enablements | 1)
      elif enablement_key == "ROLE_DISCORD_BOT":
        current_roles = await self.get_user_roles_mask(users_guid)
        if current_roles & 0x10:
          raise ValueError("Feature already enabled")
        await self.set_user_roles_mask(users_guid, current_roles | 0x10)
      else:
        raise ValueError("Unsupported enablement product")

      if self._to_decimal(amount) > Decimal("0"):
        config = await self.get_active_product_journal_config("enablement", resolved_period_guid)
        if not config:
          raise ValueError("No active journal configuration for enablement purchases in the current period")
        payment_clearing_account = await self.get_pipeline_config(
          "credit_purchase",
          "payment_clearing_account_number",
        )
        saas_revenue_guid = await self._get_account_guid_by_number("4100")
        payment_clearing_guid = await self._get_account_guid_by_number(payment_clearing_account)
        await self._append_balanced_journal_lines(
          journals_recid=int(config["journals_recid"]),
          debit_account_guid=payment_clearing_guid,
          credit_account_guid=saas_revenue_guid,
          amount=amount,
          description=f"Enablement purchase: {sku} - {transaction_token}",
        )

      return {
        "product": sku,
        "enablement_granted": enablement_key,
        "transaction_token": transaction_token,
      }

    raise ValueError(f"Unsupported product category: {category}")

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

    lot_number, numbers_recid = await self._next_formatted_number("LOT", "credit_lot")
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
          status=CREDIT_LOT_ACTIVE,
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
      deferred_revenue_account = await self.get_pipeline_config(
        "credit_consumption",
        "deferred_revenue_account_number",
      )
      recognized_revenue_account = await self.get_pipeline_config(
        "credit_consumption",
        "revenue_account_number",
      )
      deferred_revenue_guid = await self._get_account_guid_by_number(deferred_revenue_account)
      recognized_revenue_guid = await self._get_account_guid_by_number(recognized_revenue_account)
      journal = await self.create_and_post_system_journal(
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
        posted_by=actor_guid or "SYSTEM",
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
