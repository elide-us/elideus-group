# MIGRATION NOTE: DROP TABLE frontend_links (data migrated to system_objects_page_data_bindings)
"""MSSQL implementations for system public query registry services."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from queryregistry.providers.mssql import run_rows_many

from queryregistry.models import DBResponse

__all__ = [
  "delete_route_v1",
  "get_cms_shell_tree_v1",
  "get_cms_tree_for_path_v1",
  "get_config_value_v1",
  "get_page_data_bindings_v1",
  "get_routes_v1",
  "list_frontend_pages_v1",
  "upsert_route_v1",
]

async def get_routes_v1(_: Mapping[str, Any]) -> DBResponse:
  return DBResponse(payload=[])


async def list_frontend_pages_v1(_: Mapping[str, Any]) -> DBResponse:
  return DBResponse(payload=[])


async def upsert_route_v1(args: Mapping[str, Any]) -> DBResponse:
  return DBResponse(payload=[], rowcount=0)


async def delete_route_v1(args: Mapping[str, Any]) -> DBResponse:
  return DBResponse(payload=[], rowcount=0)

async def get_cms_shell_tree_v1(args: Mapping[str, Any]) -> DBResponse:
  """Walk the Workbench shell tree from the hardcoded root."""
  del args
  sql = """
    WITH tree AS (
      SELECT
        t.key_guid AS guid,
        t.ref_parent_guid AS parent_guid,
        t.pub_sequence AS sequence,
        t.pub_label AS label,
        t.pub_field_binding AS field_binding,
        c.pub_name AS component,
        c.pub_category AS category,
        0 AS depth
      FROM system_objects_component_tree t
      JOIN system_objects_components c ON c.key_guid = t.ref_component_guid
      WHERE t.key_guid = 'EE3B1A30-83A2-5990-96FE-99F8154138E3'

      UNION ALL

      SELECT
        child.key_guid AS guid,
        child.ref_parent_guid AS parent_guid,
        child.pub_sequence AS sequence,
        child.pub_label AS label,
        child.pub_field_binding AS field_binding,
        cc.pub_name AS component,
        cc.pub_category AS category,
        parent.depth + 1 AS depth
      FROM system_objects_component_tree child
      JOIN tree parent ON parent.guid = child.ref_parent_guid
      JOIN system_objects_components cc ON cc.key_guid = child.ref_component_guid
    )
    SELECT
      guid,
      parent_guid,
      sequence,
      label,
      field_binding,
      component,
      category,
      depth
    FROM tree
    ORDER BY depth, sequence;
  """
  response = await run_rows_many(sql, ())
  rows = [dict(row) for row in response.rows]
  return DBResponse(payload=rows, rowcount=len(rows))


async def get_cms_tree_for_path_v1(args: Mapping[str, Any]) -> DBResponse:
  path = str(args.get("path") or "")
  sql = """
    WITH root_route AS (
      SELECT TOP (1) ref_root_node_guid
      FROM system_objects_routes
      WHERE pub_path = ?
        AND pub_is_active = 1
    ),
    tree AS (
      SELECT
        t.key_guid AS guid,
        t.ref_parent_guid AS parent_guid,
        t.pub_sequence AS sequence,
        t.pub_label AS label,
        t.pub_field_binding AS field_binding,
        c.pub_name AS component,
        c.pub_category AS category,
        0 AS depth
      FROM system_objects_component_tree t
      JOIN root_route rr ON rr.ref_root_node_guid = t.key_guid
      JOIN system_objects_components c ON c.key_guid = t.ref_component_guid

      UNION ALL

      SELECT
        child.key_guid AS guid,
        child.ref_parent_guid AS parent_guid,
        child.pub_sequence AS sequence,
        child.pub_label AS label,
        child.pub_field_binding AS field_binding,
        cc.pub_name AS component,
        cc.pub_category AS category,
        parent.depth + 1 AS depth
      FROM system_objects_component_tree child
      JOIN tree parent ON parent.guid = child.ref_parent_guid
      JOIN system_objects_components cc ON cc.key_guid = child.ref_component_guid
    )
    SELECT
      guid,
      parent_guid,
      sequence,
      label,
      field_binding,
      component,
      category,
      depth
    FROM tree
    ORDER BY depth, sequence;
  """
  response = await run_rows_many(sql, (path,))
  rows = [dict(row) for row in response.rows]
  return DBResponse(payload=rows, rowcount=len(rows))


async def get_page_data_bindings_v1(args: Mapping[str, Any]) -> DBResponse:
  """Get all data bindings for the page associated with a route path."""
  path = str(args.get("path") or "")
  sql = """
    SELECT
      b.pub_alias AS alias,
      b.pub_source_type AS source_type,
      b.pub_literal_value AS literal_value,
      b.pub_config_key AS config_key,
      col.pub_name AS column_name,
      tbl.pub_name AS table_name
    FROM system_objects_page_data_bindings b
    JOIN system_objects_pages p ON p.key_guid = b.ref_page_guid
    JOIN system_objects_routes r ON r.ref_page_guid = p.key_guid
    LEFT JOIN system_objects_database_columns col ON col.key_guid = b.ref_column_guid
    LEFT JOIN system_objects_database_tables tbl ON tbl.key_guid = col.ref_table_guid
    WHERE r.pub_path = ?
      AND r.pub_is_active = 1
    ORDER BY b.pub_alias;
  """
  response = await run_rows_many(sql, (path,))
  rows = [dict(row) for row in response.rows]
  return DBResponse(payload=rows, rowcount=len(rows))


async def get_config_value_v1(args: Mapping[str, Any]) -> DBResponse:
  key = str(args.get("key") or "")
  sql = """
    SELECT element_key, element_value
    FROM system_config
    WHERE element_key = ?;
  """
  response = await run_rows_many(sql, (key,))
  rows = [dict(row) for row in response.rows]
  return DBResponse(payload=rows, rowcount=len(rows))
