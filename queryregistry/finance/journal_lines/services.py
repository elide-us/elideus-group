"""Finance journal lines query registry service dispatchers."""

from __future__ import annotations

from collections.abc import Awaitable, Callable, Mapping
from typing import Any

from queryregistry.models import DBRequest, DBResponse

from . import mssql
from .models import (
  CreateLineParams,
  CreateLinesBatchParams,
  DeleteLinesByJournalParams,
  ListLinesByJournalParams,
)

__all__ = ["create_line_v1", "create_lines_batch_v1", "delete_by_journal_v1", "list_by_journal_v1"]

_Dispatcher = Callable[[Mapping[str, Any]], Awaitable[DBResponse]]

_LIST_BY_JOURNAL_DISPATCHERS: dict[str, _Dispatcher] = {"mssql": mssql.list_by_journal_v1}
_CREATE_LINE_DISPATCHERS: dict[str, _Dispatcher] = {"mssql": mssql.create_line_v1}
_CREATE_LINES_BATCH_DISPATCHERS: dict[str, _Dispatcher] = {"mssql": mssql.create_lines_batch_v1}
_DELETE_BY_JOURNAL_DISPATCHERS: dict[str, _Dispatcher] = {"mssql": mssql.delete_by_journal_v1}


def _select_dispatcher(provider: str, dispatchers: dict[str, _Dispatcher]) -> _Dispatcher:
  dispatcher = dispatchers.get(provider)
  if dispatcher is None:
    raise KeyError(f"Unsupported provider '{provider}' for finance journal lines registry")
  return dispatcher


async def list_by_journal_v1(request: DBRequest, *, provider: str) -> DBResponse:
  params = ListLinesByJournalParams.model_validate(request.payload)
  result = await _select_dispatcher(provider, _LIST_BY_JOURNAL_DISPATCHERS)(params.model_dump())
  return DBResponse(op=request.op, payload=result.payload, rowcount=result.rowcount)


async def create_line_v1(request: DBRequest, *, provider: str) -> DBResponse:
  params = CreateLineParams.model_validate(request.payload)
  result = await _select_dispatcher(provider, _CREATE_LINE_DISPATCHERS)(params.model_dump())
  return DBResponse(op=request.op, payload=result.payload, rowcount=result.rowcount)


async def create_lines_batch_v1(request: DBRequest, *, provider: str) -> DBResponse:
  params = CreateLinesBatchParams.model_validate(request.payload)
  result = await _select_dispatcher(provider, _CREATE_LINES_BATCH_DISPATCHERS)(params.model_dump())
  return DBResponse(op=request.op, payload=result.payload, rowcount=result.rowcount)


async def delete_by_journal_v1(request: DBRequest, *, provider: str) -> DBResponse:
  params = DeleteLinesByJournalParams.model_validate(request.payload)
  result = await _select_dispatcher(provider, _DELETE_BY_JOURNAL_DISPATCHERS)(params.model_dump())
  return DBResponse(op=request.op, payload=result.payload, rowcount=result.rowcount)
