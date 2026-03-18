"""Finance ledgers query registry request builders."""

from __future__ import annotations

from queryregistry.models import DBRequest

from .models import (
  CreateLedgerParams,
  DeleteLedgerParams,
  GetLedgerByNameParams,
  GetLedgerParams,
  JournalReferenceCountParams,
  ListLedgersParams,
  UpdateLedgerParams,
)

__all__ = [
  "create_ledger_request",
  "delete_ledger_request",
  "get_ledger_by_name_request",
  "get_ledger_request",
  "journal_reference_count_request",
  "list_ledgers_request",
  "update_ledger_request",
]


def list_ledgers_request(params: ListLedgersParams) -> DBRequest:
  return DBRequest(op="db:finance:ledgers:list:1", payload=params.model_dump())


def get_ledger_request(params: GetLedgerParams) -> DBRequest:
  return DBRequest(op="db:finance:ledgers:get:1", payload=params.model_dump())


def get_ledger_by_name_request(params: GetLedgerByNameParams) -> DBRequest:
  return DBRequest(op="db:finance:ledgers:get_by_name:1", payload=params.model_dump())


def create_ledger_request(params: CreateLedgerParams) -> DBRequest:
  return DBRequest(op="db:finance:ledgers:create:1", payload=params.model_dump())


def update_ledger_request(params: UpdateLedgerParams) -> DBRequest:
  return DBRequest(op="db:finance:ledgers:update:1", payload=params.model_dump())


def delete_ledger_request(params: DeleteLedgerParams) -> DBRequest:
  return DBRequest(op="db:finance:ledgers:delete:1", payload=params.model_dump())


def journal_reference_count_request(params: JournalReferenceCountParams) -> DBRequest:
  return DBRequest(op="db:finance:ledgers:journal_reference_count:1", payload=params.model_dump())
