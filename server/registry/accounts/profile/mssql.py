"""MSSQL profile helpers for account users."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from server.registry.providers.mssql import run_exec, run_json_one
from server.registry.types import DBResponse

from server.registry.security.identities.mssql import get_auth_provider_recid

__all__ = [
  "get_profile_v1",
  "set_display_v1",
  "set_optin_v1",
  "set_profile_image_v1",
  "set_roles_v1",
  "update_if_unedited_v1",
]


async def get_profile_v1(args: dict[str, Any]) -> DBResponse:
  guid = str(args["guid"])
  sql = """
    SELECT TOP 1
      v.user_guid AS guid,
      v.display_name,
      v.email,
      v.opt_in AS display_email,
      v.credits,
      v.profile_image_base64 AS profile_image,
      v.provider_name AS default_provider,
      (
        SELECT
          ap.element_name AS name,
          ap.element_display AS display
        FROM users_auth ua
        JOIN auth_providers ap ON ap.recid = ua.providers_recid
        WHERE ua.users_guid = v.user_guid AND ua.element_linked = 1
        FOR JSON PATH
      ) AS auth_providers
    FROM vw_account_user_profile v
    WHERE v.user_guid = ?
    FOR JSON PATH, WITHOUT_ARRAY_WRAPPER;
  """
  return await run_json_one(sql, (guid,))


async def set_display_v1(args: dict[str, Any]) -> DBResponse:
  guid = args["guid"]
  display_name = args["display_name"]
  sql = """
    UPDATE account_users
    SET element_display = ?
    WHERE element_guid = ?;
  """
  return await run_exec(sql, (display_name, guid))


async def set_optin_v1(args: dict[str, Any]) -> DBResponse:
  guid = args["guid"]
  display_email = args["display_email"]
  sql = """
    UPDATE account_users
    SET element_optin = ?
    WHERE element_guid = ?;
  """
  return await run_exec(sql, (display_email, guid))


async def update_if_unedited_v1(args: dict[str, Any]) -> DBResponse:
  guid = str(UUID(args["guid"]))
  email = args.get("email")
  display = args.get("display_name")
  res = await run_exec(
    """
    UPDATE account_users
    SET element_email = ?, element_display = ?
    WHERE element_guid = ? AND (element_email <> ? OR element_display <> ?);
    """,
    (email, display, guid, email, display),
  )
  if res.rowcount > 0:
    return await run_json_one(
      """
      SELECT element_display AS display_name, element_email AS email
      FROM account_users
      WHERE element_guid = ?
      FOR JSON PATH, WITHOUT_ARRAY_WRAPPER;
      """,
      (guid,),
    )
  return DBResponse()


async def set_roles_v1(args: dict[str, Any]) -> DBResponse:
  guid = args["guid"]
  roles = int(args["roles"])
  if roles == 0:
    return await run_exec("DELETE FROM users_roles WHERE users_guid = ?;", (guid,))
  res = await run_exec(
    "UPDATE users_roles SET element_roles = ? WHERE users_guid = ?;",
    (roles, guid),
  )
  if res.rowcount == 0:
    res = await run_exec(
      "INSERT INTO users_roles (users_guid, element_roles) VALUES (?, ?);",
      (guid, roles),
    )
  return res


async def set_profile_image_v1(args: dict[str, Any]) -> DBResponse:
  guid = args["guid"]
  image_b64 = args["image_b64"]
  provider = args["provider"]
  ap_recid = await get_auth_provider_recid(provider)
  rc = await run_exec(
    "UPDATE users_profileimg SET element_base64 = ?, providers_recid = ? WHERE users_guid = ?;",
    (image_b64, ap_recid, guid),
  )
  if rc.rowcount == 0:
    rc = await run_exec(
      "INSERT INTO users_profileimg (users_guid, element_base64, providers_recid) VALUES (?, ?, ?);",
      (guid, image_b64, ap_recid),
    )
  return rc
