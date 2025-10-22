"""Account enablements registry helpers."""

from __future__ import annotations

from typing import Any, TYPE_CHECKING

from server.registry.types import DBRequest

from .model import (
  UpsertUserEnablementsParams,
  UserEnablementsRecord,
)

if TYPE_CHECKING:
  from server.registry import SubdomainRouter

__all__ = [
  "get_user_enablements_request",
  "register",
  "upsert_user_enablements_request",
  "UpsertUserEnablementsParams",
  "UserEnablementsRecord",
]

_OP_PREFIX = "db:account:enablements"


def _op(name: str) -> str:
  return f"{_OP_PREFIX}:{name}:1"


def get_user_enablements_request(*, users_guid: str) -> DBRequest:
  params: dict[str, Any] = {"users_guid": users_guid}
  return DBRequest(op=_op("get_by_user"), params=params)


def upsert_user_enablements_request(
  *,
  users_guid: str,
  element_enablements: str,
) -> DBRequest:
  params: UpsertUserEnablementsParams = {
    "users_guid": users_guid,
    "element_enablements": element_enablements,
  }
  return DBRequest(op=_op("upsert"), params=params)


def register(router: "SubdomainRouter") -> None:
  router.add_function("get_by_user", version=1)
  router.add_function("upsert", version=1)
