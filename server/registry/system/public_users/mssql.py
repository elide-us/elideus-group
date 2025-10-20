"""Public user queries for MSSQL."""

from __future__ import annotations

from uuid import UUID

from server.registry.providers.mssql import run_json_many, run_json_one
from server.registry.types import DBResponse

from .model import GetProfileParams, GetPublishedFilesParams

__all__ = [
  "get_profile_v1",
  "get_published_files_v1",
]


async def get_profile_v1(args: GetProfileParams) -> DBResponse:
  guid = str(UUID(args["guid"]))
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
  return await run_json_one(sql, (guid,))


async def get_published_files_v1(args: GetPublishedFilesParams) -> DBResponse:
  guid = str(UUID(args["guid"]))
  sql = """
    SELECT
      usc.element_path AS path,
      usc.element_filename AS filename,
      usc.element_url AS url,
      st.element_mimetype AS content_type
    FROM users_storage_cache usc
    JOIN storage_types st ON st.recid = usc.types_recid
    WHERE usc.users_guid = ? AND usc.element_public = 1 AND usc.element_deleted = 0 AND ISNULL(usc.element_reported,0) = 0
    ORDER BY usc.element_created_on
    FOR JSON PATH;
  """
  return await run_json_many(sql, (guid,))
