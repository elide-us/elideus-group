"""System batch jobs query registry service dispatchers."""

from __future__ import annotations

from collections.abc import Awaitable, Callable, Mapping
from typing import Any

from queryregistry.models import DBRequest, DBResponse

from . import mssql
from .models import (
  CreateHistoryParams,
  DeleteJobParams,
  GetJobParams,
  ListHistoryParams,
  ListJobsParams,
  UpdateHistoryParams,
  UpdateJobStatusParams,
  UpsertJobParams,
)

__all__ = [
  "create_history_v1",
  "delete_job_v1",
  "get_job_v1",
  "list_history_v1",
  "list_jobs_v1",
  "update_history_v1",
  "update_job_status_v1",
  "upsert_job_v1",
]

_Dispatcher = Callable[[Mapping[str, Any]], Awaitable[DBResponse]]

_LIST_JOBS_DISPATCHERS: dict[str, _Dispatcher] = {"mssql": mssql.list_jobs_v1}
_GET_JOB_DISPATCHERS: dict[str, _Dispatcher] = {"mssql": mssql.get_job_v1}
_UPSERT_JOB_DISPATCHERS: dict[str, _Dispatcher] = {"mssql": mssql.upsert_job_v1}
_DELETE_JOB_DISPATCHERS: dict[str, _Dispatcher] = {"mssql": mssql.delete_job_v1}
_LIST_HISTORY_DISPATCHERS: dict[str, _Dispatcher] = {"mssql": mssql.list_history_v1}
_CREATE_HISTORY_DISPATCHERS: dict[str, _Dispatcher] = {"mssql": mssql.create_history_v1}
_UPDATE_HISTORY_DISPATCHERS: dict[str, _Dispatcher] = {"mssql": mssql.update_history_v1}
_UPDATE_JOB_STATUS_DISPATCHERS: dict[str, _Dispatcher] = {"mssql": mssql.update_job_status_v1}


def _select_dispatcher(provider: str, dispatchers: dict[str, _Dispatcher]) -> _Dispatcher:
  dispatcher = dispatchers.get(provider)
  if dispatcher is None:
    raise KeyError(f"Unsupported provider '{provider}' for system batch jobs registry")
  return dispatcher


async def list_jobs_v1(request: DBRequest, *, provider: str) -> DBResponse:
  params = ListJobsParams.model_validate(request.payload)
  result = await _select_dispatcher(provider, _LIST_JOBS_DISPATCHERS)(params.model_dump())
  return DBResponse(op=request.op, payload=result.payload, rowcount=result.rowcount)


async def get_job_v1(request: DBRequest, *, provider: str) -> DBResponse:
  params = GetJobParams.model_validate(request.payload)
  result = await _select_dispatcher(provider, _GET_JOB_DISPATCHERS)(params.model_dump())
  return DBResponse(op=request.op, payload=result.payload, rowcount=result.rowcount)


async def upsert_job_v1(request: DBRequest, *, provider: str) -> DBResponse:
  params = UpsertJobParams.model_validate(request.payload)
  result = await _select_dispatcher(provider, _UPSERT_JOB_DISPATCHERS)(params.model_dump())
  return DBResponse(op=request.op, payload=result.payload, rowcount=result.rowcount)


async def delete_job_v1(request: DBRequest, *, provider: str) -> DBResponse:
  params = DeleteJobParams.model_validate(request.payload)
  result = await _select_dispatcher(provider, _DELETE_JOB_DISPATCHERS)(params.model_dump())
  return DBResponse(op=request.op, payload=result.payload, rowcount=result.rowcount)


async def list_history_v1(request: DBRequest, *, provider: str) -> DBResponse:
  params = ListHistoryParams.model_validate(request.payload)
  result = await _select_dispatcher(provider, _LIST_HISTORY_DISPATCHERS)(params.model_dump())
  return DBResponse(op=request.op, payload=result.payload, rowcount=result.rowcount)


async def create_history_v1(request: DBRequest, *, provider: str) -> DBResponse:
  params = CreateHistoryParams.model_validate(request.payload)
  result = await _select_dispatcher(provider, _CREATE_HISTORY_DISPATCHERS)(params.model_dump())
  return DBResponse(op=request.op, payload=result.payload, rowcount=result.rowcount)


async def update_history_v1(request: DBRequest, *, provider: str) -> DBResponse:
  params = UpdateHistoryParams.model_validate(request.payload)
  result = await _select_dispatcher(provider, _UPDATE_HISTORY_DISPATCHERS)(params.model_dump())
  return DBResponse(op=request.op, payload=result.payload, rowcount=result.rowcount)


async def update_job_status_v1(request: DBRequest, *, provider: str) -> DBResponse:
  params = UpdateJobStatusParams.model_validate(request.payload)
  result = await _select_dispatcher(provider, _UPDATE_JOB_STATUS_DISPATCHERS)(params.model_dump())
  return DBResponse(op=request.op, payload=result.payload, rowcount=result.rowcount)
