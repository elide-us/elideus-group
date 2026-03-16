"""Finance credit lots query registry request builders."""

from __future__ import annotations

from queryregistry.models import DBRequest

from .models import (
  CreateEventParams,
  CreateLotParams,
  ConsumeCreditsParams,
  ExpireLotParams,
  GetLotParams,
  ListEventsByLotParams,
  ListLotsByUserParams,
  SumRemainingByUserParams,
)

__all__ = [
  "consume_credits_request",
  "create_event_request",
  "create_lot_request",
  "expire_lot_request",
  "get_lot_request",
  "list_events_by_lot_request",
  "list_lots_by_user_request",
  "sum_remaining_by_user_request",
]


def list_lots_by_user_request(params: ListLotsByUserParams) -> DBRequest:
  return DBRequest(op="db:finance:credit_lots:list_lots_by_user:1", payload=params.model_dump())


def get_lot_request(params: GetLotParams) -> DBRequest:
  return DBRequest(op="db:finance:credit_lots:get_lot:1", payload=params.model_dump())


def create_lot_request(params: CreateLotParams) -> DBRequest:
  return DBRequest(op="db:finance:credit_lots:create_lot:1", payload=params.model_dump())


def consume_credits_request(params: ConsumeCreditsParams) -> DBRequest:
  return DBRequest(op="db:finance:credit_lots:consume_credits:1", payload=params.model_dump())


def expire_lot_request(params: ExpireLotParams) -> DBRequest:
  return DBRequest(op="db:finance:credit_lots:expire_lot:1", payload=params.model_dump())


def list_events_by_lot_request(params: ListEventsByLotParams) -> DBRequest:
  return DBRequest(op="db:finance:credit_lots:list_events_by_lot:1", payload=params.model_dump())


def create_event_request(params: CreateEventParams) -> DBRequest:
  return DBRequest(op="db:finance:credit_lots:create_event:1", payload=params.model_dump())


def sum_remaining_by_user_request(params: SumRemainingByUserParams) -> DBRequest:
  return DBRequest(op="db:finance:credit_lots:sum_remaining_by_user:1", payload=params.model_dump())
