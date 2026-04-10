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

  async def startup(self):
    self.db = self.app.state.db
    await self.db.on_ready()
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
