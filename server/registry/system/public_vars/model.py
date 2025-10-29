"""Response payload helpers for public system vars."""

from __future__ import annotations

from typing import TypedDict

__all__ = ["PublicVarRecord"]


class PublicVarRecord(TypedDict, total=False):
  """Representation of a public system variable."""

  version: str | None
  hostname: str | None
  repo: str | None
