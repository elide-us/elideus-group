"""Typed request contracts for finance credit registry operations."""

from __future__ import annotations

from typing import TypedDict

__all__ = [
  "SetCreditsParams",
]


class SetCreditsParams(TypedDict):
  """Parameters required to update a user's credit balance."""

  guid: str
  credits: int
