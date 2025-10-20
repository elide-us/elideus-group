"""Typed contract helpers for assistant model registry."""

from __future__ import annotations

from typing import TypedDict

__all__ = [
  "GetModelByNameParams",
  "ModelRecord",
]


class ModelRecord(TypedDict, total=False):
  recid: int
  name: str


class GetModelByNameParams(TypedDict):
  name: str
