from __future__ import annotations

from collections.abc import Awaitable, Callable, Mapping
from typing import Any

from queryregistry.models import DBRequest, DBResponse

from . import mssql
from .models import (
  CreateTaskEventParams,
  CreateTaskParams,
  GetTaskParams,
  ListTaskEventsParams,
  ListTasksParams,
  UpdateTaskParams,
)

_Dispatcher = Callable[[Mapping[str, Any]], Awaitable[DBResponse]]

_CREATE_TASK_DISPATCHERS: dict[str, _Dispatcher] = {"mssql": mssql.create_task_v1}
_GET_TASK_DISPATCHERS: dict[str, _Dispatcher] = {"mssql": mssql.get_task_v1}
_LIST_TASKS_DISPATCHERS: dict[str, _Dispatcher] = {"mssql": mssql.list_tasks_v1}
_UPDATE_TASK_DISPATCHERS: dict[str, _Dispatcher] = {"mssql": mssql.update_task_v1}
_CREATE_TASK_EVENT_DISPATCHERS: dict[str, _Dispatcher] = {"mssql": mssql.create_task_event_v1}
_LIST_TASK_EVENTS_DISPATCHERS: dict[str, _Dispatcher] = {"mssql": mssql.list_task_events_v1}


def _select_dispatcher(provider: str, dispatchers: dict[str, _Dispatcher]) -> _Dispatcher:
  dispatcher = dispatchers.get(provider)
  if dispatcher is None:
    raise KeyError(f"Unsupported provider '{provider}' for system async tasks registry")
  return dispatcher


async def create_task_v1(request: DBRequest, *, provider: str) -> DBResponse:
  params = CreateTaskParams.model_validate(request.payload)
  result = await _select_dispatcher(provider, _CREATE_TASK_DISPATCHERS)(params.model_dump())
  return DBResponse(op=request.op, payload=result.payload, rowcount=result.rowcount)


async def get_task_v1(request: DBRequest, *, provider: str) -> DBResponse:
  params = GetTaskParams.model_validate(request.payload)
  result = await _select_dispatcher(provider, _GET_TASK_DISPATCHERS)(params.model_dump())
  return DBResponse(op=request.op, payload=result.payload, rowcount=result.rowcount)


async def list_tasks_v1(request: DBRequest, *, provider: str) -> DBResponse:
  params = ListTasksParams.model_validate(request.payload)
  result = await _select_dispatcher(provider, _LIST_TASKS_DISPATCHERS)(params.model_dump())
  return DBResponse(op=request.op, payload=result.payload, rowcount=result.rowcount)


async def update_task_v1(request: DBRequest, *, provider: str) -> DBResponse:
  params = UpdateTaskParams.model_validate(request.payload)
  result = await _select_dispatcher(provider, _UPDATE_TASK_DISPATCHERS)(params.model_dump(exclude_unset=True))
  return DBResponse(op=request.op, payload=result.payload, rowcount=result.rowcount)


async def create_task_event_v1(request: DBRequest, *, provider: str) -> DBResponse:
  params = CreateTaskEventParams.model_validate(request.payload)
  result = await _select_dispatcher(provider, _CREATE_TASK_EVENT_DISPATCHERS)(params.model_dump())
  return DBResponse(op=request.op, payload=result.payload, rowcount=result.rowcount)


async def list_task_events_v1(request: DBRequest, *, provider: str) -> DBResponse:
  params = ListTaskEventsParams.model_validate(request.payload)
  result = await _select_dispatcher(provider, _LIST_TASK_EVENTS_DISPATCHERS)(params.model_dump())
  return DBResponse(op=request.op, payload=result.payload, rowcount=result.rowcount)
