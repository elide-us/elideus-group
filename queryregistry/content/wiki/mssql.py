"""MSSQL implementations for content wiki query registry services."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from queryregistry.models import DBResponse
from queryregistry.providers.mssql import run_exec, run_json_many, run_json_one

__all__ = [
  "create_v1",
  "create_version_v1",
  "delete_v1",
  "get_by_route_context_v1",
  "get_by_slug_v1",
  "get_v1",
  "get_version_v1",
  "list_children_v1",
  "list_v1",
  "list_versions_v1",
  "update_v1",
]


async def list_v1(args: Mapping[str, Any]) -> DBResponse:
  where_clauses: list[str] = []
  params: list[Any] = []

  if args.get("parent_slug") is not None:
    where_clauses.append("element_parent_slug = ?")
    params.append(args["parent_slug"])

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
      element_parent_slug,
      element_route_context,
      element_roles,
      element_is_active,
      element_sequence,
      element_created_by,
      element_modified_by,
      element_created_on,
      element_modified_on
    FROM content_wiki
    {where_sql}
    ORDER BY element_sequence ASC, element_created_on DESC
    FOR JSON PATH, INCLUDE_NULL_VALUES;
  """
  return await run_json_many(sql, tuple(params))


async def get_v1(args: Mapping[str, Any]) -> DBResponse:
  sql = """
    SELECT
      w.recid,
      w.element_guid,
      w.element_slug,
      w.element_title,
      w.element_parent_slug,
      w.element_route_context,
      w.element_roles,
      w.element_is_active,
      w.element_sequence,
      w.element_created_by,
      w.element_modified_by,
      w.element_created_on,
      w.element_modified_on,
      v.element_version,
      v.element_content,
      v.element_edit_summary,
      v.version_created_by,
      v.version_created_on
    FROM content_wiki w
    OUTER APPLY (
      SELECT TOP 1
        element_version,
        element_content,
        element_edit_summary,
        element_created_by AS version_created_by,
        element_created_on AS version_created_on
      FROM content_wiki_versions
      WHERE wiki_recid = w.recid
      ORDER BY element_version DESC
    ) AS v
    WHERE w.recid = ?
    FOR JSON PATH, WITHOUT_ARRAY_WRAPPER, INCLUDE_NULL_VALUES;
  """
  return await run_json_one(sql, (args["recid"],))


async def get_by_slug_v1(args: Mapping[str, Any]) -> DBResponse:
  sql = """
    SELECT
      w.recid,
      w.element_guid,
      w.element_slug,
      w.element_title,
      w.element_parent_slug,
      w.element_route_context,
      w.element_roles,
      w.element_is_active,
      w.element_sequence,
      w.element_created_by,
      w.element_modified_by,
      w.element_created_on,
      w.element_modified_on,
      v.element_version,
      v.element_content,
      v.element_edit_summary,
      v.version_created_by,
      v.version_created_on
    FROM content_wiki w
    OUTER APPLY (
      SELECT TOP 1
        element_version,
        element_content,
        element_edit_summary,
        element_created_by AS version_created_by,
        element_created_on AS version_created_on
      FROM content_wiki_versions
      WHERE wiki_recid = w.recid
      ORDER BY element_version DESC
    ) AS v
    WHERE w.element_slug = ?
    FOR JSON PATH, WITHOUT_ARRAY_WRAPPER, INCLUDE_NULL_VALUES;
  """
  return await run_json_one(sql, (args["slug"],))


