"""MSSQL implementations for users cache registry functions."""

from __future__ import annotations

from datetime import datetime, timezone
import logging
from typing import Any, Dict
from uuid import UUID

from server.registry.providers.mssql import (
  run_exec,
  run_json_many,
  run_json_one,
  transaction,
)
from server.registry.types import DBResponse

__all__ = [
  "count_rows_v1",
  "delete_folder_v1",
  "delete_v1",
  "list_v1",
  "list_public_v1",
  "list_reported_v1",
  "replace_user_v1",
  "set_public_v1",
  "set_reported_v1",
  "upsert_v1",
]


def _as_utc(value: Any | None) -> datetime | None:
  if value is None:
    return None
  if not isinstance(value, datetime):
    raise TypeError(f"Expected datetime value, received {type(value).__name__}")
  if value.tzinfo is None:
    return value.replace(tzinfo=timezone.utc)
  return value.astimezone(timezone.utc)


async def _get_storage_type_recid(mimetype: str, *, allow_folder: bool) -> int:
  async def _fetch_type(target: str) -> DBResponse:
    return await run_json_one(
      "SELECT recid FROM storage_types WHERE element_mimetype = ? FOR JSON PATH, WITHOUT_ARRAY_WRAPPER;",
      (target,),
    )

  res = await _fetch_type(mimetype)
  if res.rows:
    return res.rows[0]["recid"]

  if not allow_folder:
    raise ValueError(f"Unknown storage mimetype: {mimetype}")

  if mimetype == "path/folder":
    await run_exec(
      """
      MERGE storage_types AS target
      USING (SELECT 16 AS recid, 'path/folder' AS element_mimetype, 'Folder' AS element_displaytype) AS src
      ON target.element_mimetype = src.element_mimetype
      WHEN NOT MATCHED THEN
        INSERT (recid, element_mimetype, element_displaytype)
        VALUES (src.recid, src.element_mimetype, src.element_displaytype);
      """,
    )
    res = await _fetch_type(mimetype)
    if res.rows:
      return res.rows[0]["recid"]
    return 16

  fallback = await _fetch_type("application/octet-stream")
  if fallback.rows:
    return fallback.rows[0]["recid"]
  return 1


async def list_v1(args: Dict[str, Any]) -> DBResponse:
  user_guid = args["user_guid"]
  sql = """
    SELECT
      usc.element_path AS path,
      usc.element_filename AS filename,
      st.element_mimetype AS content_type,
      usc.element_url AS url,
      usc.element_public AS [public]
    FROM users_storage_cache usc
    JOIN storage_types st ON st.recid = usc.types_recid
    WHERE usc.users_guid = ? AND usc.element_deleted = 0
    ORDER BY usc.element_path, usc.element_filename
    FOR JSON PATH;
  """
  return await run_json_many(sql, (user_guid,))


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


async def replace_user_v1(args: Dict[str, Any]) -> DBResponse:
  user_guid = args["user_guid"]
  items: list[Dict[str, Any]] = args.get("items", [])
  async with transaction() as cur:
    await cur.execute("DELETE FROM users_storage_cache WHERE users_guid = ?;", (user_guid,))
    for item in items:
      path = item.get("path", "")
      filename = item.get("filename", "")
      mimetype = item.get("content_type", "application/octet-stream")
      type_recid = await _get_storage_type_recid(mimetype, allow_folder=False)
      await cur.execute(
        """INSERT INTO users_storage_cache
          (users_guid, types_recid, element_path, element_filename, element_public, element_modified_on, element_deleted)
          VALUES (?, ?, ?, ?, ?, NULL, 0);""",
        (user_guid, type_recid, path, filename, item.get("public", 0)),
      )
  return DBResponse(rows=[], rowcount=len(items))


