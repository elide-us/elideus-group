from __future__ import annotations

from typing import Any

from fastapi import FastAPI, HTTPException

from queryregistry.system.public import (
  get_cms_tree_for_path_request,
  get_config_value_request,
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

  async def load_path(self, path: str, user_context: dict[str, Any] | None) -> LoadPathResult1:
    del user_context
    assert self.db

    tree_res = await self.db.run(get_cms_tree_for_path_request(path))
    tree_rows = [dict(row) for row in tree_res.rows]
    if not tree_rows:
      raise HTTPException(status_code=404, detail=f"No CMS route found for path '{path}'")

    nodes_by_guid: dict[str, PathNode1] = {}
    root_guid: str | None = None

    for row in tree_rows:
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

    for row in tree_rows:
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

    if not root_guid or root_guid not in nodes_by_guid:
      raise HTTPException(status_code=500, detail="CMS route tree missing root node")

    component_data: dict[str, Any] = {}
    for node in nodes_by_guid.values():
      if node.fieldBinding != "version":
        continue
      version_res = await self.db.run(get_config_value_request("Version"))
      version_rows = [dict(row) for row in version_res.rows]
      if version_rows:
        component_data["version"] = version_rows[0].get("element_value")

    return LoadPathResult1(pathData=nodes_by_guid[root_guid], componentData=component_data)
