"""Account user registry helpers."""

from __future__ import annotations

from typing import Any, TYPE_CHECKING

from server.registry.types import DBRequest
from . import mssql  # noqa: F401 - ensure provider import

if TYPE_CHECKING:
  from server.registry import SubdomainRouter

__all__ = [
  "set_credits_request",
  "register",
]

_DEF_PROVIDER = "account.users"


def _request(name: str, params: dict[str, Any]) -> DBRequest:
  return DBRequest(op=f"db:account:users:{name}:1", params=params)


def set_credits_request(*, guid: str, credits: int) -> DBRequest:
  return _request("set_credits", {"guid": guid, "credits": credits})


def register(router: "SubdomainRouter") -> None:
  router.add_function(
    "set_credits",
    version=1,
    provider_map=f"{_DEF_PROVIDER}.set_credits",
  )
