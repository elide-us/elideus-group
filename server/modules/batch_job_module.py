from __future__ import annotations

import asyncio
import importlib
import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import FastAPI

from . import BaseModule
from .db_module import DbModule
from queryregistry.system.batch_jobs import (
  create_history_request,
  delete_job_request,
  get_job_request,
  list_history_request,
  list_jobs_request,
  update_history_request,
  update_job_status_request,
  upsert_job_request,
)
from queryregistry.system.batch_jobs.models import (
  CreateHistoryParams,
  DeleteJobParams,
  GetJobParams,
  ListHistoryParams,
  ListJobsParams,
  UpdateHistoryParams,
  UpdateJobStatusParams,
  UpsertJobParams,
)


class BatchJobModule(BaseModule):
  def __init__(self, app: FastAPI):
    super().__init__(app)
    self.db: DbModule | None = None
    self._scheduler_task: asyncio.Task | None = None

  async def startup(self):
    self.db = self.app.state.db
    await self.db.on_ready()
    self.app.state.batch_job = self
    self._scheduler_task = asyncio.create_task(self._scheduler_loop())
    logging.debug("[BatchJobModule] loaded")
    self.mark_ready()

  async def shutdown(self):
    if self._scheduler_task and not self._scheduler_task.done():
      self._scheduler_task.cancel()
      try:
        await self._scheduler_task
      except asyncio.CancelledError:
        pass
    self._scheduler_task = None
    self.db = None
    logging.info("[BatchJobModule] shutdown")

  def _map_job(self, row: dict[str, Any]) -> dict[str, Any]:
    return {
      "recid": row.get("recid"),
      "name": row.get("element_name"),
      "description": row.get("element_description"),
      "class_path": row.get("element_class"),
      "parameters": row.get("element_parameters"),
      "cron": row.get("element_cron"),
      "recurrence_type": row.get("element_recurrence_type"),
      "run_count_limit": row.get("element_run_count_limit"),
      "run_until": row.get("element_run_until"),
      "total_runs": row.get("element_total_runs"),
      "is_enabled": row.get("element_is_enabled"),
      "last_run": row.get("element_last_run"),
      "next_run": row.get("element_next_run"),
      "status": row.get("element_status"),
    }

  def _map_history(self, row: dict[str, Any]) -> dict[str, Any]:
    return {
      "recid": row.get("recid"),
      "jobs_recid": row.get("jobs_recid"),
      "started_on": row.get("element_started_on"),
      "ended_on": row.get("element_ended_on"),
      "status": row.get("element_status"),
      "error": row.get("element_error"),
      "result": row.get("element_result"),
    }

  async def list_jobs(self) -> list[dict[str, Any]]:
    assert self.db
    res = await self.db.run(list_jobs_request(ListJobsParams()))
    return [self._map_job(dict(row)) for row in res.rows]

  async def get_job(self, recid: int) -> dict[str, Any] | None:
    assert self.db
    res = await self.db.run(get_job_request(GetJobParams(recid=recid)))
    if not res.rows:
      return None
    return self._map_job(dict(res.rows[0]))

  async def upsert_job(self, data: dict[str, Any]) -> dict[str, Any]:
    assert self.db
    params = UpsertJobParams(**data)
    res = await self.db.run(upsert_job_request(params))
    row = dict(res.rows[0]) if res.rows else params.model_dump()
    return self._map_job(row)

  async def delete_job(self, recid: int) -> dict[str, Any]:
    assert self.db
    await self.db.run(delete_job_request(DeleteJobParams(recid=recid)))
    return {"recid": recid}

  async def list_history(self, jobs_recid: int) -> list[dict[str, Any]]:
    assert self.db
    res = await self.db.run(list_history_request(ListHistoryParams(jobs_recid=jobs_recid)))
    return [self._map_history(dict(row)) for row in res.rows]

  async def run_now(self, recid: int) -> dict[str, Any]:
    """Trigger a job immediately regardless of schedule."""
    assert self.db
    res = await self.db.run(get_job_request(GetJobParams(recid=recid)))
    if not res.rows:
      raise ValueError(f"Batch job {recid} not found")
    await self._execute_job(dict(res.rows[0]))
    updated = await self.get_job(recid)
    if not updated:
      raise ValueError(f"Batch job {recid} not found after execution")
    return updated

  @staticmethod
  def _parse_utc(value: str | None) -> datetime | None:
    if not value:
      return None
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
      return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)

  def _compute_next_run_for_job(self, job: dict[str, Any], after: datetime) -> datetime | None:
    recurrence_type = int(job.get("element_recurrence_type") or 0)
    total_runs = int(job.get("element_total_runs") or 0)
    run_count_limit = job.get("element_run_count_limit")
    run_until = self._parse_utc(job.get("element_run_until"))

    if recurrence_type == 0 and total_runs >= 1:
      return None

    if recurrence_type == 2 and run_count_limit is not None and total_runs >= int(run_count_limit):
      return None

    next_run = self._compute_next_run(job.get("element_cron") or "", after)
    if not next_run:
      return None

    if recurrence_type == 3 and run_until and next_run > run_until:
      return None

    return next_run

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
      logging.error("[BatchJobModule] Invalid cron expression: %s", cron_expr)
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

  async def _scheduler_loop(self) -> None:
    while True:
      await asyncio.sleep(30)
      try:
        now = datetime.now(timezone.utc)
        assert self.db
        jobs_res = await self.db.run(list_jobs_request(ListJobsParams()))
        for row in jobs_res.rows:
          job = dict(row)
          if not job.get("element_is_enabled"):
            continue
          job_status = int(job.get("element_status") or 0)
          if job_status in (1, 6):  # Skip Running and Paused
            continue

          next_run = self._parse_utc(job.get("element_next_run"))
          if next_run is None:
            computed = self._compute_next_run_for_job(job, now)
            await self.db.run(
              update_job_status_request(
                UpdateJobStatusParams(
                  recid=int(job["recid"]),
                  status=int(job.get("element_status") or 0),
                  next_run=computed.isoformat() if computed else None,
                )
              )
            )
            next_run = computed

          if next_run and next_run <= now:
            await self._execute_job(job)
      except asyncio.CancelledError:
        raise
      except Exception:
        logging.exception("[BatchJobModule] Scheduler tick failed")

  async def _execute_job(self, job: dict[str, Any]) -> None:
    assert self.db
    recid = int(job["recid"])
    now = datetime.now(timezone.utc)
    run_status = 2

    await self.db.run(
      update_job_status_request(
        UpdateJobStatusParams(
          recid=recid,
          status=1,
        )
      )
    )

    history_res = await self.db.run(create_history_request(CreateHistoryParams(jobs_recid=recid)))
    history_row = dict(history_res.rows[0]) if history_res.rows else {}
    history_recid = int(history_row.get("recid", 0))

    try:
      class_path = str(job.get("element_class") or "")
      if not class_path or "." not in class_path:
        raise ValueError(f"Invalid class path for job {recid}: {class_path}")

      module_path, callable_name = class_path.rsplit(".", 1)
      module = importlib.import_module(module_path)
      target = getattr(module, callable_name)

      params_raw = job.get("element_parameters")
      params = json.loads(params_raw) if params_raw else {}
      if not isinstance(params, dict):
        raise ValueError("Job parameters must decode to an object")

      result = await target(self.app, params)
      await self.db.run(
        update_history_request(
          UpdateHistoryParams(
            recid=history_recid,
            status=2,
            result=json.dumps(result),
          )
        )
      )
    except Exception as exc:
      run_status = 3
      logging.exception("[BatchJobModule] Job %s execution failed", recid)
      await self.db.run(
        update_history_request(
          UpdateHistoryParams(
            recid=history_recid,
            status=3,
            error=str(exc),
          )
        )
      )

    total_runs = int(job.get("element_total_runs") or 0) + 1
    run_until = self._parse_utc(job.get("element_run_until"))
    next_run = self._compute_next_run_for_job(
      {
        **job,
        "element_total_runs": total_runs,
        "element_run_until": run_until.isoformat() if run_until else None,
      },
      now,
    )
    final_status = 5 if next_run is None else run_status

    await self.db.run(
      update_job_status_request(
        UpdateJobStatusParams(
          recid=recid,
          status=final_status,
          total_runs=total_runs,
          last_run=now.isoformat(),
          next_run=next_run.isoformat() if next_run else None,
        )
      )
    )
