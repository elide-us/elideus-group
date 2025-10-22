"""MSSQL helpers for account session management."""

from __future__ import annotations

from typing import Any
from uuid import UUID, uuid4

from server.registry.account.providers.mssql import get_auth_provider_recid
from server.registry.providers.mssql import (
  run_exec,
  run_json_many,
  run_json_one,
  transaction,
)
from server.registry.types import DBResponse

__all__ = [
  "create_session_v1",
  "get_rotkey_v1",
  "get_security_snapshot_v1",
  "list_snapshots_v1",
  "revoke_all_device_tokens_v1",
  "revoke_device_token_v1",
  "revoke_provider_tokens_v1",
  "set_rotkey_v1",
  "update_device_token_v1",
  "update_session_v1",
]


async def create_session_v1(args: dict[str, Any]) -> DBResponse:
  access_token = args["access_token"]
  expires = args["expires"]
  fingerprint = args.get("fingerprint")
  user_agent = args.get("user_agent")
  ip_address = args.get("ip_address")
  user_guid = args["user_guid"]
  provider = args["provider"]

  if not fingerprint:
    raise ValueError("Missing device fingerprint")

  async with transaction() as cur:
    provider_recid = await get_auth_provider_recid(provider, cursor=cur)

    await cur.execute(
      "SELECT element_guid FROM users_sessions WHERE users_guid = ?;",
      (user_guid,),
    )
    row = await cur.fetchone()
    if row:
      session_guid = row[0]
      await cur.execute(
        "UPDATE users_sessions SET element_created_at = SYSDATETIMEOFFSET() WHERE users_guid = ?;",
        (user_guid,),
      )
    else:
      session_guid = str(uuid4())
      await cur.execute(
        """
          INSERT INTO users_sessions (element_guid, users_guid, element_created_at)
          VALUES (?, ?, SYSDATETIMEOFFSET());
        """,
        (session_guid, user_guid),
      )

    await cur.execute(
      "SELECT element_guid FROM sessions_devices WHERE sessions_guid = ? AND element_device_fingerprint = ?;",
      (session_guid, fingerprint),
    )
    row = await cur.fetchone()
    if row:
      device_guid = row[0]
      await cur.execute(
        """
          UPDATE sessions_devices
          SET element_token = ?, element_token_iat = SYSDATETIMEOFFSET(), element_token_exp = ?,
              element_user_agent = ?, element_ip_last_seen = ?, element_revoked_at = NULL
          WHERE element_guid = ?;
        """,
        (access_token, expires, user_agent, ip_address, device_guid),
      )
    else:
      device_guid = str(uuid4())
      await cur.execute(
        """
          INSERT INTO sessions_devices (
            element_guid, sessions_guid, providers_recid, element_token, element_token_iat, element_token_exp,
            element_device_fingerprint, element_user_agent, element_ip_last_seen
          ) VALUES (?, ?, ?, ?, SYSDATETIMEOFFSET(), ?, ?, ?, ?);
        """,
        (
          device_guid,
          session_guid,
          provider_recid,
          access_token,
          expires,
          fingerprint,
          user_agent,
          ip_address,
        ),
      )

  return DBResponse(rows=[{"session_guid": session_guid, "device_guid": device_guid}], rowcount=1)


async def update_session_v1(args: dict[str, Any]) -> DBResponse:
  token = args["access_token"]
  ip_address = args.get("ip_address")
  user_agent = args.get("user_agent")
  sql = """
      UPDATE sessions_devices
      SET element_ip_last_seen = ?, element_user_agent = ?
      WHERE element_token = ?;
    """
  return await run_exec(sql, (ip_address, user_agent, token))


async def update_device_token_v1(args: dict[str, Any]) -> DBResponse:
  device_guid = str(UUID(args["device_guid"]))
  token = args["access_token"]
  sql = """
    UPDATE sessions_devices
    SET element_token = ?
    WHERE element_guid = ?;
  """
  return await run_exec(sql, (token, device_guid))


async def revoke_device_token_v1(args: dict[str, Any]) -> DBResponse:
  token = args["access_token"]
  sql = """
    UPDATE sessions_devices
    SET element_revoked_at = SYSDATETIMEOFFSET()
    WHERE element_token = ?;
  """
  return await run_exec(sql, (token,))


async def revoke_all_device_tokens_v1(args: dict[str, Any]) -> DBResponse:
  guid = str(UUID(args["guid"]))
  sql = """
    UPDATE sd
    SET element_revoked_at = SYSDATETIMEOFFSET()
    FROM sessions_devices sd
    JOIN users_sessions us ON us.element_guid = sd.sessions_guid
    WHERE us.users_guid = ?;
  """
  return await run_exec(sql, (guid,))


async def revoke_provider_tokens_v1(args: dict[str, Any]) -> DBResponse:
  guid = str(UUID(args["guid"]))
  provider = args["provider"]
  sql = """
    UPDATE sd
    SET element_revoked_at = SYSDATETIMEOFFSET()
    FROM sessions_devices sd
    JOIN users_sessions us ON us.element_guid = sd.sessions_guid
    JOIN auth_providers ap ON ap.recid = sd.providers_recid
    WHERE us.users_guid = ? AND ap.element_name = ?;
  """
  return await run_exec(sql, (guid, provider))


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


async def list_snapshots_v1(params: dict[str, Any]) -> DBResponse:
  guid = str(UUID(params["guid"]))
  sql = """
    SELECT
      aus.user_guid,
      aus.user_roles,
      aus.user_created_on,
      aus.user_modified_on,
      aus.element_rotkey,
      aus.element_rotkey_iat,
      aus.element_rotkey_exp,
      aus.session_guid,
      aus.session_created_on,
      aus.session_modified_on,
      aus.device_guid,
      aus.device_created_on,
      aus.device_modified_on,
      aus.element_token,
      aus.element_token_iat,
      aus.element_token_exp,
      aus.element_revoked_at,
      aus.element_device_fingerprint,
      aus.element_user_agent,
      aus.element_ip_last_seen
    FROM vw_account_user_sessions aus
    WHERE aus.user_guid = ?
    ORDER BY aus.session_created_on DESC, aus.device_created_on DESC
    FOR JSON PATH;
  """
  return await run_json_many(sql, (guid,))


async def get_security_snapshot_v1(params: dict[str, Any]) -> DBResponse:
  guid = str(UUID(params["guid"]))
  sql = """
    SELECT
      aus.user_guid,
      aus.element_rotkey,
      aus.element_rotkey_iat,
      aus.element_rotkey_exp,
      aus.session_guid,
      aus.device_guid,
      aus.element_token,
      aus.element_token_iat,
      aus.element_token_exp,
      aus.element_revoked_at,
      aus.element_device_fingerprint,
      aus.element_user_agent,
      aus.element_ip_last_seen
    FROM vw_account_user_security aus
    WHERE aus.user_guid = ?
    ORDER BY aus.element_token_iat DESC
    FOR JSON PATH;
  """
  return await run_json_many(sql, (guid,))
