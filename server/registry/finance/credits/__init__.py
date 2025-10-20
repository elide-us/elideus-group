"""Finance credits registry helpers."""

from __future__ import annotations

from typing import Any, TYPE_CHECKING

from server.registry.types import DBRequest

from .model import SetCreditsParams

if TYPE_CHECKING:
  from server.registry import SubdomainRouter

__all__ = [
  "SetCreditsParams",
  "register",
  "set_credits_request",
]


def _request(name: str, params: dict[str, Any]) -> DBRequest:
  return DBRequest(op=f"db:finance:credits:{name}:1", params=params)


def set_credits_request(*, guid: str, credits: int) -> DBRequest:
  params: SetCreditsParams = {"guid": guid, "credits": credits}
  return _request("set", params)


def register(router: "SubdomainRouter") -> None:
  router.add_function("set", version=1, implementation="set_credits")
