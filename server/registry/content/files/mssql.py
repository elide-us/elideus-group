"""MSSQL implementations for content files registry functions."""

from __future__ import annotations

from typing import Any, Dict
from uuid import UUID

from server.modules.providers import DbRunMode
from server.modules.providers.database.mssql_provider.db_helpers import Operation

__all__ = [
  "set_gallery_v1",
]


def set_gallery_v1(args: Dict[str, Any]) -> Operation:
  guid = str(UUID(args["user_guid"]))
  name = args.get("name")
  if name:
    path, filename = name.rsplit("/", 1) if "/" in name else ("", name)
  else:
    path = args.get("path", "")
    filename = args.get("filename", "")
  gallery = 1 if args.get("gallery") else 0
  sql = """
    UPDATE users_storage_cache
    SET element_public = ?
    WHERE users_guid = ? AND element_path = ? AND element_filename = ?;
  """
  return Operation(DbRunMode.EXEC, sql, (gallery, guid, path, filename))
