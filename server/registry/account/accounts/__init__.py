"""Security account registry helpers."""

from __future__ import annotations

from typing import Any

from server.registry.types import DBRequest



def get_security_profile_request(
  *,
  guid: str | None = None,
  access_token: str | None = None,
  provider: str | None = None,
  provider_identifier: str | None = None,
  discord_id: str | None = None,
) -> DBRequest:
  params: dict[str, Any] = {}
  if guid is not None:
    params["guid"] = guid
  if access_token is not None:
    params["access_token"] = access_token
  if provider is not None:
    params["provider"] = provider
  if provider_identifier is not None:
    params["provider_identifier"] = provider_identifier
  if discord_id is not None:
    params["discord_id"] = discord_id
  return DBRequest(op="db:account:accounts:get_security_profile:1", payload=params)


def account_exists_request(user_guid: str) -> DBRequest:
  return DBRequest(
    op="db:account:accounts:exists:1",
    payload={"user_guid": user_guid},
  )
