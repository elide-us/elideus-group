"""Finance journal lines query registry request builders."""

from __future__ import annotations

from queryregistry.models import DBRequest

from .models import (
  CreateLineParams,
  CreateLinesBatchParams,
  DeleteLinesByJournalParams,
  ListLinesByJournalParams,
)

__all__ = [
  "create_line_request",
  "create_lines_batch_request",
  "delete_lines_by_journal_request",
  "list_lines_by_journal_request",
]


def list_lines_by_journal_request(params: ListLinesByJournalParams) -> DBRequest:
  return DBRequest(op="db:finance:journal_lines:list_by_journal:1", payload=params.model_dump())


def create_line_request(params: CreateLineParams) -> DBRequest:
  return DBRequest(op="db:finance:journal_lines:create_line:1", payload=params.model_dump())


def create_lines_batch_request(params: CreateLinesBatchParams) -> DBRequest:
  return DBRequest(op="db:finance:journal_lines:create_lines_batch:1", payload=params.model_dump())


def delete_lines_by_journal_request(params: DeleteLinesByJournalParams) -> DBRequest:
  return DBRequest(op="db:finance:journal_lines:delete_by_journal:1", payload=params.model_dump())
