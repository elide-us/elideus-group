"""System models query registry request builders."""

from __future__ import annotations

from queryregistry.models import DBRequest

from .models import DeleteModelParams, ModelNameParams, UpsertModelParams

__all__ = [
  "delete_model_request",
  "get_model_by_name_request",
  "list_models_request",
  "upsert_model_request",
]


_OP_PREFIX = "db:system:models"


def _op(name: str) -> str:
  return f"{_OP_PREFIX}:{name}:1"


def list_models_request() -> DBRequest:
  return DBRequest(op=_op("list"), payload={})


def get_model_by_name_request(params: ModelNameParams) -> DBRequest:
  return DBRequest(op=_op("get_by_name"), payload=params.model_dump())


def upsert_model_request(params: UpsertModelParams) -> DBRequest:
  return DBRequest(op=_op("upsert"), payload=params.model_dump())


def delete_model_request(params: DeleteModelParams) -> DBRequest:
  return DBRequest(op=_op("delete"), payload=params.model_dump())
