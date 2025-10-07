from __future__ import annotations

from typing import Any

from fastapi import FastAPI

from server.modules import BaseModule
from server.modules.auth_module import AuthModule
from server.modules.db_module import DbModule
from server.registry.system.routes import (
  delete_route_request,
  get_routes_request,
  upsert_route_request,
)


class ServiceRoutesModule(BaseModule):
  def __init__(self, app: FastAPI):
    super().__init__(app)
    self.db: DbModule | None = None
    self.auth: AuthModule | None = None

  async def startup(self):
    self.db = self.app.state.db
    await self.db.on_ready()
    self.auth = self.app.state.auth
    await self.auth.on_ready()
    self.mark_ready()

  async def shutdown(self):
    self.db = None
    self.auth = None

  async def list_routes(self) -> list[dict[str, Any]]:
    assert self.db, "database module not initialised"
    assert self.auth, "auth module not initialised"
    request = get_routes_request()
    res = await self.db.run(request)
    routes: list[dict[str, Any]] = []
    for row in res.rows:
      mask = int(row.get("element_roles", 0))
      routes.append({
        "path": row.get("element_path", ""),
        "name": row.get("element_name", ""),
        "icon": row.get("element_icon"),
        "sequence": int(row.get("element_sequence", 0)),
        "required_roles": self.auth.mask_to_names(mask),
      })
    return routes

  async def upsert_route(
    self,
    *,
    path: str,
    name: str,
    icon: str | None,
    sequence: int,
    required_roles: list[str],
  ) -> dict[str, Any]:
    assert self.db, "database module not initialised"
    assert self.auth, "auth module not initialised"
    mask = self.auth.names_to_mask(required_roles)
    request = upsert_route_request(
      path=path,
      name=name,
      icon=icon,
      sequence=sequence,
      roles=mask,
    )
    await self.db.run(request)
    return {
      "path": path,
      "name": name,
      "icon": icon,
      "sequence": sequence,
      "required_roles": required_roles,
    }

  async def delete_route(self, path: str) -> dict[str, str]:
    assert self.db, "database module not initialised"
    request = delete_route_request(path)
    await self.db.run(request)
    return {"path": path}
