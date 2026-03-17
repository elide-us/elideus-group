import asyncio
import json
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from uuid import uuid4

from fastapi import FastAPI
from pydantic import BaseModel

from server.modules.async_task_handlers import CallbackHandler, PipelineHandler, PollHandler
from server.modules.async_task_module import (
  AsyncTaskModule,
  STATUS_COMPLETED,
  STATUS_FAILED,
  STATUS_POLLING,
  STATUS_QUEUED,
  STATUS_RUNNING,
  STATUS_TIMED_OUT,
  STATUS_WAITING_CALLBACK,
)


class FakeDbModule:
  def __init__(self):
    self.tasks = []
    self.events = []
    self._recid = 1
    self._event_recid = 1

  async def on_ready(self):
    return None

  async def run(self, request):
    op = request.op
    payload = request.payload
    if op.endswith(":create_task:1"):
      recid = self._recid
      self._recid += 1
      row = {
        "recid": recid,
        "element_guid": str(uuid4()),
        "element_handler_type": payload["handler_type"],
        "element_handler_name": payload["handler_name"],
        "element_payload": payload.get("payload"),
        "element_status": payload.get("status", 0),
        "element_result": None,
        "element_error": None,
        "element_current_step": None,
        "element_step_index": 0,
        "element_max_retries": payload.get("max_retries", 0),
        "element_retry_count": payload.get("retry_count", 0),
        "element_poll_interval_seconds": payload.get("poll_interval_seconds"),
        "element_timeout_seconds": payload.get("timeout_seconds"),
        "element_timeout_at": payload.get("timeout_at"),
        "element_external_id": payload.get("external_id"),
        "element_source_type": payload.get("source_type"),
        "element_source_id": payload.get("source_id"),
        "element_created_by": payload.get("created_by"),
        "element_created_on": datetime.now(timezone.utc).isoformat(),
        "element_modified_on": datetime.now(timezone.utc).isoformat(),
      }
      self.tasks.append(row)
      return SimpleNamespace(rows=[row])

    if op.endswith(":get_task:1"):
      for row in self.tasks:
        if row["element_guid"] == payload["guid"]:
          return SimpleNamespace(rows=[row])
      return SimpleNamespace(rows=[])

    if op.endswith(":list_tasks:1"):
      rows = []
      for row in self.tasks:
        if payload.get("status") is not None and row["element_status"] != payload["status"]:
          continue
        if payload.get("handler_type") is not None and row["element_handler_type"] != payload["handler_type"]:
          continue
        if payload.get("handler_name") is not None and row["element_handler_name"] != payload["handler_name"]:
          continue
        rows.append(row)
      return SimpleNamespace(rows=rows)

    if op.endswith(":update_task:1"):
      row = next(t for t in self.tasks if t["recid"] == payload["recid"])
      mapping = {
        "status": "element_status",
        "error": "element_error",
        "current_step": "element_current_step",
        "step_index": "element_step_index",
        "retry_count": "element_retry_count",
        "poll_interval_seconds": "element_poll_interval_seconds",
        "timeout_seconds": "element_timeout_seconds",
        "timeout_at": "element_timeout_at",
        "external_id": "element_external_id",
      }
      for key, column in mapping.items():
        if key in payload:
          row[column] = payload[key]
      if "result" in payload:
        value = payload["result"]
        row["element_result"] = json.dumps(value) if isinstance(value, (dict, list)) else value
      row["element_modified_on"] = datetime.now(timezone.utc).isoformat()
      return SimpleNamespace(rows=[row])

    if op.endswith(":create_task_event:1"):
      self.events.append(
        {
          "recid": self._event_recid,
          "tasks_recid": payload["tasks_recid"],
          "element_event_type": payload["event_type"],
          "element_step_name": payload.get("step_name"),
          "element_detail": payload.get("detail"),
          "element_created_on": datetime.now(timezone.utc).isoformat(),
        }
      )
      self._event_recid += 1
      return SimpleNamespace(rows=[])

    if op.endswith(":list_task_events:1"):
      rows = [e for e in self.events if e["tasks_recid"] == payload["tasks_recid"]]
      return SimpleNamespace(rows=rows)

    raise AssertionError(f"Unhandled op: {op}")


