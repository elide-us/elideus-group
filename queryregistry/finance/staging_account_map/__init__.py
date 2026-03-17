"""Finance staging account map query registry request builders."""

from __future__ import annotations

from queryregistry.models import DBRequest

from .models import (
  DeleteAccountMapParams,
  GetAccountMapParams,
  ListAccountMapParams,
  ResolveAccountParams,
  UpsertAccountMapParams,
)

__all__ = [
  "delete_account_map_request",
  "get_account_map_request",
  "list_account_map_request",
  "resolve_account_request",
  "upsert_account_map_request",
]


def list_account_map_request(params: ListAccountMapParams) -> DBRequest:
  return DBRequest(op="db:finance:staging_account_map:list_account_map:1", payload=params.model_dump())


def get_account_map_request(params: GetAccountMapParams) -> DBRequest:
  return DBRequest(op="db:finance:staging_account_map:get_account_map:1", payload=params.model_dump())


def upsert_account_map_request(params: UpsertAccountMapParams) -> DBRequest:
  return DBRequest(op="db:finance:staging_account_map:upsert_account_map:1", payload=params.model_dump())


def delete_account_map_request(params: DeleteAccountMapParams) -> DBRequest:
  return DBRequest(op="db:finance:staging_account_map:delete_account_map:1", payload=params.model_dump())


def resolve_account_request(params: ResolveAccountParams) -> DBRequest:
  return DBRequest(op="db:finance:staging_account_map:resolve_account:1", payload=params.model_dump())
