from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict


class LoadPathParams1(BaseModel):
  model_config = ConfigDict(extra="forbid")

  path: str


class PathNode1(BaseModel):
  guid: str
  component: str
  category: str
  label: str | None
  fieldBinding: str | None
  sequence: int
  children: list["PathNode1"]


class LoadPathResult1(BaseModel):
  pathData: PathNode1
  componentData: dict[str, Any]


class ObjectTreeCategory1(BaseModel):
  guid: str
  name: str
  display: str | None = None
  icon: str | None = None
  sequence: int


PathNode1.model_rebuild()
