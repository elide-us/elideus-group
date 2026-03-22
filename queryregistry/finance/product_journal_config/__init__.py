"""Finance product journal config query registry request builders."""

from __future__ import annotations

from queryregistry.models import DBRequest

from .models import (
  ActivateProductJournalConfigParams,
  ApproveProductJournalConfigParams,
  CloseProductJournalConfigParams,
  GetActiveConfigParams,
  GetProductJournalConfigParams,
  ListProductJournalConfigParams,
  UpsertProductJournalConfigParams,
)

__all__ = [
  "activate_product_journal_config_request",
  "approve_product_journal_config_request",
  "close_product_journal_config_request",
  "get_active_product_journal_config_request",
  "get_product_journal_config_request",
  "list_product_journal_config_request",
  "upsert_product_journal_config_request",
]


def list_product_journal_config_request(params: ListProductJournalConfigParams) -> DBRequest:
  return DBRequest(op="db:finance:product_journal_config:list:1", payload=params.model_dump())


def get_product_journal_config_request(params: GetProductJournalConfigParams) -> DBRequest:
  return DBRequest(op="db:finance:product_journal_config:get:1", payload=params.model_dump())


def get_active_product_journal_config_request(params: GetActiveConfigParams) -> DBRequest:
  return DBRequest(op="db:finance:product_journal_config:get_active:1", payload=params.model_dump())


def upsert_product_journal_config_request(params: UpsertProductJournalConfigParams) -> DBRequest:
  return DBRequest(op="db:finance:product_journal_config:upsert:1", payload=params.model_dump())


def approve_product_journal_config_request(params: ApproveProductJournalConfigParams) -> DBRequest:
  return DBRequest(op="db:finance:product_journal_config:approve:1", payload=params.model_dump())


def activate_product_journal_config_request(params: ActivateProductJournalConfigParams) -> DBRequest:
  return DBRequest(op="db:finance:product_journal_config:activate:1", payload=params.model_dump())


def close_product_journal_config_request(params: CloseProductJournalConfigParams) -> DBRequest:
  return DBRequest(op="db:finance:product_journal_config:close:1", payload=params.model_dump())
