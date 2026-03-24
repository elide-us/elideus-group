"""Finance status code query registry models."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict

__all__ = [
  "GetStatusCodeParams",
  "ListStatusCodesParams",
]


class ListStatusCodesParams(BaseModel):
  model_config = ConfigDict(extra="forbid")

  element_domain: str | None = None


class GetStatusCodeParams(BaseModel):
  model_config = ConfigDict(extra="forbid")

  element_domain: str
  element_code: int
