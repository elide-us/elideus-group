"""MSSQL implementations for content pages query registry services."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from queryregistry.models import DBResponse
from queryregistry.providers.mssql import run_exec, run_json_many, run_json_one

__all__ = [
  "create_v1",
  "create_version_v1",
  "delete_v1",
  "get_by_slug_v1",
  "get_v1",
  "get_version_v1",
  "list_v1",
  "list_versions_v1",
  "update_v1",
]


async def list_v1(args: Mapping[str, Any]) -> DBResponse:
  where_clauses: list[str] = []
  params: list[Any] = []

  if args.get("page_type") is not None:
    where_clauses.append("element_page_type = ?")
    params.append(args["page_type"])

  if args.get("is_active") is not None:
    where_clauses.append("element_is_active = ?")
    params.append(args["is_active"])

  where_sql = ""
  if where_clauses:
    where_sql = f"WHERE {' AND '.join(where_clauses)}"

  sql = f"""
    SELECT
      recid,
      element_guid,
      element_slug,
      element_title,
      element_page_type,
      element_category,
      element_roles,
      element_is_active,
      element_is_pinned,
      element_sequence,
      element_created_by,
      element_modified_by,
      element_created_on,
      element_modified_on
    FROM content_pages
    {where_sql}
    ORDER BY element_is_pinned DESC, element_sequence ASC, element_created_on DESC
    FOR JSON PATH, INCLUDE_NULL_VALUES;
  """
  return await run_json_many(sql, tuple(params))


async def get_v1(args: Mapping[str, Any]) -> DBResponse:
  sql = """
    SELECT
      p.recid,
      p.element_guid,
      p.element_slug,
      p.element_title,
      p.element_page_type,
      p.element_category,
      p.element_roles,
      p.element_is_active,
      p.element_is_pinned,
      p.element_sequence,
      p.element_created_by,
      p.element_modified_by,
      p.element_created_on,
      p.element_modified_on,
      v.element_version,
      v.element_content,
      v.element_summary,
      v.version_created_by,
      v.version_created_on
    FROM content_pages p
    OUTER APPLY (
      SELECT TOP 1
        element_version,
        element_content,
        element_summary,
        element_created_by AS version_created_by,
        element_created_on AS version_created_on
      FROM content_page_versions
      WHERE pages_recid = p.recid
      ORDER BY element_version DESC
    ) AS v
    WHERE p.recid = ?
    FOR JSON PATH, WITHOUT_ARRAY_WRAPPER, INCLUDE_NULL_VALUES;
  """
  return await run_json_one(sql, (args["recid"],))


async def get_by_slug_v1(args: Mapping[str, Any]) -> DBResponse:
  sql = """
    SELECT
      p.recid,
      p.element_guid,
      p.element_slug,
      p.element_title,
      p.element_page_type,
      p.element_category,
      p.element_roles,
      p.element_is_active,
      p.element_is_pinned,
      p.element_sequence,
      p.element_created_by,
      p.element_modified_by,
      p.element_created_on,
      p.element_modified_on,
      v.element_version,
      v.element_content,
      v.element_summary,
      v.version_created_by,
      v.version_created_on
    FROM content_pages p
    OUTER APPLY (
      SELECT TOP 1
        element_version,
        element_content,
        element_summary,
        element_created_by AS version_created_by,
        element_created_on AS version_created_on
      FROM content_page_versions
      WHERE pages_recid = p.recid
      ORDER BY element_version DESC
    ) AS v
    WHERE p.element_slug = ?
    FOR JSON PATH, WITHOUT_ARRAY_WRAPPER, INCLUDE_NULL_VALUES;
  """
  return await run_json_one(sql, (args["slug"],))


async def create_v1(args: Mapping[str, Any]) -> DBResponse:
  sql = """
    SET NOCOUNT ON;

    DECLARE @pages TABLE (recid bigint);

    INSERT INTO content_pages (
      element_slug,
      element_title,
      element_page_type,
      element_category,
      element_roles,
      element_is_active,
      element_is_pinned,
      element_sequence,
      element_created_by,
      element_modified_by,
      element_created_on,
      element_modified_on
    )
    OUTPUT inserted.recid INTO @pages
    VALUES (?, ?, ?, ?, ?, 1, ?, ?, TRY_CAST(? AS UNIQUEIDENTIFIER), TRY_CAST(? AS UNIQUEIDENTIFIER), SYSUTCDATETIME(), SYSUTCDATETIME());

    INSERT INTO content_page_versions (
      pages_recid,
      element_version,
      element_content,
      element_summary,
      element_created_by,
      element_created_on
    )
    SELECT
      p.recid,
      1,
      ?,
      ?,
      TRY_CAST(? AS UNIQUEIDENTIFIER),
      SYSUTCDATETIME()
    FROM @pages p;

    SELECT
      cp.recid,
      cp.element_guid,
      cp.element_slug,
      cp.element_title,
      cp.element_page_type,
      cp.element_category,
      cp.element_roles,
      cp.element_is_active,
      cp.element_is_pinned,
      cp.element_sequence,
      cp.element_created_by,
      cp.element_modified_by,
      cp.element_created_on,
      cp.element_modified_on,
      v.element_version,
      v.element_content,
      v.element_summary,
      v.element_created_by AS version_created_by,
      v.element_created_on AS version_created_on
    FROM content_pages cp
    INNER JOIN @pages p ON p.recid = cp.recid
    INNER JOIN content_page_versions v
      ON v.pages_recid = cp.recid
      AND v.element_version = 1
    FOR JSON PATH, WITHOUT_ARRAY_WRAPPER, INCLUDE_NULL_VALUES;
  """
  params = (
    args["slug"],
    args["title"],
    args["page_type"],
    args.get("category"),
    args["roles"],
    args["is_pinned"],
    args["sequence"],
    args["created_by"],
    args["created_by"],
    args["content"],
    args.get("summary"),
    args["created_by"],
  )
  return await run_json_one(sql, params)


async def update_v1(args: Mapping[str, Any]) -> DBResponse:
  set_clauses: list[str] = []
  params: list[Any] = []

  updates = (
    ("title", "element_title"),
    ("page_type", "element_page_type"),
    ("category", "element_category"),
    ("roles", "element_roles"),
    ("is_active", "element_is_active"),
    ("is_pinned", "element_is_pinned"),
    ("sequence", "element_sequence"),
  )

  for payload_key, field_name in updates:
    if args.get(payload_key) is not None:
      set_clauses.append(f"{field_name} = ?")
      params.append(args[payload_key])

  set_clauses.append("element_modified_by = TRY_CAST(? AS UNIQUEIDENTIFIER)")
  params.append(args["modified_by"])
  set_clauses.append("element_modified_on = SYSUTCDATETIME()")

  sql = f"""
    SET NOCOUNT ON;

    DECLARE @result TABLE (
      recid bigint,
      element_guid uniqueidentifier,
      element_slug nvarchar(256),
      element_title nvarchar(512),
      element_page_type nvarchar(64),
      element_category nvarchar(128),
      element_roles bigint,
      element_is_active bit,
      element_is_pinned bit,
      element_sequence int,
      element_created_by uniqueidentifier,
      element_modified_by uniqueidentifier,
      element_created_on datetimeoffset,
      element_modified_on datetimeoffset
    );

    UPDATE content_pages
    SET
      {', '.join(set_clauses)}
    OUTPUT
      inserted.recid,
      inserted.element_guid,
      inserted.element_slug,
      inserted.element_title,
      inserted.element_page_type,
      inserted.element_category,
      inserted.element_roles,
      inserted.element_is_active,
      inserted.element_is_pinned,
      inserted.element_sequence,
      inserted.element_created_by,
      inserted.element_modified_by,
      inserted.element_created_on,
      inserted.element_modified_on
    INTO @result
    WHERE recid = ?;

    SELECT *
    FROM @result
    FOR JSON PATH, WITHOUT_ARRAY_WRAPPER, INCLUDE_NULL_VALUES;
  """
  params.append(args["recid"])
  return await run_json_one(sql, tuple(params))


async def delete_v1(args: Mapping[str, Any]) -> DBResponse:
  sql = """
    SET NOCOUNT ON;

    UPDATE content_pages
    SET
      element_is_active = 0,
      element_modified_by = TRY_CAST(? AS UNIQUEIDENTIFIER),
      element_modified_on = SYSUTCDATETIME()
    WHERE recid = ?;
  """
  return await run_exec(sql, (args["modified_by"], args["recid"]))


async def create_version_v1(args: Mapping[str, Any]) -> DBResponse:
  sql = """
    SET NOCOUNT ON;

    DECLARE @result TABLE (
      recid bigint,
      pages_recid bigint,
      element_version int,
      element_content nvarchar(max),
      element_summary nvarchar(512),
      element_created_by uniqueidentifier,
      element_created_on datetimeoffset
    );

    INSERT INTO content_page_versions (
      pages_recid,
      element_version,
      element_content,
      element_summary,
      element_created_by,
      element_created_on
    )
    OUTPUT
      inserted.recid,
      inserted.pages_recid,
      inserted.element_version,
      inserted.element_content,
      inserted.element_summary,
      inserted.element_created_by,
      inserted.element_created_on
    INTO @result
    VALUES (
      ?,
      (SELECT ISNULL(MAX(element_version), 0) + 1 FROM content_page_versions WHERE pages_recid = ?),
      ?,
      ?,
      TRY_CAST(? AS UNIQUEIDENTIFIER),
      SYSUTCDATETIME()
    );

    UPDATE content_pages
    SET
      element_modified_by = TRY_CAST(? AS UNIQUEIDENTIFIER),
      element_modified_on = SYSUTCDATETIME()
    WHERE recid = ?;

    SELECT *
    FROM @result
    FOR JSON PATH, WITHOUT_ARRAY_WRAPPER, INCLUDE_NULL_VALUES;
  """
  params = (
    args["pages_recid"],
    args["pages_recid"],
    args["content"],
    args.get("summary"),
    args["created_by"],
    args["created_by"],
    args["pages_recid"],
  )
  return await run_json_one(sql, params)


async def list_versions_v1(args: Mapping[str, Any]) -> DBResponse:
  sql = """
    SELECT
      recid,
      pages_recid,
      element_version,
      element_summary,
      element_created_by,
      element_created_on
    FROM content_page_versions
    WHERE pages_recid = ?
    ORDER BY element_version DESC
    FOR JSON PATH, INCLUDE_NULL_VALUES;
  """
  return await run_json_many(sql, (args["pages_recid"],))


async def get_version_v1(args: Mapping[str, Any]) -> DBResponse:
  where_clauses: list[str] = []
  params: list[Any] = []

  if args.get("recid") is not None:
    where_clauses.append("recid = ?")
    params.append(args["recid"])
  elif args.get("pages_recid") is not None and args.get("version") is not None:
    where_clauses.append("pages_recid = ?")
    where_clauses.append("element_version = ?")
    params.extend((args["pages_recid"], args["version"]))

  sql = f"""
    SELECT
      recid,
      pages_recid,
      element_version,
      element_content,
      element_summary,
      element_created_by,
      element_created_on
    FROM content_page_versions
    WHERE {' AND '.join(where_clauses) if where_clauses else '1 = 0'}
    FOR JSON PATH, WITHOUT_ARRAY_WRAPPER, INCLUDE_NULL_VALUES;
  """
  return await run_json_one(sql, tuple(params))
