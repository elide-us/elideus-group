"""Session registry helpers for the users domain."""

from __future__ import annotations

from datetime import datetime
from typing import Any, TYPE_CHECKING

from server.registry.types import DBRequest

if TYPE_CHECKING:
  from server.registry import SubdomainRouter

__all__ = [
  "get_rotkey_request",
  "register",
  "set_rotkey_request",
]


def _request(op: str, params: dict[str, Any]) -> DBRequest:
  return DBRequest(op=op, params=params)


def get_rotkey_request(*, guid: str) -> DBRequest:
  return _request(
    "db:users:session:get_rotkey:1",
    {"guid": guid},
  )


def set_rotkey_request(
  *,
  guid: str,
  rotkey: str,
  iat: datetime,
  exp: datetime,
) -> DBRequest:
  return _request(
    "db:users:session:set_rotkey:1",
    {
      "guid": guid,
      "rotkey": rotkey,
      "iat": iat,
      "exp": exp,
    },
  )


def register(router: "SubdomainRouter") -> None:
  router.add_function("get_rotkey", version=1)
  router.add_function("set_rotkey", version=1)
