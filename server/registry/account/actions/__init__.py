"""Account user action log registry helpers."""

from __future__ import annotations

from functools import partial
from typing import TYPE_CHECKING

from server.registry.types import DBRequest

from .model import (
  ListUserActionsParams,
  LogUserActionParams,
  UpdateUserActionParams,
  UserActionLogRecord,
)

if TYPE_CHECKING:
  from server.registry import RegistryRouter

__all__ = [
  "list_user_actions_request",
  "log_user_action_request",
  "register",
  "update_user_action_request",
  "ListUserActionsParams",
  "LogUserActionParams",
  "UpdateUserActionParams",
  "UserActionLogRecord",
]

_OP_PREFIX = "db:account:actions"


def _op(name: str) -> str:
  return f"{_OP_PREFIX}:{name}:1"


def list_user_actions_request(
  *,
  users_guid: str,
  action_recid: int | None = None,
  limit: int | None = None,
) -> DBRequest:
  params: ListUserActionsParams = {"users_guid": users_guid}
  if action_recid is not None:
    params["action_recid"] = action_recid
  if limit is not None:
    params["limit"] = limit
  return DBRequest(op=_op("list_by_user"), payload=params)


def log_user_action_request(
  *,
  recid: int,
  users_guid: str,
  action_recid: int,
  element_url: str | None = None,
  element_notes: str | None = None,
) -> DBRequest:
  params: LogUserActionParams = {
    "recid": recid,
    "users_guid": users_guid,
    "action_recid": action_recid,
  }
  if element_url is not None:
    params["element_url"] = element_url
  if element_notes is not None:
    params["element_notes"] = element_notes
  return DBRequest(op=_op("log"), payload=params)


def update_user_action_request(
  *,
  recid: int,
  element_url: str | None = None,
  element_notes: str | None = None,
) -> DBRequest:
  params: UpdateUserActionParams = {"recid": recid}
  if element_url is not None:
    params["element_url"] = element_url
  if element_notes is not None:
    params["element_notes"] = element_notes
  return DBRequest(op=_op("update"), payload=params)


def register(
  router: "RegistryRouter",
  *,
  domain: str,
  path: tuple[str, ...],
) -> None:
  register_op = partial(router.register_function, domain=domain, path=path)
  register_op(name="list_by_user", version=1)
  register_op(name="log", version=1)
  register_op(name="update", version=1)
