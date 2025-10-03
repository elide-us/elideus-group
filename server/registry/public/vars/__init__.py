"""Public vars registry bindings."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from server.registry.types import DBRequest

if TYPE_CHECKING:
  from server.registry import SubdomainRouter

__all__ = [
  "get_hostname_request",
  "get_repo_request",
  "get_version_request",
  "register",
]

_DEF_PROVIDER = "public.vars"
_PROVIDER_MODULE = "server.registry.public.vars.mssql"
_PROVIDER_ATTRS: dict[str, str] = {
  "get_version": "get_version_v1",
  "get_hostname": "get_hostname_v1",
  "get_repo": "get_repo_v1",
}


def _request(op: str, params: dict[str, Any] | None = None) -> DBRequest:
  return DBRequest(op=op, params=params or {})


def get_version_request() -> DBRequest:
  return _request("db:public:vars:get_version:1")


def get_hostname_request() -> DBRequest:
  return _request("db:public:vars:get_hostname:1")


def get_repo_request() -> DBRequest:
  return _request("db:public:vars:get_repo:1")


def register(router: "SubdomainRouter") -> None:
  for name, attr in _PROVIDER_ATTRS.items():
    router.add_function(
      name,
      version=1,
      provider_map=f"{_DEF_PROVIDER}.{name}",
      provider=(_PROVIDER_MODULE, attr),
    )
