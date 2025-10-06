"""Public users registry bindings."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from server.registry.types import DBRequest

if TYPE_CHECKING:
  from server.registry import SubdomainRouter

__all__ = [
  "get_profile_request",
  "get_published_files_request",
  "register",
]


def _request(op: str, params: dict[str, Any] | None = None) -> DBRequest:
  return DBRequest(op=op, params=params or {})


def get_profile_request(*, guid: str) -> DBRequest:
  return _request("db:users:public.users:get_profile:1", {"guid": guid})


def get_published_files_request(*, guid: str) -> DBRequest:
  return _request("db:users:public.users:get_published_files:1", {"guid": guid})


def register(router: "SubdomainRouter") -> None:
  router.add_function("get_profile", version=1)
  router.add_function("get_published_files", version=1)
