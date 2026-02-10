"""Pydantic models describing finance credit registry contracts.

These models provide a single source of truth for registry requests so
providers and services share a stable contract.  All parameters are validated
eagerly which keeps database operations type-safe.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict

__all__ = [
  "SetCreditsParams",
]


class SetCreditsParams(BaseModel):
  """Parameters required to update a user's credit balance."""

  model_config = ConfigDict(extra="forbid")

  guid: str
  credits: int
