from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel, Field


class StepResult(BaseModel):
  """Return value from a workflow step's try_step method."""

  output: dict[str, Any] = Field(default_factory=dict)
  compensation: dict[str, Any] | None = None


class WorkflowStep(ABC):
  """Base class for all workflow steps.

  Steps are invoked in RAII order by WorkflowModule:
  init_step -> try_step -> catch_step (on failure) -> finally_step.
  """

  step_type: str = "pipe"
  disposition: str = "harmless"

  async def init_step(self, app, payload: dict[str, Any], context: dict[str, Any], config: dict[str, Any]) -> None:
    return None

  @abstractmethod
  async def try_step(
    self,
    app,
    payload: dict[str, Any],
    context: dict[str, Any],
    config: dict[str, Any],
  ) -> StepResult:
    ...

  async def catch_step(
    self,
    app,
    payload: dict[str, Any],
    context: dict[str, Any],
    config: dict[str, Any],
    error: Exception,
  ) -> None:
    return None

  async def finally_step(self, app, payload: dict[str, Any], context: dict[str, Any], config: dict[str, Any]) -> None:
    return None

  async def compensate_step(
    self,
    app,
    payload: dict[str, Any],
    context: dict[str, Any],
    compensation: dict[str, Any],
  ) -> None:
    return None
