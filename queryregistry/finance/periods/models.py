"""Finance periods query registry models."""

from __future__ import annotations

from typing import TypedDict

from pydantic import BaseModel, ConfigDict

__all__ = [
  "DeletePeriodParams",
  "GenerateCalendarParams",
  "GetPeriodParams",
  "ListPeriodsByYearParams",
  "ListPeriodsParams",
  "PeriodRecord",
  "UpsertPeriodParams",
]


class ListPeriodsParams(BaseModel):
  model_config = ConfigDict(extra="forbid")


class ListPeriodsByYearParams(BaseModel):
  model_config = ConfigDict(extra="forbid")

  year: int


class GetPeriodParams(BaseModel):
  model_config = ConfigDict(extra="forbid")

  guid: str


class UpsertPeriodParams(BaseModel):
  model_config = ConfigDict(extra="forbid")

  guid: str | None = None
  year: int
  period_number: int
  period_name: str
  start_date: str
  end_date: str
  days_in_period: int
  quarter_number: int
  has_closing_week: bool = False
  is_leap_adjustment: bool = False
  anchor_event: str | None = None
  close_type: int = 0
  status: int = 1
  numbers_recid: int | None = None


class DeletePeriodParams(BaseModel):
  model_config = ConfigDict(extra="forbid")

  guid: str


class GenerateCalendarParams(BaseModel):
  model_config = ConfigDict(extra="forbid")

  fiscal_year: int
  start_date: str


class PeriodRecord(TypedDict):
  element_guid: str
  element_year: int
  element_period_number: int
  element_period_name: str
  element_start_date: str
  element_end_date: str
  element_days_in_period: int
  element_quarter_number: int
  element_has_closing_week: bool
  element_is_leap_adjustment: bool
  element_anchor_event: str | None
  element_close_type: int
  element_status: int
  numbers_recid: int | None
  element_display_format: str | None
  element_created_on: str
  element_modified_on: str
