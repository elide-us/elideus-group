"""Account public registry bindings."""

from __future__ import annotations

from typing import Any

from server.registry.types import DBRequest



def _request(op: str, params: dict[str, Any] | None = None) -> DBRequest:
  return DBRequest(op=op, payload=params or {})


def list_public_request() -> DBRequest:
  return _request("db:account:public:list_public:1")


def list_reported_request() -> DBRequest:
  return _request("db:account:public:list_reported:1")


def get_public_files_request() -> DBRequest:
  return _request("db:account:public:get_public_files:1")
