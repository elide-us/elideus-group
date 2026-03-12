from __future__ import annotations

import calendar
import logging
import uuid
from datetime import date, datetime, timedelta
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
  get_number_request,
  list_numbers_request,
  next_number_request,
  upsert_number_request,
)
from queryregistry.finance.numbers.models import (
  DeleteNumberParams,
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
          "numbers_recid": None,
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
        "numbers_recid": None,
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
