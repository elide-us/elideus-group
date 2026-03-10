"""Shared reflection domain models."""

from __future__ import annotations

from typing import TypedDict

__all__ = ["SchemaObjectRef"]


class SchemaObjectRef(TypedDict):
  """Schema-qualified object reference."""

  schema: str
  name: str
