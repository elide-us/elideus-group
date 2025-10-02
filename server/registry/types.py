"""Common registry request and response models."""

from __future__ import annotations

from typing import Any
import importlib

from pydantic import BaseModel, Field

from server.modules.providers import DBResult

__all__ = [
  "DBRequest",
  "DBResponse",
  "DBResult",
]


def _current_dbresult_cls():
  providers_mod = importlib.import_module("server.modules.providers")
  return getattr(providers_mod, "DBResult")


class DBRequest(BaseModel):
  """Payload describing a database registry operation."""

  op: str
  params: dict[str, Any] = Field(default_factory=dict)
  metadata: dict[str, Any] | None = None

  class Config:
    frozen = True
    arbitrary_types_allowed = True


class DBResponse(BaseModel):
  """Wrapper around :class:`DBResult` used by the registry."""

  rows: list[dict] = Field(default_factory=list)
  rowcount: int = 0
  meta: dict[str, Any] | None = None

  @classmethod
  def from_result(cls, result: DBResult, *, meta: dict[str, Any] | None = None) -> "DBResponse":
    return cls(rows=list(result.rows), rowcount=result.rowcount, meta=meta)

  def to_result(self) -> DBResult:
    DBResultCls = _current_dbresult_cls()
    return DBResultCls(rows=list(self.rows), rowcount=self.rowcount)
