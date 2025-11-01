"""MSSQL implementations for users public registry functions."""

from __future__ import annotations

from typing import Any, Dict

from server.registry.providers.mssql import run_json_many
from server.registry.types import DBResponse

__all__ = [
  "get_public_files_v1",
  "list_public_v1",
  "list_reported_v1",
]


async def list_public_v1(_: Dict[str, Any]) -> DBResponse:
  sql = """
    SELECT usc.users_guid AS user_guid,
           au.element_display AS display_name,
           usc.element_path AS path,
           usc.element_filename AS name,
           usc.element_url AS url,
           st.element_mimetype AS content_type
    FROM users_storage_cache usc
    JOIN account_users au ON au.element_guid = usc.users_guid
    JOIN storage_types st ON st.recid = usc.types_recid
    WHERE usc.element_public = 1 AND usc.element_deleted = 0 AND ISNULL(usc.element_reported,0) = 0
    ORDER BY usc.element_created_on
    FOR JSON PATH;
  """
  return await run_json_many(sql)


async def list_reported_v1(_: Dict[str, Any]) -> DBResponse:
  sql = """
    SELECT usc.users_guid AS user_guid,
           usc.element_path AS path,
           usc.element_filename AS name,
           usc.element_url AS url,
           st.element_mimetype AS content_type
    FROM users_storage_cache usc
    JOIN storage_types st ON st.recid = usc.types_recid
    WHERE usc.element_reported = 1 AND usc.element_deleted = 0
    ORDER BY usc.element_created_on
    FOR JSON PATH;
  """
  return await run_json_many(sql)


async def get_public_files_v1(args: Dict[str, Any]) -> DBResponse:
  return await list_public_v1(args)
