"""MSSQL helpers for security identity linkage."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from server.registry.providers.mssql import run_exec, run_json_one
from server.registry.types import DBResponse
from server.modules.providers.database.mssql_provider.logic import transaction

__all__ = [
  "create_from_provider_v1",
  "get_any_by_provider_identifier_v1",
  "get_auth_provider_recid",
  "get_by_provider_identifier_v1",
  "get_user_by_email_v1",
  "link_provider_v1",
  "set_provider_v1",
  "soft_delete_account_v1",
  "unlink_provider_v1",
  "unlink_last_provider_v1",
]


async def get_auth_provider_recid(provider: str, *, cursor=None) -> int:
  """Return the auth provider recid for ``provider`` or raise a uniform error."""
  if cursor is not None:
    await cursor.execute(
      "SELECT recid FROM auth_providers WHERE element_name = ?;",
      (provider,),
    )
    row = await cursor.fetchone()
    if not row:
      raise ValueError(f"Unknown auth provider: {provider}")
    return row[0]
  res = await run_json_one(
    "SELECT recid FROM auth_providers WHERE element_name = ? FOR JSON PATH, WITHOUT_ARRAY_WRAPPER;",
    (provider,),
  )
  if not res.rows:
    raise ValueError(f"Unknown auth provider: {provider}")
  return res.rows[0]["recid"]


async def get_by_provider_identifier_v1(args: dict[str, Any]) -> DBResponse:
  provider = args["provider"]
  identifier = str(UUID(args["provider_identifier"]))
  sql = """
    SELECT TOP 1
      v.user_guid AS guid,
      v.display_name,
      v.email,
      v.credits,
      v.provider_name,
      v.provider_display,
      v.profile_image_base64 AS profile_image
    FROM vw_account_user_profile v
    JOIN users_auth ua ON ua.users_guid = v.user_guid AND ua.element_linked = 1
    JOIN auth_providers ap ON ap.recid = ua.providers_recid
    WHERE ap.element_name = ? AND ua.element_identifier = ?
    FOR JSON PATH, WITHOUT_ARRAY_WRAPPER;
  """
  return await run_json_one(sql, (provider, identifier))


async def get_any_by_provider_identifier_v1(args: dict[str, Any]) -> DBResponse:
  identifier = str(UUID(args["provider_identifier"]))
  sql = """
    SELECT TOP 1
      au.element_guid AS guid,
      au.element_soft_deleted_at
    FROM users_auth ua
    JOIN account_users au ON au.element_guid = ua.users_guid
    WHERE ua.element_identifier = ?
    FOR JSON PATH, WITHOUT_ARRAY_WRAPPER;
  """
  return await run_json_one(sql, (identifier,))


async def create_from_provider_v1(args: dict[str, Any]) -> DBResponse:
  from datetime import datetime, timezone
  from uuid import uuid4

  new_guid = str(uuid4())
  element_rotkey = ""
  element_rotkey_iat = datetime.now(timezone.utc)
  element_rotkey_exp = datetime.now(timezone.utc)
  provider = args["provider"]
  identifier = str(UUID(args["provider_identifier"]))
  provider_email = args["provider_email"]
  provider_displayname = args["provider_displayname"]
  provider_profileimg = args.get("provider_profile_image", "")

  ap_recid = await get_auth_provider_recid(provider)

  dup = await run_json_one(
    "SELECT users_guid FROM users_auth WHERE element_identifier = ? FOR JSON PATH, WITHOUT_ARRAY_WRAPPER;",
    (identifier,),
  )
  if dup.rows:
    existing_guid = dup.rows[0]["users_guid"]
    await run_exec(
      "UPDATE users_auth SET element_linked = 1, providers_recid = ? WHERE element_identifier = ?;",
      (ap_recid, identifier),
    )
    await run_exec(
      "UPDATE account_users SET providers_recid = ? WHERE element_guid = ?;",
      (ap_recid, existing_guid),
    )
    return await get_by_provider_identifier_v1({
      "provider": provider,
      "provider_identifier": identifier,
    })

  async with transaction() as cur:
    await cur.execute(
      """
        INSERT INTO account_users (element_guid, element_email, element_display, providers_recid, element_rotkey, element_rotkey_iat, element_rotkey_exp)
        VALUES (?, ?, ?, ?, ?, ?, ?);
      """,
      (new_guid, provider_email, provider_displayname, ap_recid, element_rotkey, element_rotkey_iat, element_rotkey_exp),
    )
    await cur.execute(
      "INSERT INTO users_auth (users_guid, providers_recid, element_identifier, element_linked) VALUES (?, ?, ?, 1);",
      (new_guid, ap_recid, identifier),
    )
    await cur.execute(
      "INSERT INTO users_credits (users_guid, element_credits) VALUES (?, ?);",
      (new_guid, 50),
    )
    await cur.execute(
      "INSERT INTO users_profileimg (users_guid, element_base64, providers_recid) VALUES (?, ?, ?);",
      (new_guid, provider_profileimg, ap_recid),
    )
    await cur.execute(
      "INSERT INTO users_roles (users_guid, element_roles) VALUES (?, ?);",
      (new_guid, 1),
    )

  return await get_by_provider_identifier_v1({
    "provider": provider,
    "provider_identifier": identifier,
  })


async def link_provider_v1(args: dict[str, Any]) -> DBResponse:
  guid = str(UUID(args["guid"]))
  provider = args["provider"]
  identifier = str(UUID(args["provider_identifier"]))
  ap_recid = await get_auth_provider_recid(provider)
  return await run_exec(
    """
    MERGE users_auth AS target
    USING (SELECT ? AS users_guid, ? AS providers_recid, ? AS element_identifier) AS source
    ON target.element_identifier = source.element_identifier
    WHEN MATCHED THEN
      UPDATE SET users_guid = source.users_guid, providers_recid = source.providers_recid, element_linked = 1
    WHEN NOT MATCHED THEN
      INSERT (users_guid, providers_recid, element_identifier, element_linked)
      VALUES (source.users_guid, source.providers_recid, source.element_identifier, 1);
    """,
    (guid, ap_recid, identifier),
  )


async def unlink_provider_v1(args: dict[str, Any]) -> DBResponse:
  guid = str(UUID(args["guid"]))
  provider = args["provider"]
  new_recid = args.get("new_provider_recid")
  async with transaction() as cur:
    await cur.execute(
      "SELECT providers_recid FROM account_users WHERE element_guid = ?;",
      (guid,),
    )
    row = await cur.fetchone()
    current_recid = row[0] if row else None
    provider_recid = await get_auth_provider_recid(provider, cursor=cur)
    await cur.execute(
      """
      UPDATE ua
      SET ua.element_linked = 0
      FROM users_auth ua
      JOIN auth_providers ap ON ap.recid = ua.providers_recid
      WHERE ua.users_guid = ? AND ap.element_name = ?;
      """,
      (guid, provider),
    )
    await cur.execute(
      "SELECT COUNT(*) AS cnt FROM users_auth WHERE users_guid = ? AND element_linked = 1;",
      (guid,),
    )
    row = await cur.fetchone()
    cnt = row[0] if row else 0
    if cnt == 0:
      await cur.execute(
        "UPDATE users_roles SET element_roles = 0 WHERE users_guid = ?;",
        (guid,),
      )
      await cur.execute(
        "UPDATE account_users SET providers_recid = NULL, element_display = '', element_email = '' WHERE element_guid = ?;",
        (guid,),
      )
    elif current_recid == provider_recid:
      if new_recid is not None:
        await cur.execute(
          "UPDATE account_users SET providers_recid = ? WHERE element_guid = ?;",
          (new_recid, guid),
        )
      else:
        await cur.execute(
          "UPDATE account_users SET providers_recid = NULL WHERE element_guid = ?;",
          (guid,),
        )
  return DBResponse(rows=[{"providers_remaining": cnt}], rowcount=1)


async def soft_delete_account_v1(args: dict[str, Any]) -> DBResponse:
  guid = str(UUID(args["guid"]))
  sql = """
    UPDATE account_users
    SET element_soft_deleted_at = SYSDATETIMEOFFSET()
    WHERE element_guid = ?;
  """
  return await run_exec(sql, (guid,))


async def get_user_by_email_v1(args: dict[str, Any]) -> DBResponse:
  email = args["email"]
  sql = """
    SELECT TOP 1
      element_guid AS guid
    FROM account_users
    WHERE element_email = ?
    FOR JSON PATH, WITHOUT_ARRAY_WRAPPER;
  """
  return await run_json_one(sql, (email,))


async def set_provider_v1(args: dict[str, Any]) -> DBResponse:
  guid = args["guid"]
  provider = args["provider"]
  ap_recid = await get_auth_provider_recid(provider)
  return await run_exec(
    "UPDATE account_users SET providers_recid = ? WHERE element_guid = ?;",
    (ap_recid, guid),
  )


async def unlink_last_provider_v1(args: dict[str, Any]) -> DBResponse:
  guid = args["guid"]
  provider = args["provider"]
  sql = "EXEC auth_unlink_last_provider @guid=?, @provider=?;"
  return await run_exec(sql, (guid, provider))