class PollPayload(BaseModel):
  prompt: str


class DemoPollHandler(PollHandler):
  payload_model = PollPayload

  def __init__(self):
    self._checks = 0

  async def start(self, app, payload):
    return {"external_id": "ext-1", "poll_interval": 0}

  async def check(self, app, external_id, payload):
    self._checks += 1
    return {"complete": True, "result": {"external_id": external_id}}


class DemoCallbackHandler(CallbackHandler):
  async def start(self, app, payload):
    return {}

  async def on_callback(self, app, payload, callback_data):
    return {"complete": True, "result": callback_data}


class DemoPipelineHandler(PipelineHandler):
  def __init__(self):
    self.steps = [("step_a", self._step_a), ("step_b", self._step_b)]

  async def _step_a(self, app, payload, context):
    return {"a": 1}

  async def _step_b(self, app, payload, context):
    if payload.get("fail"):
      raise RuntimeError("step_b_failed")
    return {"b": context["a"] + 1}


async def _build_module() -> AsyncTaskModule:
  app = FastAPI()
  app.state.db = FakeDbModule()
  mod = AsyncTaskModule(app)
  await mod.startup()
  return mod


def test_submission_and_poll_lifecycle():
  asyncio.run(_test_submission_and_poll_lifecycle())


async def _test_submission_and_poll_lifecycle():
  module = await _build_module()
  try:
    module.register_handler("test.poll", DemoPollHandler())
    task = await module.submit_task("test.poll", {"prompt": "hi"}, "rpc", "req-1", None, 30, 0, 0)
    assert task["status"] == STATUS_QUEUED

    await module.tick_once()
    started = await module.get_task(task["guid"])
    assert started["status"] == STATUS_POLLING

    await module.tick_once()
    completed = await module.get_task(task["guid"])
    assert completed["status"] == STATUS_COMPLETED
  finally:
    await module.shutdown()


def test_pipeline_failure_and_retry():
  asyncio.run(_test_pipeline_failure_and_retry())


async def _test_pipeline_failure_and_retry():
  module = await _build_module()
  try:
    module.register_handler("test.pipeline", DemoPipelineHandler())
    task = await module.submit_task("test.pipeline", {"fail": True}, "rpc", "req-2", None, 30, None, 2)

    await module.tick_once()
    await module.tick_once()
    await module.tick_once()
    failed = await module.get_task(task["guid"])
    assert failed["status"] == STATUS_FAILED
    assert failed["current_step"] == "step_b"

    await module.retry_task(task["guid"])
    retried = await module.get_task(task["guid"])
    assert retried["status"] == STATUS_RUNNING
    assert retried["retry_count"] == 1
  finally:
    await module.shutdown()


def test_callback_resolution():
  asyncio.run(_test_callback_resolution())


async def _test_callback_resolution():
  module = await _build_module()
  try:
    module.register_handler("test.callback", DemoCallbackHandler())
    task = await module.submit_task("test.callback", {}, "rpc", "req-3", None, 30, None, 0)

    await module.tick_once()
    waiting = await module.get_task(task["guid"])
    assert waiting["status"] == STATUS_WAITING_CALLBACK

    resolved = await module.resolve_callback(task["guid"], {"ok": True})
    assert resolved["status"] == STATUS_COMPLETED
    assert resolved["result"]["ok"] is True
  finally:
    await module.shutdown()


def test_timeout_detection():
  asyncio.run(_test_timeout_detection())


async def _test_timeout_detection():
  module = await _build_module()
  try:
    module.register_handler("test.callback.timeout", DemoCallbackHandler())
    task = await module.submit_task("test.callback.timeout", {}, "rpc", "req-4", None, 1, None, 0)

    row = next(t for t in module.db.tasks if t["element_guid"] == task["guid"])
    row["element_timeout_at"] = (datetime.now(timezone.utc) - timedelta(seconds=5)).isoformat()

    await module.tick_once()
    timed_out = await module.get_task(task["guid"])
    assert timed_out["status"] == STATUS_TIMED_OUT
  finally:
    await module.shutdown()
