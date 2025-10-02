"""Public vars registry bindings."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from server.registry.types import DBRequest

from . import mssql  # noqa: F401

if TYPE_CHECKING:
  from server.registry import SubdomainRouter

__all__ = [
  "get_hostname_request",
  "get_repo_request",
  "get_version_request",
  "register",
]

_DEF_PROVIDER = "public.vars"


def _request(op: str, params: dict[str, Any] | None = None) -> DBRequest:
  return DBRequest(op=op, params=params or {})


def get_version_request() -> DBRequest:
  return _request("db:public:vars:get_version:1")


def get_hostname_request() -> DBRequest:
  return _request("db:public:vars:get_hostname:1")


def get_repo_request() -> DBRequest:
  return _request("db:public:vars:get_repo:1")


def register(router: "SubdomainRouter") -> None:
  router.add_function(
    "get_version",
    version=1,
    provider_map=f"{_DEF_PROVIDER}.get_version",
  )
  router.add_function(
    "get_hostname",
    version=1,
    provider_map=f"{_DEF_PROVIDER}.get_hostname",
  )
  router.add_function(
    "get_repo",
    version=1,
    provider_map=f"{_DEF_PROVIDER}.get_repo",
  )
