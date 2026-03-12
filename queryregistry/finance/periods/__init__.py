"""Finance periods query registry request builders."""

from __future__ import annotations

from queryregistry.models import DBRequest

from .models import (
  DeletePeriodParams,
  GenerateCalendarParams,
  GetPeriodParams,
  ListPeriodsByYearParams,
  ListPeriodsParams,
  UpsertPeriodParams,
)

__all__ = [
  "delete_period_request",
  "generate_calendar_request",
  "get_period_request",
  "list_periods_by_year_request",
  "list_periods_request",
  "upsert_period_request",
]


def list_periods_request(params: ListPeriodsParams) -> DBRequest:
  return DBRequest(op="db:finance:periods:list:1", payload=params.model_dump())


def list_periods_by_year_request(params: ListPeriodsByYearParams) -> DBRequest:
  return DBRequest(op="db:finance:periods:list_by_year:1", payload=params.model_dump())


def get_period_request(params: GetPeriodParams) -> DBRequest:
  return DBRequest(op="db:finance:periods:get:1", payload=params.model_dump())


def upsert_period_request(params: UpsertPeriodParams) -> DBRequest:
  return DBRequest(op="db:finance:periods:upsert:1", payload=params.model_dump())


def delete_period_request(params: DeletePeriodParams) -> DBRequest:
  return DBRequest(op="db:finance:periods:delete:1", payload=params.model_dump())


def generate_calendar_request(params: GenerateCalendarParams) -> DBRequest:
  return DBRequest(op="db:finance:periods:generate_calendar:1", payload=params.model_dump())
