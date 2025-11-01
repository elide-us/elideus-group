"""Account enablements registry helpers."""

from __future__ import annotations

from typing import Any

from server.registry.types import DBRequest

from .model import (
  UpsertUserEnablementsParams,
  UserEnablementsRecord,
)

__all__ = [
  "get_user_enablements_request",
  "upsert_user_enablements_request",
  "UpsertUserEnablementsParams",
  "UserEnablementsRecord",
]

_OP_PREFIX = "db:account:enablements"


def _op(name: str) -> str:
  return f"{_OP_PREFIX}:{name}:1"


def get_user_enablements_request(*, users_guid: str) -> DBRequest:
  params: dict[str, Any] = {"users_guid": users_guid}
  return DBRequest(op=_op("get_by_user"), payload=params)


def upsert_user_enablements_request(
  *,
  users_guid: str,
  element_enablements: str,
) -> DBRequest:
  params: UpsertUserEnablementsParams = {
    "users_guid": users_guid,
    "element_enablements": element_enablements,
  }
  return DBRequest(op=_op("upsert"), payload=params)
