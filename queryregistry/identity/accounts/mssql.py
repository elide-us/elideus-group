"""MSSQL implementations for identity accounts query registry services."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any
from uuid import UUID

from queryregistry.providers.mssql import run_json_one

from queryregistry.models import DBResponse

__all__ = [
  "account_exists",
  "get_by_discord_id",
  "get_security_profile",
]

_BASE_QUERY = """
  SELECT TOP 1
    v.user_guid,
    v.user_guid AS guid,
    v.user_roles,
    v.user_roles AS element_roles,
    v.user_created_on,
    v.user_modified_on,
    v.element_rotkey,
    v.element_rotkey AS rotkey,
    v.element_rotkey_iat,
    v.element_rotkey_exp,
    ap.element_name AS provider_name,
    ap.element_display AS provider_display,
    au.providers_recid,
    v.session_guid,
    v.session_created_on,
    v.session_created_on AS session_created_at,
    v.session_modified_on,
    v.device_guid,
    v.device_created_on,
    v.device_modified_on,
    v.element_token,
    v.element_token AS token,
    v.element_token_iat,
    v.element_token_iat AS issued_at,
    v.element_token_exp,
    v.element_token_exp AS expires_at,
    v.element_revoked_at,
    v.element_revoked_at AS revoked_at,
    v.element_device_fingerprint,
    v.element_device_fingerprint AS device_fingerprint,
    v.element_user_agent,
    v.element_user_agent AS user_agent,
    v.element_ip_last_seen,
    v.element_ip_last_seen AS ip_last_seen
  FROM vw_user_session_security v
  LEFT JOIN account_users au ON au.element_guid = v.user_guid
  LEFT JOIN auth_providers ap ON ap.recid = au.providers_recid
"""

_JOIN_USERS_AUTH = """
  JOIN users_auth ua ON ua.users_guid = v.user_guid AND ua.element_linked = 1
"""


def _normalize_provider_identifier(identifier: str) -> str:
  try:
    return str(UUID(identifier))
  except (TypeError, ValueError):
    raise ValueError("provider_identifier must be a valid UUID") from None


def _normalize_discord_identifier(discord_id: str) -> str:
  from uuid import NAMESPACE_URL, uuid5

  return str(UUID(str(uuid5(NAMESPACE_URL, str(discord_id)))))


def _unique(sequence: Iterable[str]) -> list[str]:
  items: list[str] = []
  seen: set[str] = set()
  for entry in sequence:
    if entry not in seen:
      seen.add(entry)
      items.append(entry)
  return items


async def get_security_profile(params: Mapping[str, Any]) -> DBResponse:
  """Return an operation that fetches security metadata for a user context."""

  filters: list[str] = []
  args: list[Any] = []
  joins: list[str] = []

  guid = params.get("user_guid") or params.get("guid")
  if guid:
    filters.append("v.user_guid = ?")
    args.append(str(guid))

  token = params.get("access_token") or params.get("token")
  if token:
    filters.append("v.element_token = ?")
    args.append(str(token))

  provider = params.get("provider")
  provider_identifier = params.get("provider_identifier")
  if provider and provider_identifier:
    joins.append(_JOIN_USERS_AUTH)
    filters.append("ap.element_name = ?")
    args.append(str(provider))
    normalised = _normalize_provider_identifier(str(provider_identifier))
    filters.append("ua.element_identifier = ?")
    args.append(normalised)

  discord_id = params.get("discord_id")
  if discord_id:
    joins.append(_JOIN_USERS_AUTH)
    filters.append("ap.element_name = ?")
    args.append("discord")
    filters.append("ua.element_identifier = ?")
    args.append(_normalize_discord_identifier(str(discord_id)))

  if not filters:
    raise ValueError("get_security_profile requires a selection filter")

  join_sql = "".join(_unique(joins))
  where_sql = " AND\n    ".join(filters)
  sql = f"{_BASE_QUERY}{join_sql}  WHERE {where_sql}\n  FOR JSON PATH, WITHOUT_ARRAY_WRAPPER;"
  response = await run_json_one(sql, args)
  return DBResponse(payload=response.payload)


async def account_exists(args: Mapping[str, Any]) -> DBResponse:
  guid = str(UUID(args["user_guid"]))
  sql = """
    SELECT 1 AS exists_flag
    FROM account_users
    WHERE element_guid = ?
    FOR JSON PATH, WITHOUT_ARRAY_WRAPPER;
  """
  response = await run_json_one(sql, (guid,))
  return DBResponse(payload=response.payload)


async def get_by_discord_id(params: Mapping[str, Any]) -> DBResponse:
  """Look up a user's GUID and role mask by Discord numeric ID.

  The Discord auth provider stores identifiers as
  uuid5(NAMESPACE_URL, f"discord:{discord_id}") — the prefix is
  required to match.
  """
  from uuid import NAMESPACE_URL, uuid5

  discord_id = str(params["discord_id"])
  identifier = str(UUID(str(uuid5(NAMESPACE_URL, f"discord:{discord_id}"))))

  sql = """
    SELECT TOP 1
      user_guid,
      user_roles
    FROM vw_user_discord_security
    WHERE discord_identifier = ?
    FOR JSON PATH, WITHOUT_ARRAY_WRAPPER, INCLUDE_NULL_VALUES;
  """
  return await run_json_one(sql, (identifier,))
