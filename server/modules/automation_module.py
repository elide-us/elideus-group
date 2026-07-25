"""Automation runner — the workflow executor and scheduler.

The automation SCHEMA has been in this database since v0.11.1.0/v0.11.4.0
(system_workflows, _workflow_actions, _workflow_runs, _workflow_run_actions,
system_scheduled_tasks, plus the status/disposition/trigger lookups). What was
missing was the process that turns those rows into work. This is that process.

Spec: pagespec/system/SystemAutomationPages.md and
pagespec/system/SystemAutomationTasks.md, both recoverable verbatim from tag
mem-unify-01/pre-doc-deletion. This module implements the EXECUTION half —
scheduler tick, run execution, stall detection. The management/RPC surface the
spec also describes (workflow designer, run controls, the two history pages,
task CRUD) is deliberately not built here; it is operator UI, not execution.

## How an action becomes a call
system_workflow_actions.functions_recid is a NOT NULL FK to
reflection_rpc_functions, and that row carries element_module_attr +
element_method_name. So an action resolves to
``getattr(app.state, module_attr).method_name(**payload)`` — the same
binding shape the MCP gateway uses. An action cannot call a bare module method;
it must go through a registered RPC function. No codegen is involved in
dispatch.

## What this module does NOT do
Rollback (disposition 'reversible' + element_rollback_functions_recid) is
recorded in the schema but not executed here. A half-built rollback is worse
than none: it would report success having undone part of a chain. Runs that
fail are left in 'failed' (status 3, allows_retry) for an operator, which is
what the spec's retryWorkflowRunAction/rollbackWorkflowRun controls are for.

Concurrency is enforced per workflow via element_max_concurrency. There is no
cross-process claim protocol — this is a single-instance app on a single-user
test system. If it is ever run multi-instance, run claiming needs to become an
atomic UPDATE..OUTPUT rather than the read-then-write used here; that is called
out at the claim site.
"""

from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime, timezone
from os import getenv
from typing import Any

from fastapi import FastAPI
from queryregistry.providers.mssql import run_exec, run_json_many, run_json_one

from . import BaseModule
from .db_module import DbModule
from ..helpers.cron import CronError, next_run

# system_automation_statuses
ST_PENDING, ST_RUNNING, ST_COMPLETED, ST_FAILED = 0, 1, 2, 3
ST_CANCELLED, ST_WAITING, ST_STALLED = 4, 5, 10
TERMINAL_STATUSES = (ST_COMPLETED, ST_CANCELLED)

# system_trigger_types / system_scheduled_task_statuses / system_workflow_statuses
TRIGGER_MANUAL, TRIGGER_SCHEDULE = 0, 1
TASK_ENABLED = 1
WORKFLOW_PUBLISHED = 1

DEFAULT_TICK_SECONDS = 60
DEFAULT_STALL_SECONDS = 3600


