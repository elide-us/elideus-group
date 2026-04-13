from __future__ import annotations

import json
from typing import Any

from fastapi import FastAPI, HTTPException

from queryregistry.system.public import (
  get_cms_shell_tree_request,
  get_cms_tree_for_path_request,
  get_config_value_request,
  get_page_data_bindings_request,
)
from rpc.public.route.models import LoadPathResult1, PathNode1
from server.helpers.strings import deterministic_guid

from . import BaseModule
from .db_module import DbModule


class CmsWorkbenchModule(BaseModule):
  MODULE_GUID = "CF85FB11-5981-56B7-8E43-9D453E611D43"

  def __init__(self, app: FastAPI):
    super().__init__(app)
    self.db: DbModule | None = None
    self._role_guid_to_name: dict[str, str] = {}
    self._queries: dict[str, str] = {}

  async def startup(self):
    self.db = self.app.state.db
    await self.db.on_ready()

    from queryregistry.providers.mssql import run_json_many, run_rows_many

    role_result = await run_rows_many(
      """
      SELECT key_guid, pub_name
      FROM system_auth_roles;
      """,
      (),
    )
    self._role_guid_to_name = {
      str(row.get("key_guid") or "").upper(): str(row.get("pub_name") or "")
      for row in role_result.rows
      if row.get("key_guid")
    }

    query_sql = """
      SELECT pub_name, pub_query_text
      FROM system_objects_queries
      WHERE ref_module_guid = TRY_CAST(? AS UNIQUEIDENTIFIER)
        AND pub_is_active = 1
      FOR JSON PATH, INCLUDE_NULL_VALUES;
    """
    loaded = await run_json_many(query_sql, (self.MODULE_GUID,))
    rows = loaded.rows if loaded else []
    self._queries = {
      str(row.get("pub_name")): str(row.get("pub_query_text"))
      for row in rows
      if row.get("pub_name") and row.get("pub_query_text")
    }

    import logging

    logging.info("[CmsWorkbenchModule] Loaded %s data-driven queries", len(self._queries))

    self.mark_ready()

  async def shutdown(self):
    self.db = None

  @staticmethod
  def _build_tree(rows: list[dict[str, Any]]) -> tuple[str | None, dict[str, PathNode1]]:
    """Build a PathNode1 tree from flat CTE result rows.

    Returns (root_guid, nodes_by_guid).
    """
    nodes_by_guid: dict[str, PathNode1] = {}
    root_guid: str | None = None

    for row in rows:
      guid = str(row.get("guid") or "")
      if not guid:
        continue
      if row.get("parent_guid") is None:
        root_guid = guid
      nodes_by_guid[guid] = PathNode1(
        guid=guid,
        component=str(row.get("component") or ""),
        category=str(row.get("category") or ""),
        label=row.get("label"),
        fieldBinding=row.get("field_binding"),
        sequence=int(row.get("sequence") or 0),
        children=[],
      )

    for row in rows:
      guid = str(row.get("guid") or "")
      parent_guid = row.get("parent_guid")
      if not guid or parent_guid is None:
        continue
      child_node = nodes_by_guid.get(guid)
      parent_node = nodes_by_guid.get(str(parent_guid))
      if child_node and parent_node:
        parent_node.children.append(child_node)

    for node in nodes_by_guid.values():
      node.children.sort(key=lambda child: child.sequence)

    return root_guid, nodes_by_guid

  async def load_path(self, path: str, user_context: dict[str, Any] | None) -> LoadPathResult1:
    del user_context
    assert self.db

    shell_res = await self.db.run(get_cms_shell_tree_request())
    shell_rows = [dict(row) for row in shell_res.rows]
    if not shell_rows:
      raise HTTPException(status_code=500, detail="Workbench shell tree not found")

    shell_root_guid, shell_nodes = self._build_tree(shell_rows)
    if not shell_root_guid or shell_root_guid not in shell_nodes:
      raise HTTPException(status_code=500, detail="Workbench shell tree missing root node")

    page_res = await self.db.run(get_cms_tree_for_path_request(path))
    page_rows = [dict(row) for row in page_res.rows]
    if not page_rows:
      raise HTTPException(status_code=404, detail=f"No CMS route found for path '{path}'")

    page_root_guid, page_nodes = self._build_tree(page_rows)
    if not page_root_guid or page_root_guid not in page_nodes:
      raise HTTPException(status_code=500, detail="Page tree missing root node")

    content_panel: PathNode1 | None = None
    for node in shell_nodes.values():
      if node.component == "ContentPanel":
        content_panel = node
        break

    if not content_panel:
      raise HTTPException(status_code=500, detail="Shell tree missing ContentPanel")

    content_panel.children.append(page_nodes[page_root_guid])
    content_panel.children.sort(key=lambda child: child.sequence)

    component_data: dict[str, Any] = {}
    bindings_res = await self.db.run(get_page_data_bindings_request(path))
    bindings_rows = [dict(row) for row in bindings_res.rows]

    for binding in bindings_rows:
      alias = binding.get("alias")
      source_type = binding.get("source_type", "")
      if not alias:
        continue

      if source_type == "literal":
        component_data[alias] = binding.get("literal_value")

      elif source_type == "config":
        config_key = binding.get("config_key")
        if config_key:
          config_res = await self.db.run(get_config_value_request(config_key))
          config_rows = [dict(row) for row in config_res.rows]
          if config_rows:
            component_data[alias] = config_rows[0].get("element_value")

      elif source_type == "column":
        pass

    return LoadPathResult1(pathData=shell_nodes[shell_root_guid], componentData=component_data)

  async def read_navigation(self, user_role_names: list[str] | None = None) -> list[dict[str, Any]]:
    """Return active routes filtered by user roles."""
    assert self.db

    from queryregistry.providers.mssql import run_rows_many

    result = await run_rows_many(
      """
      SELECT
        r.pub_path AS path,
        r.pub_title AS title,
        r.pub_icon AS icon,
        r.pub_sequence AS sequence,
        r.ref_parent_route_guid AS parent_route_guid,
        r.ref_required_role_guid AS required_role_guid
      FROM system_objects_routes r
      WHERE r.pub_is_active = 1
      ORDER BY r.pub_sequence;
      """,
      (),
    )
    rows = [dict(row) for row in result.rows]

    role_names_upper = {
      str(name).upper()
      for name in (user_role_names or [])
      if isinstance(name, str) and name.strip()
    }
    filtered: list[dict[str, Any]] = []

    for row in rows:
      required_guid = row.get("required_role_guid")
      if required_guid:
        role_name = self._role_guid_to_name.get(str(required_guid).upper())
        if not role_name or role_name.upper() not in role_names_upper:
          continue

      filtered.append(
        {
          "path": str(row.get("path") or ""),
          "title": str(row.get("title") or ""),
          "icon": row.get("icon"),
          "sequence": int(row.get("sequence") or 0),
          "parentRouteGuid": row.get("parent_route_guid"),
        }
      )

    return filtered

  @staticmethod
  def _quote_ident(identifier: str) -> str:
    return "[" + identifier.replace("]", "]]") + "]"

  async def _run_query(self, query_name: str, params: tuple = ()) -> Any:
    from queryregistry.providers.mssql import run_json_many, run_json_one

    sql = self._queries.get(query_name)
    if not sql:
      raise HTTPException(status_code=500, detail=f"Query not found: {query_name}")
    if "WITHOUT_ARRAY_WRAPPER" in sql:
      return await run_json_one(sql, params)
    return await run_json_many(sql, params)

  async def read_object_tree_categories(self) -> list[dict[str, Any]]:
    result = await self._run_query("cms.object_tree.get_categories")
    return [dict(row) for row in (result.rows if result else [])]

  async def read_object_tree_children(
    self,
    category_guid: str,
    table_guid: str | None = None,
  ) -> list[dict[str, Any]]:
    if table_guid:
      result = await self._run_query(
        "cms.object_tree.get_table_columns",
        (table_guid,),
      )
      return [dict(row) for row in (result.rows if result else [])]

    tables_result = await self._run_query(
      "cms.object_tree.get_category_tables",
      (category_guid,),
    )
    tables = [dict(row) for row in (tables_result.rows if tables_result else [])]
    root_table = next((table for table in tables if table.get("isRoot")), None)
    if not root_table:
      return []

    root_table_guid = str(root_table.get("guid") or "")
    root_table_name = str(root_table.get("name") or "")
    if not root_table_guid:
      return []

    try:
      detail = await self.read_object_tree_detail(root_table_guid, max_rows=500)
    except Exception:
      return []

    children: list[dict[str, Any]] = []
    for row in detail.get("rows", []):
      key_guid = str(row.get("key_guid") or "")
      if not key_guid:
        continue
      name = (
        row.get("pub_name")
        or row.get("pub_display")
        or row.get("pub_path")
        or row.get("pub_title")
        or key_guid[:8]
      )
      children.append(
        {
          "guid": key_guid,
          "name": str(name),
          "tableName": root_table_name,
          "isRoot": False,
          "sequence": row.get("pub_sequence") or row.get("pub_ordinal") or 0,
        }
      )

    return children

  async def read_object_tree_detail(self, table_guid: str, max_rows: int = 100) -> dict[str, Any]:
    from queryregistry.providers.mssql import run_rows_many, run_rows_one

    bounded_max_rows = max(1, min(int(max_rows or 100), 1000))

    resolved = await run_rows_one(
      """
      SELECT TOP 1 pub_name, pub_schema
      FROM system_objects_database_tables
      WHERE key_guid = ?;
      """,
      (table_guid,),
    )
    row = dict(resolved.rows[0]) if resolved.rows else None
    if not row:
      raise HTTPException(status_code=404, detail="Object tree table not found")

    table_name = str(row.get("pub_name") or "")
    schema_name = str(row.get("pub_schema") or "")
    if not table_name or not schema_name:
      raise HTTPException(status_code=400, detail="Object tree table metadata incomplete")

    safe_schema = self._quote_ident(schema_name)
    safe_table = self._quote_ident(table_name)
    payload_result = await run_rows_many(
      f"""
      SELECT
        (
          SELECT TOP (?) *
          FROM {safe_schema}.{safe_table}
          FOR JSON PATH
        ) AS rows_json,
        (
          SELECT COUNT(1)
          FROM {safe_schema}.{safe_table}
        ) AS row_count;
      """,
      (bounded_max_rows,),
    )
    payload_row = dict(payload_result.rows[0]) if payload_result.rows else {}
    rows_json = payload_row.get("rows_json")

    rows: list[dict[str, Any]] = []
    if isinstance(rows_json, str) and rows_json.strip():
      parsed = json.loads(rows_json)
      if isinstance(parsed, list):
        rows = parsed

    return {
      "tableName": table_name,
      "schema": schema_name,
      "rowCount": int(payload_row.get("row_count") or 0),
      "rows": rows,
    }

  async def upsert_database_table(self, key_guid: str | None, name: str, schema: str) -> dict[str, bool]:
    await self._run_query(
      "cms.database.upsert_table",
      (key_guid, name, schema),
    )
    return {"ok": True}

  async def delete_database_table(self, key_guid: str) -> dict[str, bool]:
    await self._run_query(
      "cms.database.delete_table",
      (key_guid,),
    )
    return {"ok": True}

  async def upsert_database_column(
    self,
    key_guid: str | None,
    table_guid: str,
    type_guid: str,
    name: str,
    ordinal: int,
    is_nullable: bool,
    is_primary_key: bool,
    is_identity: bool,
    default_value: str | None = None,
    max_length: int | None = None,
  ) -> dict[str, bool]:
    await self._run_query(
      "cms.database.upsert_column",
      (
        key_guid,
        table_guid,
        type_guid,
        name,
        ordinal,
        is_nullable,
        is_primary_key,
        is_identity,
        default_value,
        max_length,
      ),
    )
    return {"ok": True}

  async def delete_database_column(self, key_guid: str) -> dict[str, bool]:
    await self._run_query(
      "cms.database.delete_column",
      (key_guid,),
    )
    return {"ok": True}

  async def upsert_type(
    self,
    key_guid: str | None,
    name: str,
    mssql_type: str,
    postgresql_type: str | None,
    mysql_type: str | None,
    python_type: str,
    typescript_type: str,
    json_type: str,
    odbc_type_code: int | None,
    max_length: int | None,
    notes: str | None,
  ) -> dict[str, bool]:
    await self._run_query(
      "cms.types.upsert_type",
      (
        key_guid,
        name,
        mssql_type,
        postgresql_type,
        mysql_type,
        python_type,
        typescript_type,
        json_type,
        odbc_type_code,
        max_length,
        notes,
      ),
    )
    return {"ok": True}

  async def delete_type(self, key_guid: str) -> dict[str, bool]:
    await self._run_query(
      "cms.types.delete_type",
      (key_guid,),
    )
    return {"ok": True}

  async def get_type_controls(self, type_guid: str) -> list[dict[str, Any]]:
    result = await self._run_query(
      "cms.types.get_type_controls",
      (type_guid,),
    )
    return [dict(row) for row in (result.rows if result else [])]

  async def get_module_methods(self, module_guid: str) -> list[dict[str, Any]]:
    """Return methods for a module with joined model names."""
    result = await self._run_query("cms.modules.get_methods", (module_guid,))
    return [dict(row) for row in (result.rows if result else [])]

  async def upsert_module(
    self,
    key_guid: str,
    description: str | None,
    is_active: bool,
  ) -> dict[str, bool]:
    """Update module description and is_active. Modules are code-loaded - no INSERT."""
    await self._run_query(
      "cms.modules.upsert_module",
      (description, is_active, key_guid),
    )
    return {"ok": True}

  async def upsert_module_method(
    self,
    key_guid: str | None,
    module_guid: str,
    name: str,
    description: str | None,
    is_active: bool,
  ) -> dict[str, bool]:
    """Insert or update a module method."""
    await self._run_query(
      "cms.modules.upsert_method",
      (key_guid, module_guid, name, description, is_active),
    )
    return {"ok": True}

  async def delete_module_method(self, key_guid: str) -> dict[str, bool]:
    """Delete a module method by GUID."""
    await self._run_query("cms.modules.delete_method", (key_guid,))
    return {"ok": True}

  async def get_method_contract(self, method_guid: str) -> list[dict[str, Any]]:
    """Return contract info for a method, if one exists."""
    result = await self._run_query("cms.modules.get_method_contract", (method_guid,))
    return [dict(row) for row in (result.rows if result else [])]


  async def get_page_tree(self, page_guid: str) -> list[dict[str, Any]]:
    """Return the recursive component tree for a page."""
    result = await self._run_query("cms.pages.get_page_tree", (page_guid,))
    return [dict(row) for row in (result.rows if result else [])]

  async def list_components(self) -> list[dict[str, Any]]:
    """Return all registered components for the component picker."""
    result = await self._run_query("cms.pages.list_components")
    return [dict(row) for row in (result.rows if result else [])]

  async def get_component_detail(self, component_guid: str) -> dict[str, Any]:
    """Return full detail for a single component."""
    result = await self._run_query(
      "cms.components.get_component_detail",
      (component_guid,),
    )
    row = dict(result.rows[0]) if result and result.rows else {}
    return row

  async def upsert_component(
    self,
    key_guid: str,
    description: str | None,
    default_type_guid: str | None,
  ) -> dict[str, bool]:
    """Update component description and default type."""
    await self._run_query(
      "cms.components.upsert_component",
      (description, default_type_guid, key_guid),
    )
    return {"ok": True}

  async def create_tree_node(
    self,
    page_guid: str,
    parent_guid: str | None,
    component_guid: str,
    label: str | None = None,
    field_binding: str | None = None,
    sequence: int = 0,
  ) -> dict[str, Any]:
    """Insert a new component tree node with a deterministic GUID.

    Computes the tree path by resolving the parent chain, then generates
    uuid5(NS, 'tree:{full_path}') as the key_guid.
    """
    comp_result = await self._run_query("cms.pages.list_components")
    comp_rows = [dict(row) for row in (comp_result.rows if comp_result else [])]
    comp_name = next(
      (row.get("name") for row in comp_rows if str(row.get("guid", "")).upper() == component_guid.upper()),
      "Unknown",
    )

    segment = comp_name
    if field_binding:
      segment = f"{comp_name}:{field_binding}"
    elif label:
      segment = f"{comp_name}:{label}"

    if parent_guid:
      tree_result = await self._run_query("cms.pages.get_page_tree", (page_guid,))
      tree_rows = [dict(row) for row in (tree_result.rows if tree_result else [])]
      parent_path = self._resolve_tree_path(tree_rows, parent_guid)
      full_path = f"{parent_path}.{segment}" if parent_path else segment
    else:
      full_path = segment

    key_guid = deterministic_guid("tree", full_path)

    result = await self._run_query(
      "cms.pages.create_tree_node",
      (key_guid, parent_guid, component_guid, label, field_binding, sequence, page_guid, key_guid),
    )
    row = dict(result.rows[0]) if result and result.rows else {}
    return {"ok": True, "keyGuid": row.get("key_guid", key_guid)}

  @staticmethod
  def _resolve_tree_path(tree_rows: list[dict[str, Any]], target_guid: str) -> str:
    """Walk the parent chain to build the full dot-delimited tree path."""
    by_guid: dict[str, dict[str, Any]] = {}
    for row in tree_rows:
      guid = str(row.get("guid", "")).upper()
      if guid:
        by_guid[guid] = row

    segments: list[str] = []
    current = target_guid.upper()
    while current and current in by_guid:
      row = by_guid[current]
      name = str(row.get("component_name", "Unknown"))
      binding = row.get("field_binding")
      label = row.get("label")
      if binding:
        segments.append(f"{name}:{binding}")
      elif label:
        segments.append(f"{name}:{label}")
      else:
        segments.append(name)
      parent = row.get("parent_guid")
      current = str(parent).upper() if parent else ""

    segments.reverse()
    return ".".join(segments)

  async def update_tree_node(
    self,
    key_guid: str,
    label: str | None = None,
    field_binding: str | None = None,
    sequence: int | None = None,
    rpc_operation: str | None = None,
    rpc_contract: str | None = None,
    component_guid: str | None = None,
  ) -> dict[str, bool]:
    """Update tree node properties. COALESCE in SQL preserves existing when None."""
    await self._run_query(
      "cms.pages.update_tree_node",
      (label, field_binding, sequence, rpc_operation, rpc_contract, component_guid, key_guid),
    )
    return {"ok": True}

  async def delete_tree_node(self, key_guid: str) -> dict[str, bool]:
    """Delete a tree node and cascade all descendants."""
    await self._run_query("cms.pages.delete_tree_node", (key_guid,))
    return {"ok": True}

  async def move_tree_node(
    self,
    key_guid: str,
    new_parent_guid: str | None,
    new_sequence: int,
  ) -> dict[str, bool]:
    """Move a node to a new parent and/or sequence."""
    await self._run_query(
      "cms.pages.move_tree_node",
      (new_parent_guid, new_sequence, key_guid),
    )
    return {"ok": True}
