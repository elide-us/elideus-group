"""Finance credit lots query registry models."""

from __future__ import annotations

from typing import TypedDict

from pydantic import BaseModel, ConfigDict

__all__ = [
  "CreateEventParams",
  "CreateLotParams",
  "ConsumeCreditsParams",
  "CreditLotEventRecord",
  "CreditLotRecord",
  "ExpireLotParams",
  "GetLotParams",
  "ListEventsByLotParams",
  "ListLotsByUserParams",
  "SumRemainingByUserParams",
]


class ListLotsByUserParams(BaseModel):
  model_config = ConfigDict(extra="forbid")

  users_guid: str


class GetLotParams(BaseModel):
  model_config = ConfigDict(extra="forbid")

  recid: int


class CreateLotParams(BaseModel):
  model_config = ConfigDict(extra="forbid")

  users_guid: str
  lot_number: str
  source_type: str
  credits_original: int
  credits_remaining: int
  unit_price: str = "0"
  total_paid: str = "0"
  currency: str = "USD"
  expires_at: str | None = None
  source_id: str | None = None
  numbers_recid: int | None = None
  status: int = 1


class ConsumeCreditsParams(BaseModel):
  model_config = ConfigDict(extra="forbid")

  recid: int
  credits_to_consume: int


class ExpireLotParams(BaseModel):
  model_config = ConfigDict(extra="forbid")

  recid: int


class ListEventsByLotParams(BaseModel):
  model_config = ConfigDict(extra="forbid")

  lots_recid: int


class CreateEventParams(BaseModel):
  model_config = ConfigDict(extra="forbid")

  lots_recid: int
  event_type: str
  credits: int
  unit_price: str = "0"
  description: str | None = None
  actor_guid: str | None = None
  journals_recid: int | None = None


class SumRemainingByUserParams(BaseModel):
  model_config = ConfigDict(extra="forbid")

  users_guid: str


class CreditLotRecord(TypedDict):
  recid: int
  users_guid: str
  element_lot_number: str
  element_source_type: str
  element_credits_original: int
  element_credits_remaining: int
  element_unit_price: str
  element_total_paid: str
  element_currency: str
  element_expires_at: str | None
  element_expired: bool
  element_source_id: str | None
  numbers_recid: int | None
  element_status: int
  element_created_on: str
  element_modified_on: str


class CreditLotEventRecord(TypedDict):
  recid: int
  lots_recid: int
  element_event_type: str
  element_credits: int
  element_unit_price: str
  element_description: str | None
  element_actor_guid: str | None
  journals_recid: int | None
  element_created_on: str
