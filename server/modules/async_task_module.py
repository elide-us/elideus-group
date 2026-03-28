from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import UUID

from fastapi import FastAPI, HTTPException

from queryregistry.system.async_tasks import (
  create_task_event_request,
  create_task_request,
  get_task_request,
  list_task_events_request,
  list_tasks_request,
  update_task_request,
)
from queryregistry.system.async_tasks.models import (
  CreateTaskEventParams,
  CreateTaskParams,
  GetTaskParams,
  ListTaskEventsParams,
  ListTasksParams,
  UpdateTaskParams,
)

from . import BaseModule
from .async_task_handlers import CallbackHandler, PipelineHandler
from .db_module import DbModule


STATUS_QUEUED = 0
STATUS_RUNNING = 1
STATUS_POLLING = 2
STATUS_WAITING_CALLBACK = 3
STATUS_COMPLETED = 4
STATUS_FAILED = 5
STATUS_CANCELLED = 6
STATUS_TIMED_OUT = 7

ACTIVE_STATUSES = {STATUS_QUEUED, STATUS_RUNNING, STATUS_POLLING, STATUS_WAITING_CALLBACK}


class AsyncTaskModule(BaseModule):
  def __init__(self, app: FastAPI):
    super().__init__(app)
    self.db: DbModule | None = None
    self.handlers: dict[str, Any] = {}
    self.tick_interval_seconds = 10
    self._loop_task: asyncio.Task | None = None
    self._loop_lock = asyncio.Lock()

  async def startup(self):
    self.db = self.app.state.db
    await self.db.on_ready()
    self.app.state.async_task = self
    self._loop_task = asyncio.create_task(self._tick_loop())

    finance = getattr(self.app.state, "finance", None)
    if finance is not None:
      await finance.on_ready()
      from server.jobs.billing_import_pipeline import BillingImportPipelineHandler

      self.register_handler("finance.billing.import_pipeline", BillingImportPipelineHandler())

    openai = getattr(self.app.state, "openai", None)
    if openai is not None:
      await openai.on_ready()
      from server.jobs.persona_conversation_pipeline import PersonaConversationPipelineHandler

      self.register_handler("discord.chat.persona_pipeline", PersonaConversationPipelineHandler())

    logging.debug("[AsyncTaskModule] loaded")
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
    logging.info("[AsyncTaskModule] shutdown")

  def register_handler(self, name: str, handler: Any):
    if not name:
      raise ValueError("handler name is required")
    self.handlers[name] = handler

  async def submit_task(
    self,
    handler_name: str,
    payload: dict[str, Any],
    source_type: str | None,
    source_id: str | None,
    created_by: str | None,
    timeout_seconds: int | None,
    poll_interval_seconds: int | None,
    max_retries: int = 0,
  ) -> dict[str, Any]:
    assert self.db
    handler = self._get_handler(handler_name)
    validated_payload = self._validate_payload(handler, payload)
    now = datetime.now(timezone.utc)
    timeout_at = now + timedelta(seconds=timeout_seconds) if timeout_seconds else None
    params = CreateTaskParams(
      handler_type=handler.handler_type,
      handler_name=handler_name,
      payload=json.dumps(validated_payload),
      status=STATUS_QUEUED,
      max_retries=max_retries,
      poll_interval_seconds=poll_interval_seconds,
      timeout_seconds=timeout_seconds,
      timeout_at=timeout_at.isoformat() if timeout_at else None,
      source_type=source_type,
      source_id=source_id,
      created_by=self._normalize_uuid(created_by),
    )
    created = await self.db.run(create_task_request(params))
    task = self._map_task(dict(created.rows[0]))
    await self._add_event(task["recid"], "created", detail={"status": STATUS_QUEUED})
    return task

  async def get_task(self, guid: str) -> dict[str, Any] | None:
    assert self.db
    res = await self.db.run(get_task_request(GetTaskParams(guid=guid)))
    if not res.rows:
      return None
    return self._map_task(dict(res.rows[0]))

  async def list_tasks(
    self,
    status: int | None = None,
    handler_type: str | None = None,
    handler_name: str | None = None,
  ) -> list[dict[str, Any]]:
    assert self.db
    params = ListTasksParams(status=status, handler_type=handler_type, handler_name=handler_name)
    res = await self.db.run(list_tasks_request(params))
    return [self._map_task(dict(row)) for row in res.rows]

  async def list_task_events(self, guid: str) -> list[dict[str, Any]]:
    assert self.db
    task = await self.get_task(guid)
    if not task:
      raise HTTPException(status_code=404, detail="Task not found")
    res = await self.db.run(list_task_events_request(ListTaskEventsParams(tasks_recid=task["recid"])))
    return [dict(row) for row in res.rows]

  async def cancel_task(self, guid: str) -> dict[str, Any]:
    task = await self.get_task_or_404(guid)
    if task["status"] in {STATUS_COMPLETED, STATUS_CANCELLED, STATUS_TIMED_OUT}:
      return task
    updated = await self._update_task(task["recid"], status=STATUS_CANCELLED)
    await self._add_event(task["recid"], "cancelled")
    return updated

  async def resolve_callback(self, guid: str, result: dict[str, Any]) -> dict[str, Any]:
    task = await self.get_task_or_404(guid)
    if task["status"] != STATUS_WAITING_CALLBACK:
      raise HTTPException(status_code=400, detail="Task is not waiting for callback")
    handler = self._get_handler(task["handler_name"])
    if not isinstance(handler, CallbackHandler):
      raise HTTPException(status_code=400, detail="Handler is not callback type")
    payload = task["payload"] or {}
    callback_result = await handler.on_callback(self.app, payload, result)
    await self._add_event(task["recid"], "callback_received", detail=result)
    return await self._finalize_from_handler_result(task, callback_result)

  async def retry_task(self, guid: str) -> dict[str, Any]:
    task = await self.get_task_or_404(guid)
    if task["status"] != STATUS_FAILED:
      raise HTTPException(status_code=400, detail="Only failed tasks can be retried")
    handler = self._get_handler(task["handler_name"])
    if not isinstance(handler, PipelineHandler):
      raise HTTPException(status_code=400, detail="Only pipeline tasks can be retried")
    if task["retry_count"] >= task["max_retries"]:
      raise HTTPException(status_code=400, detail="Retry limit exceeded")
    updated = await self._update_task(
      task["recid"],
      status=STATUS_RUNNING,
      retry_count=task["retry_count"] + 1,
      error=None,
    )
    await self._add_event(task["recid"], "retried", detail={"retry_count": updated["retry_count"]})
    return updated

  async def get_task_or_404(self, guid: str) -> dict[str, Any]:
    task = await self.get_task(guid)
    if not task:
      raise HTTPException(status_code=404, detail="Task not found")
    return task

  async def _tick_loop(self):
    while True:
      try:
        await self.tick_once()
      except asyncio.CancelledError:
        raise
      except Exception as exc:
        logging.exception("[AsyncTaskModule] Tick error: %s", exc)
      await asyncio.sleep(self.tick_interval_seconds)

  async def tick_once(self):
    async with self._loop_lock:
      tasks = await self.list_tasks()
      now = datetime.now(timezone.utc)
      for task in tasks:
        if task["status"] not in ACTIVE_STATUSES:
          continue
        if self._is_timed_out(task, now):
          await self._timeout_task(task)
          continue
        if task["status"] == STATUS_QUEUED:
          await self._start_task(task)
        elif task["status"] == STATUS_POLLING:
          await self._process_poll_task(task, now)
        elif task["status"] == STATUS_RUNNING:
          await self._process_pipeline_task(task)

  async def _start_task(self, task: dict[str, Any]):
    handler = self._get_handler(task["handler_name"])
    payload = task["payload"] or {}
    if handler.handler_type == "poll":
      start_result = await handler.start(self.app, payload)
      interval = start_result.get("poll_interval")
      if interval is None:
        interval = task.get("poll_interval_seconds")
      updated = await self._update_task(
        task["recid"],
        status=STATUS_POLLING,
        external_id=start_result.get("external_id"),
        poll_interval_seconds=interval,
      )
      await self._add_event(task["recid"], "started", detail={"external_id": updated.get("external_id")})
      return
    if handler.handler_type == "callback":
      await handler.start(self.app, payload)
      await self._update_task(task["recid"], status=STATUS_WAITING_CALLBACK)
      await self._add_event(task["recid"], "started")
      return
    if handler.handler_type == "pipeline":
      await self._update_task(task["recid"], status=STATUS_RUNNING)
      await self._add_event(task["recid"], "started")
      return
    raise ValueError(f"Unsupported handler type '{handler.handler_type}'")

  async def _process_poll_task(self, task: dict[str, Any], now: datetime):
    poll_interval = task.get("poll_interval_seconds")
    interval = int(poll_interval if poll_interval is not None else 10)
    modified_on = self._parse_utc(task.get("modified_on"))
    if modified_on and now < modified_on + timedelta(seconds=interval):
      return
    handler = self._get_handler(task["handler_name"])
    payload = task["payload"] or {}
    poll_result = await handler.check(self.app, task.get("external_id") or "", payload)
    await self._add_event(task["recid"], "poll_check", detail=poll_result)
    await self._finalize_from_handler_result(task, poll_result)

  async def _process_pipeline_task(self, task: dict[str, Any]):
    handler = self._get_handler(task["handler_name"])
    if not isinstance(handler, PipelineHandler):
      return
    payload = task["payload"] or {}
    current_index = int(task.get("step_index") or 0)
    context = task["result"] or {}
    if current_index >= len(handler.steps):
      await self._update_task(task["recid"], status=STATUS_COMPLETED)
      await self._add_event(task["recid"], "completed", detail=context)
      return
    step_name, step_callable = handler.steps[current_index]
    await self._update_task(task["recid"], current_step=step_name)
    await self._add_event(task["recid"], "step_started", step_name=step_name)
    try:
      step_result = await step_callable(self.app, payload, context)
    except Exception as exc:
      await self._update_task(
        task["recid"],
        status=STATUS_FAILED,
        current_step=step_name,
        error=str(exc),
      )
      await self._add_event(task["recid"], "step_failed", step_name=step_name, detail={"error": str(exc)})
      return

    merged_context = dict(context)
    merged_context.update(step_result or {})
    next_index = current_index + 1
    status = STATUS_COMPLETED if next_index >= len(handler.steps) else STATUS_RUNNING
    await self._update_task(
      task["recid"],
      status=status,
      current_step=step_name,
      step_index=next_index,
      result=merged_context,
    )
    await self._add_event(task["recid"], "step_completed", step_name=step_name, detail=step_result)
    if status == STATUS_COMPLETED:
      await self._add_event(task["recid"], "completed", detail=merged_context)

  async def _finalize_from_handler_result(self, task: dict[str, Any], handler_result: dict[str, Any]):
    complete = bool(handler_result.get("complete"))
    error = handler_result.get("error")
    if error:
      updated = await self._update_task(task["recid"], status=STATUS_FAILED, error=str(error))
      await self._add_event(task["recid"], "failed", detail={"error": str(error)})
      return updated
    if complete:
      updated = await self._update_task(task["recid"], status=STATUS_COMPLETED, result=handler_result.get("result"))
      await self._add_event(task["recid"], "completed", detail=handler_result.get("result"))
      return updated
    return await self.get_task(task["guid"])

  async def _timeout_task(self, task: dict[str, Any]):
    await self._update_task(task["recid"], status=STATUS_TIMED_OUT, error="Task timed out")
    await self._add_event(task["recid"], "timed_out")

  async def _update_task(self, recid: int, **changes: Any) -> dict[str, Any]:
    assert self.db
    params = UpdateTaskParams(recid=recid, **changes)
    res = await self.db.run(update_task_request(params))
    return self._map_task(dict(res.rows[0]))

  async def _add_event(self, tasks_recid: int, event_type: str, step_name: str | None = None, detail: Any = None):
    assert self.db
    detail_json = None if detail is None else json.dumps(detail)
    await self.db.run(
      create_task_event_request(
        CreateTaskEventParams(
          tasks_recid=tasks_recid,
          event_type=event_type,
          step_name=step_name,
          detail=detail_json,
        )
      )
    )

  def _is_timed_out(self, task: dict[str, Any], now: datetime) -> bool:
    timeout_at = self._parse_utc(task.get("timeout_at"))
    return bool(timeout_at and now >= timeout_at)

  def _get_handler(self, handler_name: str):
    handler = self.handlers.get(handler_name)
    if not handler:
      raise HTTPException(status_code=400, detail=f"Unknown task handler '{handler_name}'")
    return handler

  @staticmethod
  def _parse_utc(value: str | None) -> datetime | None:
    if not value:
      return None
    dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if dt.tzinfo is None:
      return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)

  @staticmethod
  def _normalize_uuid(value: str | None) -> str | None:
    if not value:
      return None
    return str(UUID(value))

  @staticmethod
  def _loads_json(value: str | None):
    if value is None:
      return None
    if isinstance(value, (dict, list)):
      return value
    if value == "":
      return None
    return json.loads(value)

  def _validate_payload(self, handler: Any, payload: dict[str, Any]) -> dict[str, Any]:
    model = getattr(handler, "payload_model", None)
    if model is None:
      return payload
    validated = model.model_validate(payload)
    return validated.model_dump()

  def _map_task(self, row: dict[str, Any]) -> dict[str, Any]:
    return {
      "recid": row.get("recid"),
      "guid": row.get("element_guid"),
      "handler_type": row.get("element_handler_type"),
      "handler_name": row.get("element_handler_name"),
      "payload": self._loads_json(row.get("element_payload")),
      "status": row.get("element_status"),
      "result": self._loads_json(row.get("element_result")),
      "error": row.get("element_error"),
      "current_step": row.get("element_current_step"),
      "step_index": row.get("element_step_index"),
      "max_retries": row.get("element_max_retries"),
      "retry_count": row.get("element_retry_count"),
      "poll_interval_seconds": row.get("element_poll_interval_seconds"),
      "timeout_seconds": row.get("element_timeout_seconds"),
      "timeout_at": row.get("element_timeout_at"),
      "external_id": row.get("element_external_id"),
      "source_type": row.get("element_source_type"),
      "source_id": row.get("element_source_id"),
      "created_by": row.get("element_created_by"),
      "created_on": row.get("element_created_on"),
      "modified_on": row.get("element_modified_on"),
    }
