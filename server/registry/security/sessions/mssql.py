"""MSSQL helpers for security session workflows."""

from __future__ import annotations

from typing import Any
from uuid import UUID, uuid4

from server.registry.providers.mssql import run_exec
from server.registry.types import DBResponse
from server.modules.providers.database.mssql_provider.logic import transaction

from server.registry.security.identities.mssql import get_auth_provider_recid

__all__ = [
  "create_session_v1",
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


async def set_rotkey_v1(args: dict[str, Any]) -> DBResponse:
  guid = args["guid"]
  rotkey = args["rotkey"]
  iat = args["iat"]
  exp = args["exp"]
  sql = """
    UPDATE account_users
    SET element_rotkey = ?, element_rotkey_iat = ?, element_rotkey_exp = ?
    WHERE element_guid = ?;
  """
  return await run_exec(sql, (rotkey, iat, exp, guid))
