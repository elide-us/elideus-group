"""Type contracts for system public link registry operations."""

from __future__ import annotations

from typing import TypedDict

__all__ = [
  "HomeLink",
  "NavbarRoute",
  "NavbarRoutesParams",
]


class HomeLink(TypedDict):
  """Metadata for a public home link."""

  title: str
  url: str


class NavbarRoute(TypedDict):
  """Metadata for a public navigation route."""

  path: str
  name: str
  icon: str
  sequence: int


class NavbarRoutesParams(TypedDict, total=False):
  """Parameters for fetching navbar routes."""

  role_mask: int
