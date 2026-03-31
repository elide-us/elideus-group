from __future__ import annotations

from collections.abc import Awaitable, Callable, Mapping
from typing import Any

from queryregistry.models import DBRequest, DBResponse

from . import mssql
from .models import (
  CreateScheduledTaskHistoryParams,
  GetTaskParams,
  GetWorkflowNameByGuidParams,
  ListAllTasksParams,
  ListEnabledDueTasksParams,
  ListTaskHistoryParams,
  UpdateScheduledTaskParams,
)

_Dispatcher = Callable[[Mapping[str, Any]], Awaitable[DBResponse]]

_LIST_ENABLED_DUE_TASKS_DISPATCHERS: dict[str, _Dispatcher] = {"mssql": mssql.list_enabled_due_tasks_v1}
_LIST_ALL_TASKS_DISPATCHERS: dict[str, _Dispatcher] = {"mssql": mssql.list_all_tasks_v1}
_GET_TASK_DISPATCHERS: dict[str, _Dispatcher] = {"mssql": mssql.get_task_v1}
_LIST_TASK_HISTORY_DISPATCHERS: dict[str, _Dispatcher] = {"mssql": mssql.list_task_history_v1}
_UPDATE_SCHEDULED_TASK_DISPATCHERS: dict[str, _Dispatcher] = {"mssql": mssql.update_scheduled_task_v1}
_CREATE_SCHEDULED_TASK_HISTORY_DISPATCHERS: dict[str, _Dispatcher] = {"mssql": mssql.create_scheduled_task_history_v1}
_GET_WORKFLOW_NAME_BY_GUID_DISPATCHERS: dict[str, _Dispatcher] = {"mssql": mssql.get_workflow_name_by_guid_v1}


def _select_dispatcher(provider: str, dispatchers: dict[str, _Dispatcher]) -> _Dispatcher:
  dispatcher = dispatchers.get(provider)
  if dispatcher is None:
    raise KeyError(f"Unsupported provider '{provider}' for system scheduled_tasks registry")
  return dispatcher


async def list_enabled_due_tasks_v1(request: DBRequest, *, provider: str) -> DBResponse:
  params = ListEnabledDueTasksParams.model_validate(request.payload)
  result = await _select_dispatcher(provider, _LIST_ENABLED_DUE_TASKS_DISPATCHERS)(params.model_dump())
  return DBResponse(op=request.op, payload=result.payload, rowcount=result.rowcount)


async def update_scheduled_task_v1(request: DBRequest, *, provider: str) -> DBResponse:
  params = UpdateScheduledTaskParams.model_validate(request.payload)
  result = await _select_dispatcher(provider, _UPDATE_SCHEDULED_TASK_DISPATCHERS)(params.model_dump(exclude_unset=True))
  return DBResponse(op=request.op, payload=result.payload, rowcount=result.rowcount)


async def create_scheduled_task_history_v1(request: DBRequest, *, provider: str) -> DBResponse:
  params = CreateScheduledTaskHistoryParams.model_validate(request.payload)
  result = await _select_dispatcher(provider, _CREATE_SCHEDULED_TASK_HISTORY_DISPATCHERS)(params.model_dump())
  return DBResponse(op=request.op, payload=result.payload, rowcount=result.rowcount)


async def get_workflow_name_by_guid_v1(request: DBRequest, *, provider: str) -> DBResponse:
  params = GetWorkflowNameByGuidParams.model_validate(request.payload)
  result = await _select_dispatcher(provider, _GET_WORKFLOW_NAME_BY_GUID_DISPATCHERS)(params.model_dump())
  return DBResponse(op=request.op, payload=result.payload, rowcount=result.rowcount)


async def list_all_tasks_v1(request: DBRequest, *, provider: str) -> DBResponse:
  params = ListAllTasksParams.model_validate(request.payload)
  result = await _select_dispatcher(provider, _LIST_ALL_TASKS_DISPATCHERS)(params.model_dump())
  return DBResponse(op=request.op, payload=result.payload, rowcount=result.rowcount)


async def get_task_v1(request: DBRequest, *, provider: str) -> DBResponse:
  params = GetTaskParams.model_validate(request.payload)
  result = await _select_dispatcher(provider, _GET_TASK_DISPATCHERS)(params.model_dump())
  return DBResponse(op=request.op, payload=result.payload, rowcount=result.rowcount)


async def list_task_history_v1(request: DBRequest, *, provider: str) -> DBResponse:
  params = ListTaskHistoryParams.model_validate(request.payload)
  result = await _select_dispatcher(provider, _LIST_TASK_HISTORY_DISPATCHERS)(params.model_dump())
  return DBResponse(op=request.op, payload=result.payload, rowcount=result.rowcount)
