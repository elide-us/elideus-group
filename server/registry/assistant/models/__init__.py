"""Assistant model registry helpers."""

from __future__ import annotations

from typing import TYPE_CHECKING

from server.registry.types import DBRequest

if TYPE_CHECKING:
  from server.registry import SubdomainRouter

__all__ = [
  "get_model_by_name_request",
  "list_models_request",
  "register",
]

_OP_PREFIX = "db:assistant:models"
_PROVIDER_MAP = "assistant.models"
_PROVIDER_MODULE = "server.registry.assistant.models.mssql"
_PROVIDER_ATTRS: dict[str, str] = {
  "get_by_name": "get_by_name_v1",
  "list": "list_models_v1",
}


def _op(name: str) -> str:
  return f"{_OP_PREFIX}:{name}:1"


def list_models_request() -> DBRequest:
  return DBRequest(op=_op("list"), params={})


def get_model_by_name_request(name: str) -> DBRequest:
  return DBRequest(op=_op("get_by_name"), params={"name": name})


def register(router: "SubdomainRouter") -> None:
  for name, attr in _PROVIDER_ATTRS.items():
    router.add_function(
      name,
      version=1,
      provider_map=f"{_PROVIDER_MAP}.{name}",
      provider=(_PROVIDER_MODULE, attr),
    )
