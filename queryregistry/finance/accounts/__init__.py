"""Finance accounts query registry request builders."""

from __future__ import annotations

from queryregistry.models import DBRequest

from .models import (
  DeleteAccountParams,
  GetAccountParams,
  ListAccountsParams,
  ListChildrenParams,
  UpsertAccountParams,
)

__all__ = [
  "delete_account_request",
  "get_account_request",
  "list_account_children_request",
  "list_accounts_request",
  "upsert_account_request",
]


def list_accounts_request(params: ListAccountsParams) -> DBRequest:
  return DBRequest(op="db:finance:accounts:list:1", payload=params.model_dump())


def get_account_request(params: GetAccountParams) -> DBRequest:
  return DBRequest(op="db:finance:accounts:get:1", payload=params.model_dump())


def upsert_account_request(params: UpsertAccountParams) -> DBRequest:
  return DBRequest(op="db:finance:accounts:upsert:1", payload=params.model_dump())


def delete_account_request(params: DeleteAccountParams) -> DBRequest:
  return DBRequest(op="db:finance:accounts:delete:1", payload=params.model_dump())


def list_account_children_request(params: ListChildrenParams) -> DBRequest:
  return DBRequest(op="db:finance:accounts:list_children:1", payload=params.model_dump())
