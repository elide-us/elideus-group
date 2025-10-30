"""Assistant model registry helpers."""

from __future__ import annotations

from functools import partial
from typing import TYPE_CHECKING

from server.registry.types import DBRequest

from .model import (
  GetModelByNameParams,
  ModelRecord,
)

if TYPE_CHECKING:
  from server.registry import RegistryRouter

__all__ = [
  "get_model_by_name_request",
  "list_models_request",
  "register",
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


def register(
  router: "RegistryRouter",
  *,
  domain: str,
  path: tuple[str, ...],
) -> None:
  register_op = partial(router.register_function, domain=domain, path=path)
  register_op(name="get_by_name", version=1)
  register_op(name="list", version=1)
