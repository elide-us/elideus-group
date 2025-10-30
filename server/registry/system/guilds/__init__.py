"""Discord guild registry helpers."""

from __future__ import annotations

from datetime import datetime
from functools import partial
from typing import TYPE_CHECKING, Any

from server.registry.types import DBRequest

if TYPE_CHECKING:
  from server.registry import RegistryRouter

__all__ = [
  "get_guild_request",
  "list_guilds_request",
  "register",
  "upsert_guild_request",
]


_DEF_PROVIDER_KEY = "db:system:discord_guilds"


def _normalise_identifier(value: str | int | None) -> str | None:
  if value is None:
    return None
  return str(value)


def _request(op: str, params: dict[str, Any] | None = None) -> DBRequest:
  return DBRequest(op=op, payload=params or {})


def upsert_guild_request(
  *,
  guild_id: str | int,
  name: str,
  joined_on: datetime | str | None = None,
  member_count: int | None = None,
  owner_id: str | int | None = None,
  region: str | None = None,
  left_on: datetime | str | None = None,
  notes: str | None = None,
) -> DBRequest:
  params: dict[str, Any] = {
    "guild_id": _normalise_identifier(guild_id),
    "name": name,
  }
  if joined_on is not None:
    params["joined_on"] = joined_on
  if member_count is not None:
    params["member_count"] = member_count
  owner_id = _normalise_identifier(owner_id)
  if owner_id is not None:
    params["owner_id"] = owner_id
  if region is not None:
    params["region"] = region
  if left_on is not None:
    params["left_on"] = left_on
  if notes is not None:
    params["notes"] = notes
  return _request(f"{_DEF_PROVIDER_KEY}:upsert_guild:1", params)


def get_guild_request(*, guild_id: str | int) -> DBRequest:
  params = {"guild_id": _normalise_identifier(guild_id)}
  return _request(f"{_DEF_PROVIDER_KEY}:get_guild:1", params)


def list_guilds_request(*, include_inactive: bool = True) -> DBRequest:
  params: dict[str, Any] = {}
  if not include_inactive:
    params["include_inactive"] = False
  return _request(f"{_DEF_PROVIDER_KEY}:list_guilds:1", params)


def register(
  router: "RegistryRouter",
  *,
  domain: str,
  path: tuple[str, ...],
) -> None:
  register_op = partial(router.register_function, domain=domain, path=path)
  register_op(name="upsert_guild", version=1)
  register_op(name="get_guild", version=1)
  register_op(name="list_guilds", version=1)
