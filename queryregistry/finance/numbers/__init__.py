"""Finance numbers query registry request builders."""

from __future__ import annotations

from queryregistry.models import DBRequest

from .models import (
  CloseSequenceParams,
  DeleteNumberParams,
  GetByPrefixAndAccountNumberParams,
  GetNumberParams,
  ListNumbersParams,
  NextNumberParams,
  UpsertNumberParams,
)

__all__ = [
  "close_sequence_request",
  "delete_number_request",
  "get_by_prefix_account_number_request",
  "get_number_request",
  "list_numbers_request",
  "next_number_request",
  "upsert_number_request",
]


def list_numbers_request(params: ListNumbersParams) -> DBRequest:
  return DBRequest(op="db:finance:numbers:list:1", payload=params.model_dump())




def get_by_prefix_account_number_request(params: GetByPrefixAndAccountNumberParams) -> DBRequest:
  return DBRequest(op="db:finance:numbers:get_by_prefix_account:1", payload=params.model_dump())

def get_number_request(params: GetNumberParams) -> DBRequest:
  return DBRequest(op="db:finance:numbers:get:1", payload=params.model_dump())


def upsert_number_request(params: UpsertNumberParams) -> DBRequest:
  return DBRequest(op="db:finance:numbers:upsert:1", payload=params.model_dump())


def delete_number_request(params: DeleteNumberParams) -> DBRequest:
  return DBRequest(op="db:finance:numbers:delete:1", payload=params.model_dump())


def next_number_request(params: NextNumberParams) -> DBRequest:
  return DBRequest(op="db:finance:numbers:next_number:1", payload=params.model_dump())


def close_sequence_request(params: CloseSequenceParams) -> DBRequest:
  return DBRequest(op="db:finance:numbers:close_sequence:1", payload=params.model_dump())
