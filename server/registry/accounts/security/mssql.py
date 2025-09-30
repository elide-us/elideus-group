"""MSSQL provider helpers for account security queries."""

from __future__ import annotations

from importlib import import_module
from typing import TYPE_CHECKING, Any, Iterable
from uuid import UUID, NAMESPACE_URL, uuid5

if TYPE_CHECKING:
  from server.modules.providers.database.mssql_provider.db_helpers import Operation

__all__ = [
  "get_security_profile_v1",
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


def _normalise_provider_identifier(identifier: str) -> str:
  try:
    return str(UUID(identifier))
  except (TypeError, ValueError):
    raise ValueError("provider_identifier must be a valid UUID") from None


def _normalise_discord_identifier(discord_id: str) -> str:
  return str(UUID(str(uuid5(NAMESPACE_URL, f"discord:{discord_id}"))))


def _unique(sequence: Iterable[str]) -> list[str]:
  items: list[str] = []
  seen: set[str] = set()
  for entry in sequence:
    if entry not in seen:
      seen.add(entry)
      items.append(entry)
  return items


def _make_operation(sql: str, params: Iterable[Any]) -> "Operation":
  db_helpers = import_module("server.modules.providers.database.mssql_provider.db_helpers")
  json_one = getattr(db_helpers, "json_one", None)
  payload = tuple(params)
  if callable(json_one):
    op = json_one(sql, payload)
    if op is not None:
      return op
  operation_cls = getattr(db_helpers, "Operation")
  providers_mod = import_module("server.modules.providers")
  db_run_mode = getattr(providers_mod, "DbRunMode")
  try:
    return operation_cls(db_run_mode.JSON_ONE, sql, payload)
  except TypeError:
    op = operation_cls()
    setattr(op, "kind", db_run_mode.JSON_ONE)
    setattr(op, "sql", sql)
    setattr(op, "params", payload)
    setattr(op, "postprocess", None)
    return op


def get_security_profile_v1(params: dict[str, Any]) -> "Operation":
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
    normalised = _normalise_provider_identifier(str(provider_identifier))
    filters.append("ua.element_identifier = ?")
    args.append(normalised)

  discord_id = params.get("discord_id")
  if discord_id:
    joins.append(_JOIN_USERS_AUTH)
    filters.append("ap.element_name = ?")
    args.append("discord")
    filters.append("ua.element_identifier = ?")
    args.append(_normalise_discord_identifier(str(discord_id)))

  if not filters:
    raise ValueError("get_security_profile_v1 requires a selection filter")

  join_sql = "".join(_unique(joins))
  where_sql = " AND\n    ".join(filters)
  sql = f"{_BASE_QUERY}{join_sql}  WHERE {where_sql}\n  FOR JSON PATH, WITHOUT_ARRAY_WRAPPER;"
  return _make_operation(sql, args)
