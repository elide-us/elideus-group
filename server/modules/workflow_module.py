from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Any

from fastapi import FastAPI, HTTPException

from queryregistry.system.workflows import (
  count_active_runs_by_workflow_name_request,
  create_workflow_run_action_request,
  create_workflow_run_request,
  get_active_workflow_request,
  get_workflow_run_request,
  list_workflow_actions_request,
  list_workflow_run_actions_request,
  list_workflow_runs_request,
  list_workflows_request,
  update_workflow_run_action_request,
  update_workflow_run_request,
)
from queryregistry.rpcdispatch.functions import get_function_request
from queryregistry.rpcdispatch.functions.models import GetFunctionParams

from queryregistry.system.workflows.models import (
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

from . import BaseModule
from .db_module import DbModule

STATUS_PENDING = 0
STATUS_RUNNING = 1
STATUS_COMPLETED = 2
STATUS_FAILED = 3
STATUS_CANCELLED = 4
STATUS_WAITING = 5
STATUS_PAUSED = 6
STATUS_ROLLING_BACK = 7
STATUS_ROLLED_BACK = 8
STATUS_ROLLBACK_FAILED = 9
STATUS_STALLED = 10

RETRYABLE_STATUSES = {STATUS_FAILED, STATUS_ROLLBACK_FAILED, STATUS_STALLED}
RESUMABLE_STATUSES = {STATUS_FAILED, STATUS_WAITING, STATUS_PAUSED, STATUS_STALLED}
NON_TERMINAL_FOR_CONCURRENCY = {STATUS_PENDING, STATUS_RUNNING, STATUS_WAITING, STATUS_PAUSED}
RETRYABLE_DISPOSITIONS = {0, 1, 3}

POLL_TRIGGER_TYPE = 7


class WorkflowModule(BaseModule):
  def __init__(self, app: FastAPI):
    super().__init__(app)
    self.db: DbModule | None = None
    self._tick_task: asyncio.Task | None = None
    self._poll_task: asyncio.Task | None = None

  async def startup(self):
    self.db = self.app.state.db
    await self.db.on_ready()
    self.app.state.workflow = self
    self._tick_task = asyncio.create_task(self._tick_loop())
    self._poll_task = asyncio.create_task(self._poll_loop())
    logging.debug("[WorkflowModule] loaded")
    self.mark_ready()

  async def shutdown(self):
    for task in (self._tick_task, self._poll_task):
      if task and not task.done():
        task.cancel()
        try:
          await task
        except asyncio.CancelledError:
          pass
    self._tick_task = None
    self._poll_task = None
    self.db = None
    logging.info("[WorkflowModule] shutdown")

  async def submit(
    self,
    workflow_name: str,
    payload: dict[str, Any],
    trigger_type_code: int,
    trigger_ref: str | None,
    created_by: str | None = None,
  ) -> dict[str, Any]:
    assert self.db
    workflow = await self.get_workflow(workflow_name)
    if not workflow:
      raise HTTPException(status_code=404, detail=f"Workflow '{workflow_name}' not found")

    max_concurrency = int(workflow.get("max_concurrency") or 0)
    if max_concurrency > 0:
      count_res = await self.db.run(
        count_active_runs_by_workflow_name_request(
          CountActiveRunsByWorkflowNameParams(name=workflow_name)
        )
      )
      active_runs = int((count_res.rows[0] or {}).get("element_count") or 0) if count_res.rows else 0
      if active_runs >= max_concurrency:
        raise HTTPException(
          status_code=409,
          detail=f"Workflow '{workflow_name}' is at max concurrency ({max_concurrency})",
        )

    create_params = CreateWorkflowRunParams(
      workflows_guid=workflow["guid"],
      status=STATUS_PENDING,
      payload=json.dumps(payload),
      context=json.dumps({}),
      trigger_type=trigger_type_code,
      trigger_ref=trigger_ref,
      created_by=created_by,
    )
    res = await self.db.run(create_workflow_run_request(create_params))
    run = self._map_run(dict(res.rows[0]))
    asyncio.create_task(self._execute(run["guid"]))
    return run

  async def get(self, guid: str) -> dict[str, Any] | None:
    assert self.db
    res = await self.db.run(get_workflow_run_request(GetWorkflowRunParams(guid=guid)))
    if not res.rows:
      return None
    return self._map_run(dict(res.rows[0]))

  async def get_or_404(self, guid: str) -> dict[str, Any]:
    run = await self.get(guid)
    if not run:
      raise HTTPException(status_code=404, detail="Workflow run not found")
    return run

  async def list(self, status: int | None = None) -> list[dict[str, Any]]:
    assert self.db
    res = await self.db.run(list_workflow_runs_request(ListWorkflowRunsParams(status=status)))
    return [self._map_run(dict(row)) for row in res.rows]

  async def list_run_actions(self, runs_recid: int) -> list[dict[str, Any]]:
    assert self.db
    res = await self.db.run(
      list_workflow_run_actions_request(ListWorkflowRunActionsParams(runs_recid=runs_recid))
    )
    return [self._map_run_action(dict(row)) for row in res.rows]

  async def list_workflows(self, status: int | None = None) -> list[dict[str, Any]]:
    assert self.db
    res = await self.db.run(list_workflows_request(ListWorkflowsParams(status=status)))
    return [self._map_workflow(dict(row)) for row in res.rows]

  async def cancel(self, run_guid: str) -> dict[str, Any]:
    run = await self.get_or_404(run_guid)
    if int(run.get("status") or 0) in {STATUS_COMPLETED, STATUS_CANCELLED, STATUS_ROLLED_BACK}:
      return run
    return await self._update_run(
      int(run["recid"]),
      status=STATUS_CANCELLED,
      ended_on=self._iso_now(),
    )

  async def resume(self, run_guid: str) -> dict[str, Any]:
    run = await self.get_or_404(run_guid)
    run_status = int(run.get("status") or 0)
    if run_status not in RESUMABLE_STATUSES:
      raise HTTPException(status_code=409, detail="Run is not resumable")

    actions = await self.list_run_actions(int(run["recid"]))
    waiting_action = next((a for a in actions if int(a.get("status") or -1) == STATUS_WAITING), None)
    failed_action = next((a for a in actions if int(a.get("status") or -1) == STATUS_FAILED), None)

    if run_status == STATUS_WAITING and waiting_action:
      await self._poll_waiting_action(run, waiting_action)
      updated = await self.get_or_404(run_guid)
      if int(updated.get("status") or 0) == STATUS_WAITING:
        return updated

    if run_status == STATUS_FAILED and failed_action:
      await self._update_run_action(int(failed_action["recid"]), status=STATUS_PENDING, error=None)

    await self._update_run(int(run["recid"]), status=STATUS_RUNNING)
    asyncio.create_task(self._execute(run_guid))
    return await self.get_or_404(run_guid)

  async def retry_action(self, run_action_guid: str) -> dict[str, Any]:
    run_action = await self._get_run_action_by_guid(run_action_guid)
    if not run_action:
      raise HTTPException(status_code=404, detail="Workflow run action not found")

    if int(run_action.get("status") or -1) not in RETRYABLE_STATUSES:
      raise HTTPException(status_code=409, detail="Run action status does not allow retry")

    action_def = await self._get_action_definition(str(run_action["actions_guid"]))
    if not action_def:
      raise HTTPException(status_code=404, detail="Workflow action definition not found")

    disposition_code = int(action_def.get("dispositions_recid") or -1)
    if disposition_code not in RETRYABLE_DISPOSITIONS:
      raise HTTPException(status_code=409, detail="Disposition does not allow retry")

    retry_count = int(run_action.get("retry_count") or 0) + 1
    await self._update_run_action(
      int(run_action["recid"]),
      status=STATUS_RUNNING,
      retry_count=retry_count,
      error=None,
      started_on=self._iso_now(),
      ended_on=None,
    )

    run = await self.get_or_404(str(run_action["run_guid"]))
    try:
      payload = run.get("payload") or {}
      context = run.get("context") or {}
      input_payload = self._build_action_input(payload, context, action_def)
      func = self._resolve_action_callable(action_def)
      result = await self._call_action(func, input_payload)
      await self._complete_action_success(
        run=run,
        run_action=run_action,
        action_def=action_def,
        result=result,
        context=context,
      )
      await self._update_run(
        int(run["recid"]),
        status=STATUS_RUNNING,
        action_index=int(action_def.get("sequence") or 0) + 1,
      )
      asyncio.create_task(self._execute(str(run["guid"])))
    except Exception as exc:
      await self._update_run_action(
        int(run_action["recid"]),
        status=STATUS_FAILED,
        error=str(exc),
        ended_on=self._iso_now(),
      )
      await self._update_run(int(run["recid"]), status=STATUS_FAILED, error=str(exc))

    refreshed = await self._get_run_action_by_guid(run_action_guid)
    if not refreshed:
      raise HTTPException(status_code=500, detail="Retry completed but action was not reloadable")
    return refreshed

  async def rollback(self, run_guid: str) -> dict[str, Any]:
    run = await self.get_or_404(run_guid)
    await self._update_run(int(run["recid"]), status=STATUS_ROLLING_BACK)
    run_actions = await self.list_run_actions(int(run["recid"]))
    completed_actions = [a for a in run_actions if int(a.get("status") or -1) == STATUS_COMPLETED]
    completed_actions.sort(key=lambda row: int(row.get("sequence") or 0), reverse=True)

    try:
      for run_action in completed_actions:
        action_def = await self._get_action_definition(str(run_action["actions_guid"]))
        if not action_def:
          continue
        disposition = int(action_def.get("dispositions_recid") or 0)
        if disposition == 0:
          continue
        if disposition in {2, 3}:
          break
        rollback_function_guid = action_def.get("element_rollback_functions_guid")
        if rollback_function_guid is None:
          logging.error(
            "[WorkflowModule] reversible action %s has no rollback function; stopping rollback",
            run_action.get("guid"),
          )
          break

        rollback_def = await self._get_reflection_function(str(rollback_function_guid))
        rollback_callable = self._resolve_callable_from_function(rollback_def)
        await self._call_action(rollback_callable, {"run_action_guid": run_action["guid"]})

      await self._update_run(int(run["recid"]), status=STATUS_ROLLED_BACK, ended_on=self._iso_now())
    except Exception as exc:
      logging.exception("[WorkflowModule] rollback failed for run %s", run_guid)
      await self._update_run(int(run["recid"]), status=STATUS_ROLLBACK_FAILED, error=str(exc))

    return await self.get_or_404(run_guid)

  async def _tick_loop(self):
    while True:
      try:
        pending_runs = await self.list(status=STATUS_PENDING)
        for run in pending_runs:
          asyncio.create_task(self._execute(str(run["guid"])))
      except asyncio.CancelledError:
        raise
      except Exception:
        logging.exception("[WorkflowModule] tick loop error")
      await asyncio.sleep(5)

  async def _poll_loop(self):
    while True:
      try:
        waiting_runs = await self.list(status=STATUS_WAITING)
        now = datetime.now(timezone.utc)
        for run in waiting_runs:
          actions = await self.list_run_actions(int(run["recid"]))
          waiting_actions = [a for a in actions if int(a.get("status") or -1) == STATUS_WAITING]
          for action in waiting_actions:
            poll_interval = int(action.get("poll_interval_seconds") or 30)
            modified_on = self._parse_dt(action.get("modified_on"))
            if not modified_on:
              continue
            if (now - modified_on).total_seconds() < poll_interval:
              continue
            await self._poll_waiting_action(run, action)
      except asyncio.CancelledError:
        raise
      except Exception:
        logging.exception("[WorkflowModule] poll loop error")
      await asyncio.sleep(30)

  async def _poll_waiting_action(self, run: dict[str, Any], run_action: dict[str, Any]):
    action_def = await self._get_action_definition(str(run_action["actions_guid"]))
    if not action_def:
      return
    func = self._resolve_action_callable(action_def)
    result = await self._call_action(
      func,
      {
        "_poll": True,
        "external_ref": run_action.get("external_ref"),
        "trigger_type": POLL_TRIGGER_TYPE,
      },
    )
    if isinstance(result, dict) and result.get("_waiting"):
      await self._update_run_action(
        int(run_action["recid"]),
        status=STATUS_WAITING,
        external_ref=str(result.get("external_ref") or run_action.get("external_ref") or ""),
        poll_interval_seconds=int(result.get("poll_interval_seconds") or run_action.get("poll_interval_seconds") or 30),
      )
      await self._update_run(int(run["recid"]), status=STATUS_WAITING)
      return

    context = run.get("context") or {}
    await self._complete_action_success(
      run=run,
      run_action=run_action,
      action_def=action_def,
      result=result,
      context=context,
    )
    await self._update_run(
      int(run["recid"]),
      status=STATUS_RUNNING,
      action_index=int(run_action.get("sequence") or 0) + 1,
    )
    asyncio.create_task(self._execute(str(run["guid"])))

  async def _execute(self, run_guid: str) -> None:
    run = await self.get(run_guid)
    if not run:
      return
    run_status = int(run.get("status") or 0)
    if run_status in {STATUS_COMPLETED, STATUS_CANCELLED, STATUS_ROLLED_BACK}:
      return

    assert self.db
    run = await self._update_run(
      int(run["recid"]),
      status=STATUS_RUNNING,
      started_on=run.get("started_on") or self._iso_now(),
    )

    actions = await self.list_actions(str(run["workflows_guid"]))
    payload = run.get("payload") or {}
    context = run.get("context") or {}
    start_index = int(run.get("action_index") or 0)

    for action in actions:
      sequence = int(action.get("sequence") or 0)
      if sequence < start_index:
        continue

      await self._update_run(
        int(run["recid"]),
        current_action=str(action.get("name") or action.get("guid")),
        action_index=sequence,
      )

      input_payload = self._build_action_input(payload, context, action)
      run_action = await self._create_run_action(
        runs_recid=int(run["recid"]),
        actions_guid=str(action["guid"]),
        sequence=sequence,
        input_data=input_payload,
      )

      try:
        func = self._resolve_action_callable(action)
        result = await self._call_action(func, input_payload)

        if isinstance(result, dict) and result.get("_waiting"):
          await self._update_run_action(
            int(run_action["recid"]),
            status=STATUS_WAITING,
            output=json.dumps(result),
            external_ref=str(result.get("external_ref") or ""),
            poll_interval_seconds=int(result.get("poll_interval_seconds") or 30),
          )
          await self._update_run(int(run["recid"]), status=STATUS_WAITING)
          return

        await self._complete_action_success(
          run=run,
          run_action=run_action,
          action_def=action,
          result=result,
          context=context,
        )
      except Exception as exc:
        await self._update_run_action(
          int(run_action["recid"]),
          status=STATUS_FAILED,
          error=str(exc),
          ended_on=self._iso_now(),
        )
        if bool(action.get("is_optional")):
          logging.exception("[WorkflowModule] optional action %s failed", action.get("guid"))
          continue
        await self._update_run(int(run["recid"]), status=STATUS_FAILED, error=str(exc))
        return

    await self._update_run(
      int(run["recid"]),
      status=STATUS_COMPLETED,
      current_action=None,
      ended_on=self._iso_now(),
      context=json.dumps(context),
    )

  async def get_workflow(self, name: str) -> dict[str, Any] | None:
    assert self.db
    res = await self.db.run(get_active_workflow_request(GetActiveWorkflowParams(name=name)))
    if not res.rows:
      return None
    return self._map_workflow(dict(res.rows[0]))

  async def list_actions(self, workflows_guid: str) -> list[dict[str, Any]]:
    assert self.db
    res = await self.db.run(
      list_workflow_actions_request(ListWorkflowActionsParams(workflows_guid=workflows_guid))
    )
    mapped = [self._map_action(dict(row)) for row in res.rows]
    mapped = [row for row in mapped if bool(row.get("is_active"))]
    mapped.sort(key=lambda row: int(row.get("sequence") or 0))
    return mapped

  async def _create_run_action(
    self,
    runs_recid: int,
    actions_guid: str,
    sequence: int,
    input_data: dict[str, Any],
  ) -> dict[str, Any]:
    assert self.db
    params = CreateWorkflowRunActionParams(
      runs_recid=runs_recid,
      actions_guid=actions_guid,
      status=STATUS_RUNNING,
      input=json.dumps(input_data),
      sequence=sequence,
      retry_count=0,
      started_on=self._iso_now(),
    )
    res = await self.db.run(create_workflow_run_action_request(params))
    return self._map_run_action(dict(res.rows[0]))

  async def _update_run(self, recid: int, **kwargs: Any) -> dict[str, Any]:
    assert self.db
    params = UpdateWorkflowRunParams(recid=recid, **kwargs)
    res = await self.db.run(update_workflow_run_request(params))
    return self._map_run(dict(res.rows[0]))

  async def _update_run_action(self, recid: int, **kwargs: Any) -> dict[str, Any]:
    assert self.db
    params = UpdateWorkflowRunActionParams(recid=recid, **kwargs)
    res = await self.db.run(update_workflow_run_action_request(params))
    return self._map_run_action(dict(res.rows[0]))

  async def _get_run_action_by_guid(self, run_action_guid: str) -> dict[str, Any] | None:
    runs = await self.list()
    for run in runs:
      actions = await self.list_run_actions(int(run["recid"]))
      for run_action in actions:
        if str(run_action.get("guid")) == run_action_guid:
          run_action["run_guid"] = run["guid"]
          return run_action
    return None

  async def _get_action_definition(self, actions_guid: str) -> dict[str, Any] | None:
    assert self.db
    workflows = await self.db.run(list_workflow_runs_request(ListWorkflowRunsParams()))
    seen_workflows: set[str] = set()
    for row in workflows.rows:
      guid = str(row.get("workflows_guid") or "")
      if not guid or guid in seen_workflows:
        continue
      seen_workflows.add(guid)
      actions = await self.list_actions(guid)
      for action in actions:
        if str(action.get("guid")) == actions_guid:
          return action
    return None

  async def _get_reflection_function(self, function_guid: str) -> dict[str, Any]:
    assert self.db
    res = await self.db.run(get_function_request(GetFunctionParams(guid=function_guid)))
    if not res.rows:
      raise HTTPException(status_code=404, detail=f"Reflection function {function_guid} not found")
    return dict(res.rows[0])

  def _resolve_action_callable(self, action_def: dict[str, Any]):
    module_attr = action_def.get("module_attr")
    method_name = action_def.get("method_name")
    if not module_attr or not method_name:
      raise ValueError("Action definition is missing module/method metadata")
    module = getattr(self.app.state, str(module_attr), None)
    if module is None:
      raise ValueError(f"Module '{module_attr}' not found on app.state")
    method = getattr(module, str(method_name), None)
    if method is None:
      raise ValueError(f"Method '{method_name}' not found on module '{module_attr}'")
    return method

  def _resolve_callable_from_function(self, function_row: dict[str, Any]):
    module = getattr(self.app.state, str(function_row.get("element_module_attr") or ""), None)
    if module is None:
      raise ValueError("Rollback module could not be resolved")
    method = getattr(module, str(function_row.get("element_method_name") or ""), None)
    if method is None:
      raise ValueError("Rollback method could not be resolved")
    return method

  async def _call_action(self, method: Any, payload: dict[str, Any]):
    value = method(payload)
    if asyncio.iscoroutine(value):
      return await value
    return value

  async def _complete_action_success(
    self,
    run: dict[str, Any],
    run_action: dict[str, Any],
    action_def: dict[str, Any],
    result: Any,
    context: dict[str, Any],
  ):
    contribution = result.get("context") if isinstance(result, dict) else None
    if isinstance(contribution, dict):
      context.update(contribution)

    await self._update_run_action(
      int(run_action["recid"]),
      status=STATUS_COMPLETED,
      output=json.dumps(result),
      ended_on=self._iso_now(),
      error=None,
    )
    await self._update_run(
      int(run["recid"]),
      context=json.dumps(context),
      current_action=str(action_def.get("name") or action_def.get("guid") or ""),
      action_index=int(action_def.get("sequence") or 0),
      result=json.dumps(result) if result is not None else None,
      error=None,
    )

  def _build_action_input(
    self,
    payload: dict[str, Any],
    context: dict[str, Any],
    action_def: dict[str, Any],
  ) -> dict[str, Any]:
    action_config = self._decode_json(action_def.get("config")) or {}
    resolved_config = self._resolve_templates(action_config, payload=payload, context=context)
    return {
      "payload": payload,
      "context": context,
      "config": resolved_config,
      "action_guid": action_def.get("guid"),
    }

  def _resolve_templates(
    self,
    config: dict[str, Any],
    *,
    payload: dict[str, Any],
    context: dict[str, Any],
  ) -> dict[str, Any]:
    replacements: dict[str, str] = {}
    for key, value in {**payload, **context}.items():
      if isinstance(value, (str, int, float, bool)):
        replacements[key] = str(value)

    resolved: dict[str, Any] = {}
    for key, value in config.items():
      if not isinstance(value, str):
        resolved[key] = value
        continue
      output = value
      for rep_key, rep_val in replacements.items():
        output = output.replace("{" + rep_key + "}", rep_val)
      resolved[key] = output
    return resolved

  @staticmethod
  def _decode_json(raw: Any) -> dict[str, Any] | list[Any] | None:
    if raw is None:
      return None
    if isinstance(raw, (dict, list)):
      return raw
    if not isinstance(raw, str) or not raw:
      return None
    try:
      return json.loads(raw)
    except json.JSONDecodeError:
      return None

  def _map_workflow(self, row: dict[str, Any]) -> dict[str, Any]:
    return {
      "guid": row.get("element_guid"),
      "name": row.get("element_name"),
      "description": row.get("element_description"),
      "version": row.get("element_version"),
      "status": row.get("element_status"),
      "is_active": row.get("element_is_active"),
      "max_concurrency": row.get("element_max_concurrency"),
      "stall_threshold_seconds": row.get("element_stall_threshold_seconds"),
      "created_on": row.get("element_created_on"),
      "modified_on": row.get("element_modified_on"),
    }

  def _map_action(self, row: dict[str, Any]) -> dict[str, Any]:
    return {
      "guid": row.get("element_guid"),
      "workflows_guid": row.get("workflows_guid"),
      "name": row.get("element_name"),
      "description": row.get("element_description"),
      "functions_guid": row.get("functions_guid"),
      "dispositions_recid": row.get("dispositions_recid"),
      "rollback_functions_guid": row.get("element_rollback_functions_guid"),
      "sequence": row.get("element_sequence"),
      "is_optional": bool(row.get("element_is_optional")),
      "timeout_seconds": row.get("element_timeout_seconds"),
      "config": row.get("element_config"),
      "is_active": row.get("element_is_active"),
      "module_attr": row.get("element_module_attr"),
      "method_name": row.get("element_method_name"),
      "disposition_name": row.get("disposition_name"),
      "element_rollback_functions_guid": row.get("element_rollback_functions_guid"),
    }

  def _map_run(self, row: dict[str, Any]) -> dict[str, Any]:
    return {
      "recid": row.get("recid"),
      "guid": row.get("element_guid"),
      "workflows_guid": row.get("workflows_guid"),
      "status": row.get("element_status"),
      "payload": self._decode_json(row.get("element_payload")) or {},
      "context": self._decode_json(row.get("element_context")) or {},
      "current_action": row.get("element_current_action"),
      "action_index": row.get("element_action_index"),
      "error": row.get("element_error"),
      "trigger_type": row.get("element_trigger_type"),
      "trigger_ref": row.get("element_trigger_ref"),
      "result": self._decode_json(row.get("element_result")),
      "created_by": row.get("element_created_by"),
      "started_on": row.get("element_started_on"),
      "ended_on": row.get("element_ended_on"),
      "created_on": row.get("element_created_on"),
      "modified_on": row.get("element_modified_on"),
    }

  def _map_run_action(self, row: dict[str, Any]) -> dict[str, Any]:
    return {
      "recid": row.get("recid"),
      "guid": row.get("element_guid"),
      "runs_recid": row.get("runs_recid"),
      "actions_guid": row.get("actions_guid"),
      "status": row.get("element_status"),
      "input": self._decode_json(row.get("element_input")),
      "output": self._decode_json(row.get("element_output")),
      "error": row.get("element_error"),
      "sequence": row.get("element_sequence"),
      "retry_count": row.get("element_retry_count"),
      "external_ref": row.get("element_external_ref"),
      "poll_interval_seconds": row.get("element_poll_interval_seconds"),
      "started_on": row.get("element_started_on"),
      "ended_on": row.get("element_ended_on"),
      "created_on": row.get("element_created_on"),
      "modified_on": row.get("element_modified_on"),
    }

  @staticmethod
  def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()

  @staticmethod
  def _parse_dt(raw: str | None) -> datetime | None:
    if not raw:
      return None
    parsed = datetime.fromisoformat(raw)
    if parsed.tzinfo is None:
      return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)
