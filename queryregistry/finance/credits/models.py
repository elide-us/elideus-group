"""Finance credits query registry models."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict

__all__ = ["SetCreditsParams"]


class SetCreditsParams(BaseModel):
  model_config = ConfigDict(extra="forbid")

  guid: str
  credits: int
