"""MSSQL implementations for content public registry functions."""

from __future__ import annotations

from typing import Any, Dict

from server.modules.providers import DbRunMode
from server.modules.providers.database.mssql_provider.db_helpers import Operation

__all__ = [
  "get_public_files_v1",
  "list_public_v1",
  "list_reported_v1",
]


def list_public_v1(_: Dict[str, Any]) -> Operation:
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
  return Operation(DbRunMode.JSON_MANY, sql, ())


def get_public_files_v1(params: Dict[str, Any]) -> Operation:
  return list_public_v1(params)


def list_reported_v1(_: Dict[str, Any]) -> Operation:
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
  return Operation(DbRunMode.JSON_MANY, sql, ())
