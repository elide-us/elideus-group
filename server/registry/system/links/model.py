"""Pydantic models for system public link registry interactions."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict

__all__ = [
  "HomeLink",
  "NavbarRoute",
  "NavbarRoutesParams",
]


class HomeLink(BaseModel):
  """Metadata for a public home link."""

  model_config = ConfigDict(extra="forbid")

  title: str
  url: str


class NavbarRoute(BaseModel):
  """Metadata for a public navigation route."""

  model_config = ConfigDict(extra="forbid")

  path: str
  name: str
  icon: str
  sequence: int


class NavbarRoutesParams(BaseModel):
  """Parameters for fetching navbar routes."""

  model_config = ConfigDict(extra="forbid")

  role_mask: int | None = None
