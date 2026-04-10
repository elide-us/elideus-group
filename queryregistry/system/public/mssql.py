"""MSSQL implementations for system public query registry services."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from queryregistry.providers.mssql import run_exec, run_json_many, run_rows_many

from queryregistry.models import DBResponse

__all__ = [
  "delete_route_v1",
  "get_cms_tree_for_path_v1",
  "get_config_value_v1",
  "get_home_links",
  "get_navbar_routes",
  "get_routes_v1",
  "list_frontend_pages_v1",
  "upsert_route_v1",
]


def _normalize_payload(rows: list[Any]) -> list[dict[str, Any]]:
  return [dict(row) for row in rows]


async def get_home_links(args: Mapping[str, Any]) -> DBResponse:
  role_mask = int(args.get("role_mask", 0) or 0)
  sql = """
    SELECT
      element_title AS title,
      element_url AS url,
      element_url AS path,
      element_title AS name,
      CAST(NULL AS nvarchar(256)) AS icon,
      element_sequence AS sequence
    FROM (
      SELECT
        element_title,
        element_url,
        element_sequence,
        0 AS element_roles
      FROM frontend_links
    ) AS links
    WHERE element_roles = 0 OR (element_roles & ?) = element_roles
    ORDER BY element_sequence
    FOR JSON PATH;
  """
  response = await run_json_many(sql, (role_mask,))
  return DBResponse(payload=_normalize_payload(response.rows))


async def get_navbar_routes(args: Mapping[str, Any]) -> DBResponse:
  return DBResponse(payload=[])


async def get_routes_v1(_: Mapping[str, Any]) -> DBResponse:
  return DBResponse(payload=[])


async def list_frontend_pages_v1(_: Mapping[str, Any]) -> DBResponse:
  return DBResponse(payload=[])


async def upsert_route_v1(args: Mapping[str, Any]) -> DBResponse:
  return DBResponse(payload=[], rowcount=0)


async def delete_route_v1(args: Mapping[str, Any]) -> DBResponse:
  return DBResponse(payload=[], rowcount=0)


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
    WHERE component IN ('Workbench', 'ContentPanel', 'StringControl')
    ORDER BY depth, sequence;
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
