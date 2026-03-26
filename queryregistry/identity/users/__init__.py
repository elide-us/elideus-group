"""Identity users query registry request builders."""

from __future__ import annotations

from queryregistry.models import DBRequest

__all__ = ["account_exists_request", "read_by_discord_request"]


def account_exists_request(params: dict[str, str]) -> DBRequest:
  return DBRequest(op="db:identity:users:exists:1", payload=dict(params))


def read_by_discord_request(discord_id: str) -> DBRequest:
  return DBRequest(
    op="db:identity:users:read_by_discord:1",
    payload={"discord_id": discord_id},
  )
