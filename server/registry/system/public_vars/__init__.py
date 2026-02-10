"""Public vars registry bindings."""

from __future__ import annotations

from typing import Any

from server.registry.types import DBRequest
from .model import PublicVarRecord



def _request(op: str, params: dict[str, Any] | None = None) -> DBRequest:
  return DBRequest(op=op, payload=params or {})


def get_version_request() -> DBRequest:
  return _request("db:system:public_vars:get_version:1")


def get_hostname_request() -> DBRequest:
  return _request("db:system:public_vars:get_hostname:1")


def get_repo_request() -> DBRequest:
  return _request("db:system:public_vars:get_repo:1")
