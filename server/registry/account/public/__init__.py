"""Account public registry bindings."""

from __future__ import annotations

from functools import partial
from typing import TYPE_CHECKING, Any

from server.registry.types import DBRequest

if TYPE_CHECKING:
  from server.registry import RegistryRouter

__all__ = [
  "get_public_files_request",
  "list_public_request",
  "list_reported_request",
  "register",
]


def _request(op: str, params: dict[str, Any] | None = None) -> DBRequest:
  return DBRequest(op=op, payload=params or {})


def list_public_request() -> DBRequest:
  return _request("db:account:public:list_public:1")


def list_reported_request() -> DBRequest:
  return _request("db:account:public:list_reported:1")


def get_public_files_request() -> DBRequest:
  return _request("db:account:public:get_public_files:1")


def register(
  router: "RegistryRouter",
  *,
  domain: str,
  path: tuple[str, ...],
) -> None:
  register_op = partial(router.register_function, domain=domain, path=path)
  register_op(name="list_public", version=1)
  register_op(name="list_reported", version=1)
  register_op(name="get_public_files", version=1, implementation="list_public")
