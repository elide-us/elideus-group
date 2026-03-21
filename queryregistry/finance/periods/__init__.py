"""Finance periods query registry request builders."""

from __future__ import annotations

from queryregistry.models import DBRequest

from .models import (
  ClosePeriodParams,
  DeletePeriodParams,
  GenerateCalendarParams,
  GetPeriodParams,
  ListPeriodCloseBlockersParams,
  ListPeriodsByYearParams,
  ListPeriodsParams,
  LockPeriodParams,
  ReopenPeriodParams,
  UnlockPeriodParams,
  UpsertPeriodParams,
)

__all__ = [
  "close_period_request",
  "delete_period_request",
  "generate_calendar_request",
  "get_period_request",
  "list_period_close_blockers_request",
  "list_periods_by_year_request",
  "list_periods_request",
  "lock_period_request",
  "reopen_period_request",
  "unlock_period_request",
  "upsert_period_request",
]


def list_periods_request(params: ListPeriodsParams) -> DBRequest:
  return DBRequest(op="db:finance:periods:list:1", payload=params.model_dump())


def list_periods_by_year_request(params: ListPeriodsByYearParams) -> DBRequest:
  return DBRequest(op="db:finance:periods:list_by_year:1", payload=params.model_dump())


def get_period_request(params: GetPeriodParams) -> DBRequest:
  return DBRequest(op="db:finance:periods:get:1", payload=params.model_dump())


def close_period_request(params: ClosePeriodParams) -> DBRequest:
  return DBRequest(op="db:finance:periods:close:1", payload=params.model_dump())


def reopen_period_request(params: ReopenPeriodParams) -> DBRequest:
  return DBRequest(op="db:finance:periods:reopen:1", payload=params.model_dump())


def lock_period_request(params: LockPeriodParams) -> DBRequest:
  return DBRequest(op="db:finance:periods:lock:1", payload=params.model_dump())


def unlock_period_request(params: UnlockPeriodParams) -> DBRequest:
  return DBRequest(op="db:finance:periods:unlock:1", payload=params.model_dump())


def list_period_close_blockers_request(params: ListPeriodCloseBlockersParams) -> DBRequest:
  return DBRequest(op="db:finance:periods:list_close_blockers:1", payload=params.model_dump())


def upsert_period_request(params: UpsertPeriodParams) -> DBRequest:
  return DBRequest(op="db:finance:periods:upsert:1", payload=params.model_dump())


def delete_period_request(params: DeletePeriodParams) -> DBRequest:
  return DBRequest(op="db:finance:periods:delete:1", payload=params.model_dump())


def generate_calendar_request(params: GenerateCalendarParams) -> DBRequest:
  return DBRequest(op="db:finance:periods:generate_calendar:1", payload=params.model_dump())