async def get_by_route_context_v1(args: Mapping[str, Any]) -> DBResponse:
  sql = """
    SELECT
      w.recid,
      w.element_guid,
      w.element_slug,
      w.element_title,
      w.element_parent_slug,
      w.element_route_context,
      w.element_roles,
      w.element_is_active,
      w.element_sequence,
      w.element_created_by,
      w.element_modified_by,
      w.element_created_on,
      w.element_modified_on,
      v.element_version,
      v.element_content,
      v.element_edit_summary,
      v.version_created_by,
      v.version_created_on
    FROM content_wiki w
    OUTER APPLY (
      SELECT TOP 1
        element_version,
        element_content,
        element_edit_summary,
        element_created_by AS version_created_by,
        element_created_on AS version_created_on
      FROM content_wiki_versions
      WHERE wiki_recid = w.recid
      ORDER BY element_version DESC
    ) AS v
    WHERE w.element_route_context = ?
    FOR JSON PATH, WITHOUT_ARRAY_WRAPPER, INCLUDE_NULL_VALUES;
  """
  return await run_json_one(sql, (args["route_context"],))


async def list_children_v1(args: Mapping[str, Any]) -> DBResponse:
  sql = """
    SELECT
      recid,
      element_guid,
      element_slug,
      element_title,
      element_parent_slug,
      element_route_context,
      element_roles,
      element_is_active,
      element_sequence,
      element_created_by,
      element_modified_by,
      element_created_on,
      element_modified_on
    FROM content_wiki
    WHERE element_parent_slug = ?
      AND element_is_active = 1
    ORDER BY element_sequence ASC
    FOR JSON PATH, INCLUDE_NULL_VALUES;
  """
  return await run_json_many(sql, (args["parent_slug"],))


async def create_v1(args: Mapping[str, Any]) -> DBResponse:
  sql = """
    SET NOCOUNT ON;

    DECLARE @wiki TABLE (recid bigint);

    INSERT INTO content_wiki (
      element_slug,
      element_title,
      element_parent_slug,
      element_route_context,
      element_roles,
      element_is_active,
      element_sequence,
      element_created_by,
      element_modified_by,
      element_created_on,
      element_modified_on
    )
    OUTPUT inserted.recid INTO @wiki
    VALUES (
      ?,
      ?,
      ?,
      ?,
      ?,
      1,
      ?,
      TRY_CAST(? AS UNIQUEIDENTIFIER),
      TRY_CAST(? AS UNIQUEIDENTIFIER),
      SYSUTCDATETIME(),
      SYSUTCDATETIME()
    );

    INSERT INTO content_wiki_versions (
      wiki_recid,
      element_version,
      element_content,
      element_edit_summary,
      element_created_by,
      element_created_on
    )
    SELECT
      w.recid,
      1,
      ?,
      ?,
      TRY_CAST(? AS UNIQUEIDENTIFIER),
      SYSUTCDATETIME()
    FROM @wiki w;

    SELECT
      cw.recid,
      cw.element_guid,
      cw.element_slug,
      cw.element_title,
      cw.element_parent_slug,
      cw.element_route_context,
      cw.element_roles,
      cw.element_is_active,
      cw.element_sequence,
      cw.element_created_by,
      cw.element_modified_by,
      cw.element_created_on,
      cw.element_modified_on,
      v.element_version,
      v.element_content,
      v.element_edit_summary,
      v.element_created_by AS version_created_by,
      v.element_created_on AS version_created_on
    FROM content_wiki cw
    INNER JOIN @wiki w ON w.recid = cw.recid
    INNER JOIN content_wiki_versions v
      ON v.wiki_recid = cw.recid
      AND v.element_version = 1
    FOR JSON PATH, WITHOUT_ARRAY_WRAPPER, INCLUDE_NULL_VALUES;
  """
  params = (
    args["slug"],
    args["title"],
    args.get("parent_slug"),
    args.get("route_context"),
    args["roles"],
    args["sequence"],
    args["created_by"],
    args["created_by"],
    args["content"],
    args.get("edit_summary"),
    args["created_by"],
  )
  return await run_json_one(sql, params)


