"""System public query registry service models."""

from __future__ import annotations

from typing import TypedDict

from pydantic import BaseModel, ConfigDict

__all__ = [
  "RoutePathParams",
  "RouteRecord",
  "UpsertRouteParams",
]


class RoutePathParams(BaseModel):
  model_config = ConfigDict(extra="forbid")

  path: str


class UpsertRouteParams(BaseModel):
  model_config = ConfigDict(extra="forbid")

  path: str
  name: str
  icon: str | None = None
  sequence: int
  roles: int


class RouteRecord(TypedDict):
  path: str
  name: str
  icon: str | None
  sequence: int
  roles: int
