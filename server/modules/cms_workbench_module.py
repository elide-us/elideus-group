from __future__ import annotations

from typing import Any

from fastapi import FastAPI, HTTPException

from queryregistry.system.public import (
  get_cms_shell_tree_request,
  get_cms_tree_for_path_request,
  get_config_value_request,
  get_page_data_bindings_request,
)
from rpc.public.route.models import LoadPathResult1, PathNode1

from . import BaseModule
from .db_module import DbModule


class CmsWorkbenchModule(BaseModule):
  def __init__(self, app: FastAPI):
    super().__init__(app)
    self.db: DbModule | None = None
    self._role_guid_to_name: dict[str, str] = {}

  async def startup(self):
    self.db = self.app.state.db
    await self.db.on_ready()

    from queryregistry.providers.mssql import run_rows_many

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