async def upsert_v1(args: Dict[str, Any]) -> DBResponse:
  user_guid = args["user_guid"]
  path = args.get("path", "")
  filename = args.get("filename", "")
  mimetype = args.get("content_type", "application/octet-stream")
  public = args.get("public", 0)
  element_created_on = args.get("element_created_on")
  if element_created_on is None:
    element_created_on = datetime.now(timezone.utc)
  element_created_on = _as_utc(element_created_on)
  element_modified_on = _as_utc(args.get("element_modified_on"))
  url = args.get("url")
  reported = args.get("reported", 0)
  moderation_recid = args.get("moderation_recid")
  type_recid = await _get_storage_type_recid(mimetype, allow_folder=True)
  sql = """
    MERGE users_storage_cache AS target
    USING (SELECT ? AS users_guid, ? AS types_recid, ? AS element_path, ? AS element_filename,
                  ? AS element_public, ? AS element_created_on, ? AS element_modified_on,
                  ? AS element_deleted, ? AS element_url, ? AS element_reported, ? AS moderation_recid) AS src
    ON target.users_guid = src.users_guid AND target.element_path = src.element_path AND target.element_filename = src.element_filename
    WHEN MATCHED THEN UPDATE SET
      types_recid = src.types_recid,
      element_public = src.element_public,
      element_created_on = src.element_created_on,
      element_modified_on = src.element_modified_on,
      element_deleted = src.element_deleted,
      element_url = src.element_url,
      element_reported = src.element_reported,
      moderation_recid = src.moderation_recid
    WHEN NOT MATCHED THEN
      INSERT (users_guid, types_recid, element_path, element_filename, element_public,
              element_created_on, element_modified_on, element_deleted, element_url,
              element_reported, moderation_recid)
      VALUES (src.users_guid, src.types_recid, src.element_path, src.element_filename,
              src.element_public, src.element_created_on, src.element_modified_on,
              src.element_deleted, src.element_url, src.element_reported, src.moderation_recid);
  """
  params = (
    user_guid,
    type_recid,
    path,
    filename,
    public,
    element_created_on,
    element_modified_on,
    0,
    url,
    reported,
    moderation_recid,
  )
  rc = await run_exec(sql, params)
  if rc.rowcount == 0:
    logging.error(
      "[MSSQL] storage_cache_upsert affected 0 rows for %s/%s",
      path or ".",
      filename,
    )
  return rc


async def delete_v1(args: Dict[str, Any]) -> DBResponse:
  user_guid = args["user_guid"]
  path = args.get("path", "")
  filename = args.get("filename", "")
  sql = """
    DELETE FROM users_storage_cache
    WHERE users_guid = ? AND element_path = ? AND element_filename = ?;
  """
  return await run_exec(sql, (user_guid, path, filename))


async def delete_folder_v1(args: Dict[str, Any]) -> DBResponse:
  user_guid = args["user_guid"]
  path = args.get("path", "").lstrip("/")
  parent, name = path.rsplit("/", 1) if "/" in path else ("", path)
  like = f"{path}/%" if path else "%"
  sql = """
    DELETE FROM users_storage_cache
    WHERE users_guid = ? AND (
      (element_path = ? AND element_filename = ?)
      OR element_path = ?
      OR element_path LIKE ?
    );
  """
  return await run_exec(sql, (user_guid, parent, name, path, like))


async def set_public_v1(args: Dict[str, Any]) -> DBResponse:
  guid = str(UUID(args["user_guid"]))
  name = args.get("name")
  if name:
    path, filename = name.rsplit("/", 1) if "/" in name else ("", name)
  else:
    path = args.get("path", "")
    filename = args.get("filename", "")
  flag_value = 1 if args.get("public") else 0
  sql = """
    UPDATE users_storage_cache
    SET element_public = ?
    WHERE users_guid = ? AND element_path = ? AND element_filename = ?;
  """
  return await run_exec(sql, (flag_value, guid, path, filename))


async def set_reported_v1(args: Dict[str, Any]) -> DBResponse:
  guid = str(UUID(args["user_guid"]))
  path = args.get("path", "")
  filename = args.get("filename", "")
  reported = 1 if args.get("reported") else 0
  sql = """
    UPDATE users_storage_cache
    SET element_reported = ?
    WHERE users_guid = ? AND element_path = ? AND element_filename = ?;
  """
  return await run_exec(sql, (reported, guid, path, filename))


async def count_rows_v1(_: Dict[str, Any]) -> DBResponse:
  sql = """
    SELECT COUNT(*) AS count
    FROM users_storage_cache
    WHERE element_deleted = 0
    FOR JSON PATH, WITHOUT_ARRAY_WRAPPER;
  """
  return await run_json_one(sql)
