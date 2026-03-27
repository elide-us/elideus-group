from __future__ import annotations

import asyncio
import importlib
import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import FastAPI, HTTPException

from queryregistry.system.workflows import (
  create_workflow_run_request,
  create_workflow_run_step_request,
  get_active_workflow_request,
  get_workflow_run_request,
  list_workflow_runs_request,
  list_workflow_steps_request,
  update_workflow_run_request,
  update_workflow_run_step_request,
)
from queryregistry.system.workflows.models import (
  CreateWorkflowRunParams,
  CreateWorkflowRunStepParams,
  GetActiveWorkflowParams,
  GetWorkflowRunParams,
  ListWorkflowRunsParams,
  ListWorkflowStepsParams,
  UpdateWorkflowRunParams,
  UpdateWorkflowRunStepParams,
)
from server.workflows import StepResult, WorkflowStep

from . import BaseModule
from .db_module import DbModule

STATUS_QUEUED = 0
STATUS_RUNNING = 1
STATUS_COMPLETED = 4
STATUS_FAILED = 5
STATUS_CANCELLED = 6
STATUS_ROLLING_BACK = 7
STATUS_ROLLED_BACK = 8

STEP_STATUS_PENDING = 0
STEP_STATUS_RUNNING = 1
STEP_STATUS_COMPLETED = 4
STEP_STATUS_FAILED = 5
STEP_STATUS_SKIPPED = 6
STEP_STATUS_ROLLED_BACK = 7


