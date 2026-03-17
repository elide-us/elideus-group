from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

from pydantic import BaseModel


class AsyncTaskHandler:
  handler_type: str
  payload_model: type[BaseModel] | None = None


class PollHandler(AsyncTaskHandler):
  handler_type = "poll"

  async def start(self, app, payload: dict[str, Any]) -> dict[str, Any]:
    raise NotImplementedError

  async def check(self, app, external_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    raise NotImplementedError


class CallbackHandler(AsyncTaskHandler):
  handler_type = "callback"

  async def start(self, app, payload: dict[str, Any]) -> dict[str, Any]:
    raise NotImplementedError

  async def on_callback(self, app, payload: dict[str, Any], callback_data: dict[str, Any]) -> dict[str, Any]:
    raise NotImplementedError


PipelineStep = Callable[[Any, dict[str, Any], dict[str, Any]], Awaitable[dict[str, Any]]]


class PipelineHandler(AsyncTaskHandler):
  handler_type = "pipeline"
  steps: list[tuple[str, PipelineStep]] = []
