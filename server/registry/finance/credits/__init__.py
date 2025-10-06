"""Finance credits registry helpers."""

from __future__ import annotations

from typing import Any, TYPE_CHECKING

from . import mssql as credits_mssql

from server.registry.types import DBRequest

if TYPE_CHECKING:
  from server.registry import SubdomainRouter

__all__ = [
  "mssql",
  "register",
  "set_credits_request",
]

mssql = credits_mssql


def _request(name: str, params: dict[str, Any]) -> DBRequest:
  return DBRequest(op=f"db:finance:credits:{name}:1", params=params)


def set_credits_request(*, guid: str, credits: int) -> DBRequest:
  params = {"guid": guid, "credits": credits}
  return _request("set", params)


def register(router: "SubdomainRouter") -> None:
  router.add_function("set", version=1, implementation="set_credits")
