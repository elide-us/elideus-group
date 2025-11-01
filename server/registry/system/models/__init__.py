"""Assistant model registry helpers."""

from __future__ import annotations

from server.registry.types import DBRequest

from .model import (
  GetModelByNameParams,
  ModelRecord,
)

__all__ = [
  "get_model_by_name_request",
  "list_models_request",
  "GetModelByNameParams",
  "ModelRecord",
]

_OP_PREFIX = "db:system:models"


def _op(name: str) -> str:
  return f"{_OP_PREFIX}:{name}:1"


def list_models_request() -> DBRequest:
  return DBRequest(op=_op("list"), payload={})


def get_model_by_name_request(name: str) -> DBRequest:
  return DBRequest(op=_op("get_by_name"), payload={"name": name})
