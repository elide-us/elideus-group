"""Common registry request and response models."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from server.modules.providers import DBResult, get_dbresult_cls

__all__ = [
  "DBRequest",
  "DBResponse",
  "DBResult",
]

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
    DBResultCls = _DBRESULT_CLASS or get_dbresult_cls()
    return DBResultCls(rows=list(self.rows), rowcount=self.rowcount)
_DBRESULT_CLASS = DBResult
