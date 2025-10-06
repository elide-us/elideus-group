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


def _request(op: str, params: dict[str, Any] | None = None) -> DBRequest:
  return DBRequest(op=op, params=params or {})


def list_public_request() -> DBRequest:
  return _request("db:users:content_public:list_public:1")


def list_reported_request() -> DBRequest:
  return _request("db:users:content_public:list_reported:1")


def get_public_files_request() -> DBRequest:
  return _request("db:users:content_public:get_public_files:1")


def register(router: "SubdomainRouter") -> None:
  router.add_function("list_public", version=1)
  router.add_function("list_reported", version=1)
  router.add_function("get_public_files", version=1, implementation="list_public")
