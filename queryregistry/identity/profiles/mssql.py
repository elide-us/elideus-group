"""MSSQL implementations for identity profile query registry services."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from queryregistry.models import DBResponse
from queryregistry.providers.mssql import run_exec, run_json_one

from .models import (
  ProfileReadRequestPayload,
  ProfileUpdateRequestPayload,
  UpdateIfUneditedRequestPayload,
)

__all__ = [
  "get_public_profile_v1",
  "get_roles_v1",
  "read_profile",
  "set_display_v1",
  "set_optin_v1",
  "set_profile_image_v1",
  "set_roles_v1",
  "update_if_unedited",
  "update_if_unedited_v1",
  "update_profile",
]


def _normalize_guid(guid: str) -> str:
  try:
    return str(UUID(guid))
  except (TypeError, ValueError):
    raise ValueError("guid must be a valid UUID") from None


async def _get_auth_provider_recid(provider: str) -> int:
  response = await run_json_one(
    "SELECT recid FROM auth_providers WHERE element_name = ? FOR JSON PATH, WITHOUT_ARRAY_WRAPPER;",
    (provider,),
  )
  if not response.rows:
    raise ValueError(f"Unknown auth provider: {provider}")
  return response.rows[0]["recid"]


async def read_profile(args: ProfileReadRequestPayload) -> DBResponse:
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
      JSON_QUERY(
        COALESCE(
          (
            SELECT
              ap.element_name AS name,
              ap.element_display AS display
            FROM users_auth ua
            JOIN auth_providers ap ON ap.recid = ua.providers_recid
            WHERE ua.users_guid = v.user_guid AND ua.element_linked = 1
            FOR JSON PATH
          ),
          '[]'
        )
      ) AS auth_providers
    FROM vw_account_user_profile v
    WHERE v.user_guid = ?
    FOR JSON PATH, WITHOUT_ARRAY_WRAPPER;
  """
  response = await run_json_one(sql, (guid,))
  return DBResponse(payload=response.payload)


async def get_roles_v1(args: dict[str, Any]) -> DBResponse:
  guid = str(args["guid"])
  response = await run_json_one(
    "SELECT element_roles AS roles FROM users_roles WHERE users_guid = ? FOR JSON PATH, WITHOUT_ARRAY_WRAPPER;",
    (guid,),
  )
  return DBResponse(payload=response.payload, rowcount=response.rowcount)


async def set_display_v1(args: dict[str, Any]) -> DBResponse:
  guid = str(args["guid"])
  display_name = args["display_name"]
  response = await run_exec(
    "UPDATE account_users SET element_display = ? WHERE element_guid = ?;",
    (display_name, guid),
  )
  return DBResponse(payload=response.payload, rowcount=response.rowcount)


async def set_optin_v1(args: dict[str, Any]) -> DBResponse:
  guid = str(args["guid"])
  display_email = int(bool(args["display_email"]))
  response = await run_exec(
    "UPDATE account_users SET element_optin = ? WHERE element_guid = ?;",
    (display_email, guid),
  )
  return DBResponse(payload=response.payload, rowcount=response.rowcount)


async def set_profile_image_v1(args: dict[str, Any]) -> DBResponse:
  guid = str(args["guid"])
  image_b64 = args["image_b64"]
  provider = str(args["provider"])
  ap_recid = await _get_auth_provider_recid(provider)
  response = await run_exec(
    "UPDATE users_profileimg SET element_base64 = ?, providers_recid = ? WHERE users_guid = ?;",
    (image_b64, ap_recid, guid),
  )
  if response.rowcount == 0:
    response = await run_exec(
      "INSERT INTO users_profileimg (users_guid, element_base64, providers_recid) VALUES (?, ?, ?);",
      (guid, image_b64, ap_recid),
    )
  return DBResponse(payload=response.payload, rowcount=response.rowcount)


async def set_roles_v1(args: dict[str, Any]) -> DBResponse:
  guid = str(args["guid"])
  roles = int(args["roles"])
  if roles == 0:
    response = await run_exec("DELETE FROM users_roles WHERE users_guid = ?;", (guid,))
    return DBResponse(payload=response.payload, rowcount=response.rowcount)
  response = await run_exec(
    "UPDATE users_roles SET element_roles = ? WHERE users_guid = ?;",
    (roles, guid),
  )
  if response.rowcount == 0:
    response = await run_exec(
      "INSERT INTO users_roles (users_guid, element_roles) VALUES (?, ?);",
      (guid, roles),
    )
  return DBResponse(payload=response.payload, rowcount=response.rowcount)


async def update_profile(args: ProfileUpdateRequestPayload) -> DBResponse:
  guid = _normalize_guid(args["guid"])
  rowcount = 0

  if "display_name" in args:
    display_name = args.get("display_name")
    res = await run_exec(
      "UPDATE account_users SET element_display = ? WHERE element_guid = ?;",
      (display_name, guid),
    )
    rowcount += res.rowcount

  if "display_email" in args:
    display_email = args.get("display_email")
    display_email_value = int(bool(display_email))
    res = await run_exec(
      "UPDATE account_users SET element_optin = ? WHERE element_guid = ?;",
      (display_email_value, guid),
    )
    rowcount += res.rowcount

  if "image_b64" in args:
    provider = args.get("provider")
    if not provider:
      raise ValueError("Profile image updates require provider")
    image_b64 = args.get("image_b64")
    ap_recid = await _get_auth_provider_recid(str(provider))
    res = await run_exec(
      "UPDATE users_profileimg SET element_base64 = ?, providers_recid = ? WHERE users_guid = ?;",
      (image_b64, ap_recid, guid),
    )
    rowcount += res.rowcount
    if res.rowcount == 0:
      res = await run_exec(
        "INSERT INTO users_profileimg (users_guid, element_base64, providers_recid) VALUES (?, ?, ?);",
        (guid, image_b64, ap_recid),
      )
      rowcount += res.rowcount

  return DBResponse(rowcount=rowcount)


async def update_if_unedited(args: UpdateIfUneditedRequestPayload) -> DBResponse:
  guid = _normalize_guid(args["guid"])
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
    response = await run_json_one(
      """
      SELECT element_display AS display_name, element_email AS email
      FROM account_users
      WHERE element_guid = ?
      FOR JSON PATH, WITHOUT_ARRAY_WRAPPER;
      """,
      (guid,),
    )
    return DBResponse(payload=response.payload, rowcount=response.rowcount)
  return DBResponse()


async def update_if_unedited_v1(args: dict[str, Any]) -> DBResponse:
  return await update_if_unedited(args)


async def get_public_profile_v1(args: dict[str, Any]) -> DBResponse:
  guid = _normalize_guid(str(args["guid"]))
  sql = """
    SELECT TOP 1
      au.element_display AS display_name,
      CASE WHEN au.element_optin = 1 THEN au.element_email ELSE NULL END AS email,
      up.element_base64 AS profile_image
    FROM account_users au
    LEFT JOIN users_profileimg up ON up.users_guid = au.element_guid
    WHERE au.element_guid = ?
    FOR JSON PATH, WITHOUT_ARRAY_WRAPPER;
  """
  response = await run_json_one(sql, (guid,))
  return DBResponse(payload=response.payload, rowcount=response.rowcount)
