from __future__ import annotations

from collections.abc import Awaitable, Callable, Mapping
from typing import Any

from queryregistry.models import DBRequest, DBResponse

from . import mssql
from .models import (
  CountActiveRunsByWorkflowNameParams,
  CreateWorkflowRunActionParams,
  CreateWorkflowRunParams,
  GetActiveWorkflowParams,
  GetWorkflowRunParams,
  ListWorkflowActionsParams,
  ListWorkflowRunActionsParams,
  ListWorkflowRunsParams,
  ListWorkflowsParams,
  UpdateWorkflowRunActionParams,
  UpdateWorkflowRunParams,
)

_Dispatcher = Callable[[Mapping[str, Any]], Awaitable[DBResponse]]

_GET_ACTIVE_WORKFLOW_DISPATCHERS: dict[str, _Dispatcher] = {"mssql": mssql.get_active_workflow_v1}
_COUNT_ACTIVE_RUNS_BY_NAME_DISPATCHERS: dict[str, _Dispatcher] = {"mssql": mssql.count_active_runs_by_workflow_name_v1}
_LIST_WORKFLOWS_DISPATCHERS: dict[str, _Dispatcher] = {"mssql": mssql.list_workflows_v1}
_LIST_WORKFLOW_ACTIONS_DISPATCHERS: dict[str, _Dispatcher] = {"mssql": mssql.list_workflow_actions_v1}
_CREATE_WORKFLOW_RUN_DISPATCHERS: dict[str, _Dispatcher] = {"mssql": mssql.create_workflow_run_v1}
_GET_WORKFLOW_RUN_DISPATCHERS: dict[str, _Dispatcher] = {"mssql": mssql.get_workflow_run_v1}
_LIST_WORKFLOW_RUNS_DISPATCHERS: dict[str, _Dispatcher] = {"mssql": mssql.list_workflow_runs_v1}
_UPDATE_WORKFLOW_RUN_DISPATCHERS: dict[str, _Dispatcher] = {"mssql": mssql.update_workflow_run_v1}
_CREATE_WORKFLOW_RUN_ACTION_DISPATCHERS: dict[str, _Dispatcher] = {"mssql": mssql.create_workflow_run_action_v1}
_UPDATE_WORKFLOW_RUN_ACTION_DISPATCHERS: dict[str, _Dispatcher] = {"mssql": mssql.update_workflow_run_action_v1}
_LIST_WORKFLOW_RUN_ACTIONS_DISPATCHERS: dict[str, _Dispatcher] = {"mssql": mssql.list_workflow_run_actions_v1}


def _select_dispatcher(provider: str, dispatchers: dict[str, _Dispatcher]) -> _Dispatcher:
  dispatcher = dispatchers.get(provider)
  if dispatcher is None:
    raise KeyError(f"Unsupported provider '{provider}' for system workflows registry")
  return dispatcher


async def get_active_workflow_v1(request: DBRequest, *, provider: str) -> DBResponse:
  params = GetActiveWorkflowParams.model_validate(request.payload)
  result = await _select_dispatcher(provider, _GET_ACTIVE_WORKFLOW_DISPATCHERS)(params.model_dump())
  return DBResponse(op=request.op, payload=result.payload, rowcount=result.rowcount)


async def count_active_runs_by_workflow_name_v1(request: DBRequest, *, provider: str) -> DBResponse:
  params = CountActiveRunsByWorkflowNameParams.model_validate(request.payload)
  result = await _select_dispatcher(provider, _COUNT_ACTIVE_RUNS_BY_NAME_DISPATCHERS)(params.model_dump())
  return DBResponse(op=request.op, payload=result.payload, rowcount=result.rowcount)


async def list_workflows_v1(request: DBRequest, *, provider: str) -> DBResponse:
  params = ListWorkflowsParams.model_validate(request.payload)
  result = await _select_dispatcher(provider, _LIST_WORKFLOWS_DISPATCHERS)(params.model_dump())
  return DBResponse(op=request.op, payload=result.payload, rowcount=result.rowcount)


async def list_workflow_actions_v1(request: DBRequest, *, provider: str) -> DBResponse:
  params = ListWorkflowActionsParams.model_validate(request.payload)
  result = await _select_dispatcher(provider, _LIST_WORKFLOW_ACTIONS_DISPATCHERS)(params.model_dump())
  return DBResponse(op=request.op, payload=result.payload, rowcount=result.rowcount)


async def create_workflow_run_v1(request: DBRequest, *, provider: str) -> DBResponse:
  params = CreateWorkflowRunParams.model_validate(request.payload)
  result = await _select_dispatcher(provider, _CREATE_WORKFLOW_RUN_DISPATCHERS)(params.model_dump())
  return DBResponse(op=request.op, payload=result.payload, rowcount=result.rowcount)


async def get_workflow_run_v1(request: DBRequest, *, provider: str) -> DBResponse:
  params = GetWorkflowRunParams.model_validate(request.payload)
  result = await _select_dispatcher(provider, _GET_WORKFLOW_RUN_DISPATCHERS)(params.model_dump())
  return DBResponse(op=request.op, payload=result.payload, rowcount=result.rowcount)


async def list_workflow_runs_v1(request: DBRequest, *, provider: str) -> DBResponse:
  params = ListWorkflowRunsParams.model_validate(request.payload)
  result = await _select_dispatcher(provider, _LIST_WORKFLOW_RUNS_DISPATCHERS)(params.model_dump())
  return DBResponse(op=request.op, payload=result.payload, rowcount=result.rowcount)


async def update_workflow_run_v1(request: DBRequest, *, provider: str) -> DBResponse:
  params = UpdateWorkflowRunParams.model_validate(request.payload)
  result = await _select_dispatcher(provider, _UPDATE_WORKFLOW_RUN_DISPATCHERS)(params.model_dump(exclude_unset=True))
  return DBResponse(op=request.op, payload=result.payload, rowcount=result.rowcount)


async def create_workflow_run_action_v1(request: DBRequest, *, provider: str) -> DBResponse:
  params = CreateWorkflowRunActionParams.model_validate(request.payload)
  result = await _select_dispatcher(provider, _CREATE_WORKFLOW_RUN_ACTION_DISPATCHERS)(params.model_dump())
  return DBResponse(op=request.op, payload=result.payload, rowcount=result.rowcount)


async def update_workflow_run_action_v1(request: DBRequest, *, provider: str) -> DBResponse:
  params = UpdateWorkflowRunActionParams.model_validate(request.payload)
  result = await _select_dispatcher(provider, _UPDATE_WORKFLOW_RUN_ACTION_DISPATCHERS)(params.model_dump(exclude_unset=True))
  return DBResponse(op=request.op, payload=result.payload, rowcount=result.rowcount)


async def list_workflow_run_actions_v1(request: DBRequest, *, provider: str) -> DBResponse:
  params = ListWorkflowRunActionsParams.model_validate(request.payload)
  result = await _select_dispatcher(provider, _LIST_WORKFLOW_RUN_ACTIONS_DISPATCHERS)(params.model_dump())
  return DBResponse(op=request.op, payload=result.payload, rowcount=result.rowcount)
