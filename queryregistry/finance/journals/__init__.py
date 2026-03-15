"""Finance journals query registry request builders."""

from __future__ import annotations

from queryregistry.models import DBRequest

from .models import (
  CreateJournalParams,
  GetByPostingKeyParams,
  GetJournalParams,
  ListJournalsParams,
  UpdateJournalStatusParams,
)

__all__ = [
  "create_journal_request",
  "get_by_posting_key_request",
  "get_journal_request",
  "list_journals_request",
  "update_journal_status_request",
]


def list_journals_request(params: ListJournalsParams) -> DBRequest:
  return DBRequest(op="db:finance:journals:list:1", payload=params.model_dump())


def get_journal_request(params: GetJournalParams) -> DBRequest:
  return DBRequest(op="db:finance:journals:get:1", payload=params.model_dump())


def create_journal_request(params: CreateJournalParams) -> DBRequest:
  return DBRequest(op="db:finance:journals:create:1", payload=params.model_dump())


def update_journal_status_request(params: UpdateJournalStatusParams) -> DBRequest:
  return DBRequest(op="db:finance:journals:update_status:1", payload=params.model_dump())


def get_by_posting_key_request(params: GetByPostingKeyParams) -> DBRequest:
  return DBRequest(op="db:finance:journals:get_by_posting_key:1", payload=params.model_dump())