class AutomationModule(BaseModule):
  def __init__(self, app: FastAPI):
    super().__init__(app)
    self.db: DbModule | None = None
    self._task: asyncio.Task | None = None
    self._tick_seconds = int(getenv('AUTOMATION_TICK_SECONDS', DEFAULT_TICK_SECONDS))
    self._enabled = getenv('AUTOMATION_ENABLED', '1') not in ('0', 'false', 'False')

  async def startup(self):
    self.db = self.app.state.db
    await self.db.on_ready()
    self.mark_ready()
    if self._enabled:
      self._task = asyncio.create_task(self._scheduler_loop(), name='automation-scheduler')
      logging.info('[AutomationModule] scheduler started, tick=%ss', self._tick_seconds)
    else:
      logging.info('[AutomationModule] scheduler DISABLED (AUTOMATION_ENABLED=0)')

  async def shutdown(self):
    if self._task:
      self._task.cancel()
      try:
        await self._task
      except asyncio.CancelledError:
        pass
      self._task = None
    self.db = None

  # ── Loop ────────────────────────────────────────────────────────────────

  async def _scheduler_loop(self):
    """Tick forever. A failing tick must never kill the loop — it logs and
    retries next interval, because a scheduler that dies silently on one bad
    row stops every scheduled job in the system with no signal."""
    while True:
      try:
        await asyncio.sleep(self._tick_seconds)
        await self.tick()
      except asyncio.CancelledError:
        raise
      except Exception:
        logging.exception('[AutomationModule] tick failed; continuing')

  async def tick(self) -> dict[str, Any]:
    """One scheduler pass: promote due tasks, execute pending runs, flag stalls."""
    submitted = await self._promote_due_tasks()
    executed = await self._drain_pending_runs()
    stalled = await self.scan_stalls()
    if submitted or executed or stalled:
      logging.info('[AutomationModule] tick submitted=%d executed=%d stalled=%d',
                   submitted, executed, stalled)
    return {'submitted': submitted, 'executed': executed, 'stalled': stalled}

  # ── Scheduled tasks ─────────────────────────────────────────────────────

  async def _promote_due_tasks(self) -> int:
    """Submit a run for every enabled task whose next_run has passed.

    element_next_run is precomputed and stored, so the hot path is an indexed
    comparison rather than evaluating cron for every task every tick. A task
    with next_run NULL (never scheduled) is initialised from its cron here.
    """
    result = await run_json_many("""
SELECT t.recid, t.element_name, t.element_cron, t.element_next_run, t.element_payload_template,
       t.element_total_runs, t.element_run_count_limit, t.element_run_until,
       w.element_name AS workflow_name
FROM dbo.system_scheduled_tasks t
JOIN dbo.system_workflows w ON w.element_guid = t.workflows_guid
WHERE t.element_status = ?
  AND (t.element_next_run IS NULL OR t.element_next_run <= SYSUTCDATETIME())
FOR JSON PATH, INCLUDE_NULL_VALUES;
""", (TASK_ENABLED,))
    tasks = list(result.rows) if result and getattr(result, 'rows', None) else []

    now = datetime.now(timezone.utc)
    submitted = 0
    for t in tasks:
      name = t.get('element_name')
      cron = t.get('element_cron')
      try:
        upcoming = next_run(str(cron), now)
      except CronError:
        logging.error('[AutomationModule] task %r has an unusable cron %r; disabling', name, cron)
        await run_exec(
          'UPDATE dbo.system_scheduled_tasks SET element_status = 0, '
          'element_modified_on = SYSUTCDATETIME() WHERE recid = ?', (t.get('recid'),))
        continue

      # Exhausted by count or end date -> disable rather than fire forever.
      limit = t.get('element_run_count_limit')
      until = t.get('element_run_until')
      if (limit is not None and int(t.get('element_total_runs') or 0) >= int(limit)) or \
         (until is not None and str(until) < now.isoformat()):
        await run_exec(
          'UPDATE dbo.system_scheduled_tasks SET element_status = 0, '
          'element_modified_on = SYSUTCDATETIME() WHERE recid = ?', (t.get('recid'),))
        continue

      first_schedule = t.get('element_next_run') is None
      if not first_schedule:
        try:
          await self.submit_run(
            str(t.get('workflow_name')), t.get('element_payload_template'),
            TRIGGER_SCHEDULE, f'scheduled_task:{name}',
          )
          submitted += 1
        except Exception:
          logging.exception('[AutomationModule] failed to submit run for task %r', name)

      await run_exec("""
UPDATE dbo.system_scheduled_tasks
   SET element_next_run = TRY_CAST(? AS DATETIMEOFFSET(7)),
       element_last_run = CASE WHEN ? = 1 THEN element_last_run ELSE SYSUTCDATETIME() END,
       element_total_runs = element_total_runs + CASE WHEN ? = 1 THEN 0 ELSE 1 END,
       element_modified_on = SYSUTCDATETIME()
 WHERE recid = ?;
""", (upcoming.isoformat() if upcoming else None, int(first_schedule),
      int(first_schedule), t.get('recid')))
    return submitted

  # ── Runs ────────────────────────────────────────────────────────────────

  async def submit_run(self, workflow_name: str, payload: Any = None,
                       trigger_type: int = TRIGGER_MANUAL,
                       trigger_ref: str | None = None) -> dict[str, Any]:
    """Create a pending run for a published workflow. Returns {run_guid}."""
    await self.on_ready()
    wf = await run_json_one("""
SELECT TOP 1 element_guid, element_name, element_max_concurrency
FROM dbo.system_workflows
WHERE element_name = ? AND element_status = ? AND element_is_active = 1
FOR JSON PATH, WITHOUT_ARRAY_WRAPPER;
""", (workflow_name, WORKFLOW_PUBLISHED))
    rows = list(wf.rows) if wf and getattr(wf, 'rows', None) else []
    if not rows:
      raise ValueError(f'No published workflow named {workflow_name!r}.')
    workflow = rows[0]

    max_conc = workflow.get('element_max_concurrency')
    if max_conc:
      busy = await run_json_one("""
SELECT COUNT(*) AS busy FROM dbo.system_workflow_runs
WHERE workflows_guid = TRY_CAST(? AS UNIQUEIDENTIFIER) AND element_status IN (?, ?, ?)
FOR JSON PATH, WITHOUT_ARRAY_WRAPPER;
""", (workflow.get('element_guid'), ST_PENDING, ST_RUNNING, ST_WAITING))
      busy_rows = list(busy.rows) if busy and getattr(busy, 'rows', None) else []
      if busy_rows and int(busy_rows[0].get('busy') or 0) >= int(max_conc):
        logging.info('[AutomationModule] %r at max concurrency (%s); not submitting',
                     workflow_name, max_conc)
        return {'run_guid': None, 'skipped': 'max_concurrency'}

    payload_text = payload if isinstance(payload, str) or payload is None else json.dumps(payload)
    created = await run_json_one("""
SET NOCOUNT ON;
DECLARE @out TABLE (element_guid UNIQUEIDENTIFIER);
INSERT INTO dbo.system_workflow_runs
  (workflows_guid, element_status, element_payload, element_trigger_type, element_trigger_ref)
OUTPUT inserted.element_guid INTO @out
VALUES (TRY_CAST(? AS UNIQUEIDENTIFIER), ?, ?, ?, ?);
SELECT element_guid FROM @out FOR JSON PATH, WITHOUT_ARRAY_WRAPPER;
""", (workflow.get('element_guid'), ST_PENDING, payload_text, trigger_type, trigger_ref))
    out = list(created.rows) if created and getattr(created, 'rows', None) else []
    return {'run_guid': str(out[0].get('element_guid')) if out else None}

  async def _drain_pending_runs(self, limit: int = 5) -> int:
    result = await run_json_many("""
SELECT TOP (?) element_guid FROM dbo.system_workflow_runs
WHERE element_status = ? ORDER BY element_created_on ASC
FOR JSON PATH, INCLUDE_NULL_VALUES;
""", (limit, ST_PENDING))
    runs = list(result.rows) if result and getattr(result, 'rows', None) else []
    executed = 0
    for r in runs:
      try:
        await self.execute_run(str(r.get('element_guid')))
        executed += 1
      except Exception:
        logging.exception('[AutomationModule] run %s failed', r.get('element_guid'))
    return executed

  async def execute_run(self, run_guid: str) -> dict[str, Any]:
    """Walk a run's actions in sequence, dispatching each to its RPC function."""
    await self.on_ready()

    # Read-then-write claim. Single-instance only: if this ever runs
    # multi-instance, two workers could both see PENDING here. Making it safe
    # means an atomic UPDATE ... OUTPUT that flips PENDING->RUNNING and returns
    # the row only to the winner.
    claimed = await run_exec("""
UPDATE dbo.system_workflow_runs
   SET element_status = ?, element_started_on = SYSUTCDATETIME(),
       element_modified_on = SYSUTCDATETIME()
 WHERE element_guid = TRY_CAST(? AS UNIQUEIDENTIFIER) AND element_status = ?;
""", (ST_RUNNING, run_guid, ST_PENDING))
    if getattr(claimed, 'rowcount', 1) == 0:
      return {'run_guid': run_guid, 'skipped': 'not_pending'}

    actions_result = await run_json_many("""
SELECT a.element_guid, a.element_name, a.element_sequence, a.element_is_optional,
       a.element_config, a.dispositions_recid,
       f.element_module_attr, f.element_method_name
FROM dbo.system_workflow_runs r
JOIN dbo.system_workflow_actions a ON a.workflows_guid = r.workflows_guid AND a.element_is_active = 1
JOIN dbo.reflection_rpc_functions f ON f.recid = a.functions_recid
WHERE r.element_guid = TRY_CAST(? AS UNIQUEIDENTIFIER)
ORDER BY a.element_sequence ASC
FOR JSON PATH, INCLUDE_NULL_VALUES;
""", (run_guid,))
    actions = list(actions_result.rows) if actions_result and getattr(actions_result, 'rows', None) else []

    final_status, error_text = ST_COMPLETED, None
    for index, action in enumerate(actions):
      name = str(action.get('element_name'))
      await run_exec("""
UPDATE dbo.system_workflow_runs
   SET element_current_action = ?, element_action_index = ?, element_modified_on = SYSUTCDATETIME()
 WHERE element_guid = TRY_CAST(? AS UNIQUEIDENTIFIER);
""", (name, index, run_guid))

      started = await self._record_action(run_guid, action, ST_RUNNING, None, None)
      try:
        output = await self._invoke(action)
        await self._record_action(run_guid, action, ST_COMPLETED, output, None, recid=started)
      except Exception as exc:
        logging.exception('[AutomationModule] action %r failed in run %s', name, run_guid)
        await self._record_action(run_guid, action, ST_FAILED, None, repr(exc), recid=started)
        if not action.get('element_is_optional'):
          final_status, error_text = ST_FAILED, f'action {name!r}: {exc!r}'
          break

    await run_exec("""
UPDATE dbo.system_workflow_runs
   SET element_status = ?, element_error = ?, element_ended_on = SYSUTCDATETIME(),
       element_modified_on = SYSUTCDATETIME()
 WHERE element_guid = TRY_CAST(? AS UNIQUEIDENTIFIER);
""", (final_status, error_text, run_guid))
    return {'run_guid': run_guid, 'status': final_status, 'actions': len(actions)}

  async def _invoke(self, action: dict[str, Any]) -> Any:
    """Resolve an action's RPC function to a bound method and call it.

    element_config is the action's static configuration (e.g. {"reindex": true})
    and is passed as keyword arguments, matching how the workflow catalog
    documents it.
    """
    module_attr = str(action.get('element_module_attr') or '')
    method_name = str(action.get('element_method_name') or '')
    module = getattr(self.app.state, module_attr, None)
    if module is None:
      raise RuntimeError(f'Action binds to unknown module attr {module_attr!r}')
    method = getattr(module, method_name, None)
    if method is None:
      raise RuntimeError(f'Action binds to missing method {module_attr}.{method_name}')
    await module.on_ready()

    config = action.get('element_config')
    kwargs: dict[str, Any] = {}
    if config:
      try:
        parsed = json.loads(config) if isinstance(config, str) else config
        if isinstance(parsed, dict):
          kwargs = parsed
      except (TypeError, ValueError):
        raise RuntimeError(f'element_config for {action.get("element_name")!r} is not valid JSON')
    return await method(**kwargs)

  async def _record_action(self, run_guid: str, action: dict[str, Any], status: int,
                           output: Any, error: str | None, recid: int | None = None) -> int | None:
    output_text = None if output is None else json.dumps(output, default=str)[:4000]
    if recid is None:
      created = await run_json_one("""
SET NOCOUNT ON;
DECLARE @out TABLE (recid BIGINT);
INSERT INTO dbo.system_workflow_run_actions
  (runs_guid, actions_guid, element_status, element_started_on)
OUTPUT inserted.recid INTO @out
SELECT r.element_guid, TRY_CAST(? AS UNIQUEIDENTIFIER), ?, SYSUTCDATETIME()
FROM dbo.system_workflow_runs r WHERE r.element_guid = TRY_CAST(? AS UNIQUEIDENTIFIER);
SELECT recid FROM @out FOR JSON PATH, WITHOUT_ARRAY_WRAPPER;
""", (action.get('element_guid'), status, run_guid))
      rows = list(created.rows) if created and getattr(created, 'rows', None) else []
      return int(rows[0].get('recid')) if rows else None

    await run_exec("""
UPDATE dbo.system_workflow_run_actions
   SET element_status = ?, element_output = ?, element_error = ?,
       element_ended_on = SYSUTCDATETIME(), element_modified_on = SYSUTCDATETIME()
 WHERE recid = ?;
""", (status, output_text, error, recid))
    return recid

  # ── Stall detection ─────────────────────────────────────────────────────

  async def scan_stalls(self) -> int:
    """Flag runs stuck in running/waiting past their workflow's threshold.

    Backs the spec's scanStalls. Flags only — it never cancels or retries, since
    a run that merely looks slow may still be progressing.
    """
    await self.on_ready()
    result = await run_exec("""
UPDATE r SET r.element_status = ?, r.element_modified_on = SYSUTCDATETIME()
FROM dbo.system_workflow_runs r
JOIN dbo.system_workflows w ON w.element_guid = r.workflows_guid
WHERE r.element_status IN (?, ?)
  AND r.element_started_on IS NOT NULL
  AND DATEDIFF(SECOND, r.element_started_on, SYSUTCDATETIME())
      > COALESCE(w.element_stall_threshold_seconds, ?);
""", (ST_STALLED, ST_RUNNING, ST_WAITING, DEFAULT_STALL_SECONDS))
    return int(getattr(result, 'rowcount', 0) or 0)
