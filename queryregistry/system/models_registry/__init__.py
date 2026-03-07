"""System models query registry request builders."""

from __future__ import annotations

from queryregistry.models import DBRequest

from .models import ModelNameParams

__all__ = [
  "get_model_by_name_request",
  "list_models_request",
]


_OP_PREFIX = "db:system:models"


def _op(name: str) -> str:
  return f"{_OP_PREFIX}:{name}:1"


def list_models_request() -> DBRequest:
  return DBRequest(op=_op("list"), payload={})


def get_model_by_name_request(params: ModelNameParams) -> DBRequest:
  return DBRequest(op=_op("get_by_name"), payload=params.model_dump())
