"""Data models for the QueryRegistry namespace."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

__all__ = ["DBRequest", "DBResponse"]


class DBRequest(BaseModel):
  """Representation of a query registry request."""

  op: str
  payload: dict[str, Any] = Field(default_factory=dict)


class DBResponse(BaseModel):
  """Representation of a query registry response."""

  op: str = ""
  payload: Any | None = None