class WorkflowModule(BaseModule):
  def __init__(self, app: FastAPI):
    super().__init__(app)
    self.db: DbModule | None = None
    self.tick_interval_seconds = 5
    self._loop_task: asyncio.Task | None = None
    self._loop_lock = asyncio.Lock()

  async def startup(self):
    self.db = self.app.state.db
    await self.db.on_ready()
    self.app.state.workflow = self
    self._loop_task = asyncio.create_task(self._tick_loop())
    logging.debug("[WorkflowModule] loaded")
    self.mark_ready()

  async def shutdown(self):
    if self._loop_task and not self._loop_task.done():
      self._loop_task.cancel()
      try:
        await self._loop_task
      except asyncio.CancelledError:
        pass
    self._loop_task = None
    self.db = None
    logging.info("[WorkflowModule] shutdown")

  async def submit(
    self,
    workflow_name: str,
    payload: dict[str, Any],
    source_type: str | None = None,
    source_id: str | None = None,
    created_by: str | None = None,
    timeout_seconds: int | None = None,
  ) -> dict[str, Any]:
    assert self.db
    workflow = await self._get_active_workflow(workflow_name)
    if not workflow:
      raise HTTPException(status_code=404, detail=f"Workflow '{workflow_name}' not found")

    now = datetime.now(timezone.utc)
    timeout_at = now + timedelta(seconds=timeout_seconds) if timeout_seconds else None
    params = CreateWorkflowRunParams(
      workflows_guid=workflow["guid"],
      status=STATUS_QUEUED,
      payload=json.dumps(payload),
      context=json.dumps({}),
      source_type=source_type,
      source_id=source_id,
      created_by=created_by,
      timeout_at=timeout_at.isoformat() if timeout_at else None,
    )
    res = await self.db.run(create_workflow_run_request(params))
    return self._map_run(dict(res.rows[0]))

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

  async def cancel(self, guid: str) -> dict[str, Any]:
    run = await self.get_or_404(guid)
    if run["status"] in {STATUS_COMPLETED, STATUS_FAILED, STATUS_CANCELLED, STATUS_ROLLED_BACK}:
      return run
    return await self._update_run(run["recid"], status=STATUS_CANCELLED, ended_on=datetime.now(timezone.utc).isoformat())

  async def execute(self, guid: str) -> dict[str, Any]:
    run = await self.get_or_404(guid)
    await self._execute_run(run)
    return await self.get_or_404(guid)

  async def rollback(self, guid: str) -> dict[str, Any]:
    run = await self.get_or_404(guid)
    await self._rollback_run(run, [], run.get("payload") or {}, run.get("context") or {})
    return await self.get_or_404(guid)

  async def _tick_loop(self):
    while True:
      try:
        await self.tick_once()
      except asyncio.CancelledError:
        raise
      except Exception as exc:
        logging.exception("[WorkflowModule] Tick error: %s", exc)
      await asyncio.sleep(self.tick_interval_seconds)

  async def tick_once(self):
    async with self._loop_lock:
      queued_runs = await self.list(status=STATUS_QUEUED)
      for run in queued_runs:
        await self._execute_run(run)

  async def _execute_run(self, run: dict[str, Any]):
    assert self.db
    if run["status"] == STATUS_CANCELLED:
      return

    payload = run.get("payload") or {}
    context = run.get("context") or {}
    steps = await self._list_steps(run["workflows_guid"])
    rollback_stack: list[dict[str, Any]] = []

    await self._update_run(run["recid"], status=STATUS_RUNNING, started_on=datetime.now(timezone.utc).isoformat())

    for index, step in enumerate(steps, start=1):
      step_input = json.dumps(context)
      run_step = await self._create_run_step(
        run["recid"],
        steps_guid=step["guid"],
        disposition=step["disposition"],
        input_data=step_input,
      )

      await self._update_run(run["recid"], current_step=step["name"], step_index=index)
      step_instance = self._load_step_instance(step["class_path"])
      config = self._decode_json(step.get("config")) or {}

      try:
        await self._update_run_step(run_step["recid"], status=STEP_STATUS_RUNNING, started_on=datetime.now(timezone.utc).isoformat())
        await step_instance.init_step(self.app, payload, context, config)
        result = await step_instance.try_step(self.app, payload, context, config)
        await self._complete_step_success(step_instance, step, result, payload, context, rollback_stack)
        await self._update_run_step(
          run_step["recid"],
          status=STEP_STATUS_COMPLETED,
          output=json.dumps(result.model_dump()),
          ended_on=datetime.now(timezone.utc).isoformat(),
        )
      except Exception as exc:
        await self._handle_step_failure(
          run=run,
          step=step,
          run_step=run_step,
          step_instance=step_instance,
          payload=payload,
          context=context,
          config=config,
          rollback_stack=rollback_stack,
          error=exc,
        )
        return
      finally:
        await step_instance.finally_step(self.app, payload, context, config)

    await self._update_run(
      run["recid"],
      status=STATUS_COMPLETED,
      current_step=None,
      error=None,
      context=json.dumps(context),
      ended_on=datetime.now(timezone.utc).isoformat(),
    )

  async def _complete_step_success(
    self,
    step_instance: WorkflowStep,
    step: dict[str, Any],
    result: StepResult,
    payload: dict[str, Any],
    context: dict[str, Any],
    rollback_stack: list[dict[str, Any]],
  ):
    if result.output:
      context.update(result.output)
    if (
      step.get("step_type") == "stack"
      and step.get("disposition") == "reversible"
      and result.compensation is not None
    ):
      rollback_stack.append(
        {
          "instance": step_instance,
          "payload": payload,
          "context": dict(context),
          "compensation": result.compensation,
        }
      )

  async def _handle_step_failure(
    self,
    run: dict[str, Any],
    step: dict[str, Any],
    run_step: dict[str, Any],
    step_instance: WorkflowStep,
    payload: dict[str, Any],
    context: dict[str, Any],
    config: dict[str, Any],
    rollback_stack: list[dict[str, Any]],
    error: Exception,
  ):
    await self._update_run_step(
      run_step["recid"],
      status=STEP_STATUS_FAILED,
      error=str(error),
      ended_on=datetime.now(timezone.utc).isoformat(),
    )
    await step_instance.catch_step(self.app, payload, context, config, error)

    if step.get("is_optional"):
      await self._update_run_step(run_step["recid"], status=STEP_STATUS_SKIPPED)
      return

    await self._update_run(
      run["recid"],
      status=STATUS_ROLLING_BACK,
      error=str(error),
      context=json.dumps(context),
      ended_on=datetime.now(timezone.utc).isoformat(),
    )
    await self._rollback_run(run, rollback_stack, payload, context)

  async def _rollback_run(
    self,
    run: dict[str, Any],
    rollback_stack: list[dict[str, Any]],
    payload: dict[str, Any],
    context: dict[str, Any],
  ):
    for entry in reversed(rollback_stack):
      try:
        await entry["instance"].compensate_step(
          self.app,
          entry["payload"],
          entry["context"],
          entry["compensation"],
        )
      except Exception as exc:
        logging.exception("[WorkflowModule] rollback compensate failed: %s", exc)

    await self._update_run(
      run["recid"],
      status=STATUS_ROLLED_BACK,
      context=json.dumps(context),
      current_step=None,
      ended_on=datetime.now(timezone.utc).isoformat(),
    )

  async def _get_active_workflow(self, name: str) -> dict[str, Any] | None:
    assert self.db
    res = await self.db.run(get_active_workflow_request(GetActiveWorkflowParams(name=name)))
    if not res.rows:
      return None
    row = dict(res.rows[0])
    return {
      "guid": row.get("element_guid"),
      "name": row.get("element_name"),
      "description": row.get("element_description"),
      "version": row.get("element_version"),
      "status": row.get("element_status"),
    }

  async def _list_steps(self, workflows_guid: str) -> list[dict[str, Any]]:
    assert self.db
    res = await self.db.run(list_workflow_steps_request(ListWorkflowStepsParams(workflows_guid=workflows_guid)))
    mapped: list[dict[str, Any]] = []
    for row in res.rows:
      mapped.append(
        {
          "guid": row.get("element_guid"),
          "workflows_guid": row.get("workflows_guid"),
          "name": row.get("element_name"),
          "description": row.get("element_description"),
          "step_type": row.get("element_step_type"),
          "disposition": row.get("element_disposition"),
          "class_path": row.get("element_class_path"),
          "sequence": row.get("element_sequence"),
          "is_optional": bool(row.get("element_is_optional")),
          "timeout_seconds": row.get("element_timeout_seconds"),
          "config": row.get("element_config"),
        }
      )
    return mapped

  async def _create_run_step(self, runs_recid: int, steps_guid: str, disposition: str, input_data: str) -> dict[str, Any]:
    assert self.db
    params = CreateWorkflowRunStepParams(
      runs_recid=runs_recid,
      steps_guid=steps_guid,
      status=STEP_STATUS_PENDING,
      disposition=disposition,
      input=input_data,
    )
    res = await self.db.run(create_workflow_run_step_request(params))
    return dict(res.rows[0])

  async def _update_run(self, recid: int, **kwargs: Any) -> dict[str, Any]:
    assert self.db
    params = UpdateWorkflowRunParams(recid=recid, **kwargs)
    res = await self.db.run(update_workflow_run_request(params))
    return self._map_run(dict(res.rows[0]))

  async def _update_run_step(self, recid: int, **kwargs: Any) -> dict[str, Any]:
    assert self.db
    params = UpdateWorkflowRunStepParams(recid=recid, **kwargs)
    res = await self.db.run(update_workflow_run_step_request(params))
    return dict(res.rows[0])

  @staticmethod
  def _decode_json(raw: str | None) -> dict[str, Any] | list[Any] | None:
    if not raw:
      return None
    if isinstance(raw, (dict, list)):
      return raw
    try:
      return json.loads(raw)
    except json.JSONDecodeError:
      return None

  def _map_run(self, row: dict[str, Any]) -> dict[str, Any]:
    return {
      "recid": row.get("recid"),
      "guid": row.get("element_guid"),
      "workflows_guid": row.get("workflows_guid"),
      "status": row.get("element_status"),
      "payload": self._decode_json(row.get("element_payload")) or {},
      "context": self._decode_json(row.get("element_context")) or {},
      "current_step": row.get("element_current_step"),
      "step_index": row.get("element_step_index"),
      "error": row.get("element_error"),
      "source_type": row.get("element_source_type"),
      "source_id": row.get("element_source_id"),
      "created_by": row.get("element_created_by"),
      "started_on": row.get("element_started_on"),
      "ended_on": row.get("element_ended_on"),
      "timeout_at": row.get("element_timeout_at"),
      "created_on": row.get("element_created_on"),
      "modified_on": row.get("element_modified_on"),
    }

  @staticmethod
  def _load_step_instance(class_path: str) -> WorkflowStep:
    if not class_path or "." not in class_path:
      raise ValueError(f"Invalid workflow step class path: {class_path}")
    module_path, class_name = class_path.rsplit(".", 1)
    module = importlib.import_module(module_path)
    cls = getattr(module, class_name)
    instance = cls()
    if not isinstance(instance, WorkflowStep):
      raise TypeError(f"Workflow step '{class_path}' is not a WorkflowStep")
    return instance
