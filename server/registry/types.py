"""Common registry request and response models."""

from __future__ import annotations

import re
from collections.abc import Mapping
from types import MappingProxyType
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

try:  # pragma: no cover - fallback for test stubs
  from server.models import ensure_json_serializable
except ImportError:  # pragma: no cover - simplified validation for isolated tests
  def ensure_json_serializable(value: Any, *, field_name: str) -> Any:
    return value
from server.modules.providers import DBResult

__all__ = [
  "DBRequest",
  "DBResponse",
  "DBResult",
]

DB_PATTERN = re.compile(r"^db:(?:[a-z0-9_]+:){3,}[0-9]+$")


class DBRequest(BaseModel):
  """Payload describing a database registry operation."""

  op: str = Field(pattern=DB_PATTERN.pattern)
  params: dict[str, Any] = Field(default_factory=dict)
  metadata: Mapping[str, Any] | None = None

  model_config = ConfigDict(frozen=True)

  @field_validator("params")
  @classmethod
  def _validate_params(cls, value: dict[str, Any]):
    return {
      str(key): ensure_json_serializable(param_value, field_name=f"params['{key}']")
      for key, param_value in value.items()
    }

  @field_validator("metadata")
  @classmethod
  def _freeze_metadata(cls, value: Mapping[str, Any] | None):
    if value is None:
      return None
    frozen = {
      str(key): ensure_json_serializable(meta_value, field_name=f"metadata['{key}']")
      for key, meta_value in value.items()
    }
    return MappingProxyType(frozen)

  @model_validator(mode="after")
  def _validate_op(self):
    parts = self.op.split(":")
    if len(parts) < 5:
      raise ValueError("op must include domain, subdomain, name, and version segments")
    version_segment = parts[-1]
    try:
      int(version_segment)
    except ValueError as exc:  # pragma: no cover
      raise ValueError("op must terminate with an integer version segment") from exc
    return self


class DBResponse(BaseModel):
  """Wrapper around :class:`DBResult` used by the registry."""

  rows: list[dict] = Field(default_factory=list)
  rowcount: int = 0
  meta: dict[str, Any] | None = None

  @classmethod
  def from_result(cls, result: DBResult, *, meta: dict[str, Any] | None = None) -> "DBResponse":
    return cls(rows=list(result.rows), rowcount=result.rowcount, meta=meta)

  def to_result(self, *, result_cls: type[DBResult]) -> DBResult:
    return result_cls(rows=list(self.rows), rowcount=self.rowcount)
