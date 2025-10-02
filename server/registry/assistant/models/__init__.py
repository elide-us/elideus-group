"""Assistant model registry helpers."""

from __future__ import annotations

from typing import TYPE_CHECKING

from server.registry.types import DBRequest

from . import mssql  # noqa: F401 - ensure provider imports are discoverable

if TYPE_CHECKING:
  from server.registry import SubdomainRouter

__all__ = [
  "get_model_by_name_request",
  "list_models_request",
  "register",
]

_OP_PREFIX = "db:assistant:models"
_PROVIDER_MAP = "assistant.models"


def _op(name: str) -> str:
  return f"{_OP_PREFIX}:{name}:1"


def list_models_request() -> DBRequest:
  return DBRequest(op=_op("list"), params={})


def get_model_by_name_request(name: str) -> DBRequest:
  return DBRequest(op=_op("get_by_name"), params={"name": name})


def register(router: "SubdomainRouter") -> None:
  router.add_function(
    "get_by_name",
    version=1,
    provider_map=f"{_PROVIDER_MAP}.get_by_name",
  )
  router.add_function(
    "list",
    version=1,
    provider_map=f"{_PROVIDER_MAP}.list",
  )
