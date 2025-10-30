"""Public vars registry bindings."""

from __future__ import annotations

from functools import partial
from typing import TYPE_CHECKING, Any

from server.registry.types import DBRequest
from .model import PublicVarRecord

if TYPE_CHECKING:
  from server.registry import RegistryRouter

__all__ = [
  "get_hostname_request",
  "get_repo_request",
  "get_version_request",
  "register",
  "PublicVarRecord",
]


def _request(op: str, params: dict[str, Any] | None = None) -> DBRequest:
  return DBRequest(op=op, payload=params or {})


def get_version_request() -> DBRequest:
  return _request("db:system:public_vars:get_version:1")


def get_hostname_request() -> DBRequest:
  return _request("db:system:public_vars:get_hostname:1")


def get_repo_request() -> DBRequest:
  return _request("db:system:public_vars:get_repo:1")


def register(
  router: "RegistryRouter",
  *,
  domain: str,
  path: tuple[str, ...],
) -> None:
  register_op = partial(router.register_function, domain=domain, path=path)
  register_op(name="get_version", version=1)
  register_op(name="get_hostname", version=1)
  register_op(name="get_repo", version=1)
