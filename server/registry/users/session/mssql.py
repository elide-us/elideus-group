"""MSSQL-backed handlers for user session registry operations."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from server.registry.providers.mssql import run_exec, run_json_one
from server.registry.types import DBResponse

__all__ = [
  "get_rotkey_v1",
  "set_rotkey_v1",
]


async def get_rotkey_v1(params: dict[str, Any]) -> DBResponse:
  guid = str(UUID(params["guid"]))
  sql = """
    SELECT TOP 1
      au.element_guid AS user_guid,
      au.element_rotkey AS rotkey,
      au.element_rotkey_iat AS rotkey_iat,
      au.element_rotkey_exp AS rotkey_exp,
      ap.element_name AS provider_name,
      ap.element_display AS provider_display,
      latest.session_guid,
      latest.session_created_on,
      latest.session_modified_on,
      latest.device_guid,
      latest.device_token,
      latest.device_token_iat,
      latest.device_token_exp,
      latest.revoked_at,
      latest.device_fingerprint,
      latest.user_agent,
      latest.ip_last_seen
    FROM account_users au
    LEFT JOIN auth_providers ap ON ap.recid = au.providers_recid
    OUTER APPLY (
      SELECT TOP 1
        us.element_guid AS session_guid,
        us.element_created_on AS session_created_on,
        us.element_modified_on AS session_modified_on,
        sd.element_guid AS device_guid,
        sd.element_token AS device_token,
        sd.element_token_iat AS device_token_iat,
        sd.element_token_exp AS device_token_exp,
        sd.element_revoked_at AS revoked_at,
        sd.element_device_fingerprint AS device_fingerprint,
        sd.element_user_agent AS user_agent,
        sd.element_ip_last_seen AS ip_last_seen
      FROM users_sessions us
      JOIN sessions_devices sd ON sd.sessions_guid = us.element_guid
      WHERE us.users_guid = au.element_guid
      ORDER BY sd.element_token_iat DESC
    ) latest
    WHERE au.element_guid = ?
    FOR JSON PATH, WITHOUT_ARRAY_WRAPPER;
  """
  return await run_json_one(sql, (guid,))


async def set_rotkey_v1(args: dict[str, Any]) -> DBResponse:
  guid = str(UUID(args["guid"]))
  rotkey = args["rotkey"]
  iat = args["iat"]
  exp = args["exp"]
  sql = """
    UPDATE account_users
    SET element_rotkey = ?, element_rotkey_iat = ?, element_rotkey_exp = ?
    WHERE element_guid = ?;
  """
  return await run_exec(sql, (rotkey, iat, exp, guid))
