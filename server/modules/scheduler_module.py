from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import FastAPI

from queryregistry.system.config import get_config_request
from queryregistry.system.config.models import ConfigKeyParams
from queryregistry.system.scheduled_tasks import (
  create_scheduled_task_history_request,
  get_task_request,
  get_workflow_name_by_guid_request,
  list_all_tasks_request,
  list_enabled_due_tasks_request,
  list_task_history_request,
  update_scheduled_task_request,
)
from queryregistry.system.scheduled_tasks.models import (
  CreateScheduledTaskHistoryParams,
  GetTaskParams,
  GetWorkflowNameByGuidParams,
  ListAllTasksParams,
  ListEnabledDueTasksParams,
  ListTaskHistoryParams,
  UpdateScheduledTaskParams,
)

from . import BaseModule
from .db_module import DbModule
from .workflow_module import WorkflowModule

SCHEDULED_TASK_STATUS_DISABLED = 0
SCHEDULED_TASK_STATUS_ENABLED = 1


class SchedulerModule(BaseModule):
  def __init__(self, app: FastAPI):
    super().__init__(app)
    self.db: DbModule | None = None
    self.workflow: WorkflowModule | None = None
    self._task: asyncio.Task | None = None

  async def startup(self):
    self.db = self.app.state.db
    self.workflow = self.app.state.workflow
    await self.db.on_ready()
    await self.workflow.on_ready()
    self.app.state.scheduler = self
    await self._initialize_next_runs()
    self._task = asyncio.create_task(self._scheduler_loop())
    logging.debug("[SchedulerModule] loaded")
    self.mark_ready()

  async def shutdown(self):
    if self._task and not self._task.done():
      self._task.cancel()
      try:
        await self._task
      except asyncio.CancelledError:
        pass
    self._task = None
    self.db = None
    self.workflow = None

  async def _initialize_next_runs(self):
    assert self.db
    future_cutoff = (datetime.now(timezone.utc) + timedelta(days=3650)).isoformat()
    res = await self.db.run(
      list_enabled_due_tasks_request(ListEnabledDueTasksParams(now=future_cutoff))
    )
    for row in res.rows:
      task = dict(row)
      if task.get("element_next_run") is not None:
        continue
      now = datetime.now(timezone.utc)
      next_run = self._compute_next_run(str(task.get("element_cron") or ""), now)
      await self.db.run(
        update_scheduled_task_request(
          UpdateScheduledTaskParams(
            recid=int(task["recid"]),
            next_run=next_run.isoformat() if next_run else None,
            total_runs=None,
            last_run=None,
            status=None,
          )
        )
      )

  async def _scheduler_loop(self):
    while True:
      interval_seconds = await self._get_poll_interval_seconds()
      try:
        await self._tick()
      except asyncio.CancelledError:
        raise
      except Exception:
        logging.exception("[SchedulerModule] scheduler loop error")
      await asyncio.sleep(max(interval_seconds, 1))

  async def _tick(self):
    assert self.db
    assert self.workflow

    now = datetime.now(timezone.utc)
    res = await self.db.run(
      list_enabled_due_tasks_request(ListEnabledDueTasksParams(now=now.isoformat()))
    )
    due_tasks = [dict(row) for row in res.rows]
    due_tasks.sort(key=lambda row: row.get("element_next_run") or "")

    for task in due_tasks:
      await self._process_task(task, now)

  async def _process_task(self, task: dict[str, Any], now: datetime):
    assert self.db
    assert self.workflow

    recid = int(task["recid"])
    run_count_limit = task.get("element_run_count_limit")
    total_runs = int(task.get("element_total_runs") or 0)
    run_until = self._parse_utc(task.get("element_run_until"))

    if run_count_limit is not None and total_runs >= int(run_count_limit):
      await self._disable_task(recid, "run_count_limit reached")
      return

    if run_until and now > run_until:
      await self._disable_task(recid, "run_until expired")
      return

    payload = self._resolve_payload_template(task, now)
    workflow_name = await self._get_workflow_name(str(task.get("workflows_guid") or ""))

    run_recid: int | None = None
    error: str | None = None
    try:
      submitted = await self.workflow.submit(
        workflow_name=workflow_name,
        payload=payload,
        trigger_type_code=1,
        trigger_ref=str(recid),
      )
      run_recid = int(submitted.get("recid")) if submitted.get("recid") is not None else None
    except Exception as exc:
      logging.exception("[SchedulerModule] failed to submit scheduled task %s", recid)
      error = str(exc)

    await self.db.run(
      create_scheduled_task_history_request(
        CreateScheduledTaskHistoryParams(
          tasks_recid=recid,
          runs_recid=run_recid,
          error=error,
        )
      )
    )

    next_run = self._compute_next_run(str(task.get("element_cron") or ""), now)
    while next_run and next_run <= now:
      next_run = self._compute_next_run(str(task.get("element_cron") or ""), next_run)

    await self.db.run(
      update_scheduled_task_request(
        UpdateScheduledTaskParams(
          recid=recid,
          total_runs=total_runs + 1,
          last_run=now.isoformat(),
          next_run=next_run.isoformat() if next_run else None,
          status=None,
        )
      )
    )

  async def _disable_task(self, recid: int, reason: str):
    assert self.db
    logging.info("[SchedulerModule] disabling task %s: %s", recid, reason)
    await self.db.run(
      update_scheduled_task_request(
        UpdateScheduledTaskParams(
          recid=recid,
          status=SCHEDULED_TASK_STATUS_DISABLED,
          total_runs=None,
          last_run=None,
          next_run=None,
        )
      )
    )

  async def list_tasks(self) -> list[dict[str, Any]]:
    """List all scheduled tasks."""
    assert self.db
    res = await self.db.run(list_all_tasks_request(ListAllTasksParams()))
    return [dict(row) for row in res.rows]

  async def get_task(self, recid: int) -> dict[str, Any] | None:
    """Get a single scheduled task by recid."""
    assert self.db
    res = await self.db.run(get_task_request(GetTaskParams(recid=recid)))
    if not res.rows:
      return None
    return dict(res.rows[0])

  async def list_task_history(self, tasks_recid: int) -> list[dict[str, Any]]:
    """List history entries for a scheduled task."""
    assert self.db
    res = await self.db.run(
      list_task_history_request(ListTaskHistoryParams(tasks_recid=tasks_recid))
    )
    return [dict(row) for row in res.rows]

  async def get_task_workflow_name(self, recid: int) -> str | None:
    """Get the workflow name for a scheduled task."""
    task = await self.get_task(recid)
    if not task:
      return None
    return await self._get_workflow_name(str(task.get("workflows_guid") or ""))

  async def _get_workflow_name(self, workflow_guid: str) -> str:
    assert self.db
    res = await self.db.run(
      get_workflow_name_by_guid_request(GetWorkflowNameByGuidParams(guid=workflow_guid))
    )
    row = dict(res.rows[0]) if res.rows else {}
    return str(row.get("element_name") or "")

  async def _get_poll_interval_seconds(self) -> int:
    assert self.db
    res = await self.db.run(get_config_request(ConfigKeyParams(key="SchedulerPollIntervalSeconds")))
    row = dict(res.rows[0]) if res.rows else {}
    value = row.get("element_value")
    try:
      return int(value)
    except (TypeError, ValueError):
      return 60

  def _resolve_payload_template(self, task: dict[str, Any], now: datetime) -> dict[str, Any]:
    template = str(task.get("element_payload_template") or "{}")
    replacements = {
      "{{now}}": now.isoformat(),
      "{{last_run}}": str(task.get("element_last_run") or ""),
      "{{task_name}}": str(task.get("element_name") or ""),
      "{{run_count}}": str(task.get("element_total_runs") or 0),
    }
    for key, value in replacements.items():
      template = template.replace(key, value)
    try:
      parsed = json.loads(template)
      return parsed if isinstance(parsed, dict) else {"value": parsed}
    except json.JSONDecodeError:
      logging.exception("[SchedulerModule] invalid payload template for task %s", task.get("recid"))
      return {}

  @staticmethod
  def _parse_utc(value: str | None) -> datetime | None:
    if not value:
      return None
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
      return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)

  @staticmethod
  def _field_match(field: str, value: int) -> bool:
    if field == "*":
      return True
    if field.startswith("*/"):
      step = int(field[2:])
      return step > 0 and value % step == 0
    return value == int(field)

  def _compute_next_run(self, cron_expr: str, after: datetime) -> datetime | None:
    if not cron_expr:
      return None

    parts = cron_expr.split()
    if len(parts) != 5:
      logging.error("[SchedulerModule] Invalid cron expression: %s", cron_expr)
      return None

    minute_field, hour_field, dom_field, month_field, dow_field = parts
    cursor = after.astimezone(timezone.utc).replace(second=0, microsecond=0) + timedelta(minutes=1)

    for _ in range(400000):
      day_of_week = (cursor.weekday() + 1) % 7
      if (
        self._field_match(minute_field, cursor.minute)
        and self._field_match(hour_field, cursor.hour)
        and self._field_match(dom_field, cursor.day)
        and self._field_match(month_field, cursor.month)
        and self._field_match(dow_field, day_of_week)
      ):
        return cursor
      cursor += timedelta(minutes=1)

    return None