async def update_v1(args: Mapping[str, Any]) -> DBResponse:
  set_clauses: list[str] = []
  params: list[Any] = []

  updates = (
    ("title", "element_title"),
    ("parent_slug", "element_parent_slug"),
    ("route_context", "element_route_context"),
    ("roles", "element_roles"),
    ("is_active", "element_is_active"),
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
      element_slug nvarchar(512),
      element_title nvarchar(512),
      element_parent_slug nvarchar(512),
      element_route_context nvarchar(256),
      element_roles bigint,
      element_is_active bit,
      element_sequence int,
      element_created_by uniqueidentifier,
      element_modified_by uniqueidentifier,
      element_created_on datetimeoffset,
      element_modified_on datetimeoffset
    );

    UPDATE content_wiki
    SET
      {', '.join(set_clauses)}
    OUTPUT
      inserted.recid,
      inserted.element_guid,
      inserted.element_slug,
      inserted.element_title,
      inserted.element_parent_slug,
      inserted.element_route_context,
      inserted.element_roles,
      inserted.element_is_active,
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

    UPDATE content_wiki
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
      wiki_recid bigint,
      element_version int,
      element_content nvarchar(max),
      element_edit_summary nvarchar(512),
      element_created_by uniqueidentifier,
      element_created_on datetimeoffset
    );

    INSERT INTO content_wiki_versions (
      wiki_recid,
      element_version,
      element_content,
      element_edit_summary,
      element_created_by,
      element_created_on
    )
    OUTPUT
      inserted.recid,
      inserted.wiki_recid,
      inserted.element_version,
      inserted.element_content,
      inserted.element_edit_summary,
      inserted.element_created_by,
      inserted.element_created_on
    INTO @result
    VALUES (
      ?,
      (SELECT ISNULL(MAX(element_version), 0) + 1 FROM content_wiki_versions WHERE wiki_recid = ?),
      ?,
      ?,
      TRY_CAST(? AS UNIQUEIDENTIFIER),
      SYSUTCDATETIME()
    );

    UPDATE content_wiki
    SET
      element_modified_by = TRY_CAST(? AS UNIQUEIDENTIFIER),
      element_modified_on = SYSUTCDATETIME()
    WHERE recid = ?;

    SELECT *
    FROM @result
    FOR JSON PATH, WITHOUT_ARRAY_WRAPPER, INCLUDE_NULL_VALUES;
  """
  params = (
    args["wiki_recid"],
    args["wiki_recid"],
    args["content"],
    args.get("edit_summary"),
    args["created_by"],
    args["created_by"],
    args["wiki_recid"],
  )
  return await run_json_one(sql, params)


async def list_versions_v1(args: Mapping[str, Any]) -> DBResponse:
  sql = """
    SELECT
      recid,
      wiki_recid,
      element_version,
      element_edit_summary,
      element_created_by,
      element_created_on
    FROM content_wiki_versions
    WHERE wiki_recid = ?
    ORDER BY element_version DESC
    FOR JSON PATH, INCLUDE_NULL_VALUES;
  """
  return await run_json_many(sql, (args["wiki_recid"],))


async def get_version_v1(args: Mapping[str, Any]) -> DBResponse:
  where_clauses: list[str] = []
  params: list[Any] = []

  if args.get("recid") is not None:
    where_clauses.append("recid = ?")
    params.append(args["recid"])
  elif args.get("wiki_recid") is not None and args.get("version") is not None:
    where_clauses.append("wiki_recid = ?")
    where_clauses.append("element_version = ?")
    params.extend((args["wiki_recid"], args["version"]))

  sql = f"""
    SELECT
      recid,
      wiki_recid,
      element_version,
      element_content,
      element_edit_summary,
      element_created_by,
      element_created_on
    FROM content_wiki_versions
    WHERE {' AND '.join(where_clauses) if where_clauses else '1 = 0'}
    FOR JSON PATH, WITHOUT_ARRAY_WRAPPER, INCLUDE_NULL_VALUES;
  """
  return await run_json_one(sql, tuple(params))
