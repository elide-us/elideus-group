"""Content public registry bindings."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from server.registry.types import DBRequest

if TYPE_CHECKING:
  from server.registry import SubdomainRouter

__all__ = [
  "get_public_files_request",
  "list_public_request",
  "list_reported_request",
  "register",
]

_DEF_PROVIDER = "content.public"
_PROVIDER_MODULE = "server.registry.content.public.mssql"
_PROVIDER_ATTRS: dict[str, str] = {
  "list_public": "list_public_v1",
  "list_reported": "list_reported_v1",
  "get_public_files": "get_public_files_v1",
}


def _request(op: str, params: dict[str, Any] | None = None) -> DBRequest:
  return DBRequest(op=op, params=params or {})


def list_public_request() -> DBRequest:
  return _request("db:content:public:list_public:1")


def list_reported_request() -> DBRequest:
  return _request("db:content:public:list_reported:1")


def get_public_files_request() -> DBRequest:
  return _request("db:content:public:get_public_files:1")


def register(router: "SubdomainRouter") -> None:
  for name, attr in _PROVIDER_ATTRS.items():
    router.add_function(
      name,
      version=1,
      provider_map=f"{_DEF_PROVIDER}.{name}",
      provider=(_PROVIDER_MODULE, attr),
    )
