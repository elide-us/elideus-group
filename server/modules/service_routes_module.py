from __future__ import annotations

import logging
from fastapi import FastAPI

from queryregistry.system.public import (
  delete_route_request,
  get_routes_request,
  list_frontend_pages_request,
  upsert_route_request,
)
from queryregistry.system.public.models import RoutePathParams, UpsertRouteParams

from . import BaseModule
from .auth_module import AuthModule
from .db_module import DbModule


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

  async def get_routes(
    self,
    user_guid: str,
    roles: list[str],
  ) -> list[dict]:
    logging.debug(
      "[service_routes_get_routes_v1] user=%s roles=%s",
      user_guid,
      roles,
    )
    if not self.db or not self.auth:
      raise RuntimeError("ServiceRoutesModule not ready")
    res = await self.db.run(get_routes_request())
    routes: list[dict] = []
    for row in res.rows:
      mask = int(row.get("element_roles", 0))
      required_roles = self.auth.mask_to_names(mask)
      routes.append({
        "path": row.get("element_path", ""),
        "name": row.get("element_name", ""),
        "icon": row.get("element_icon"),
        "sequence": int(row.get("element_sequence", 0)),
        "required_roles": required_roles,
      })
    logging.debug(
      "[service_routes_get_routes_v1] returning %d routes",
      len(routes),
    )
    return routes

  async def list_frontend_pages(self) -> list[dict]:
    if not self.db:
      raise RuntimeError("ServiceRoutesModule not ready")
    res = await self.db.run(list_frontend_pages_request())
    return [dict(row) for row in (res.rows or [])]

  async def upsert_route(
    self,
    user_guid: str,
    roles: list[str],
    route: dict,
  ) -> dict:
    logging.debug(
      "[service_routes_upsert_route_v1] user=%s roles=%s payload=%s",
      user_guid,
      roles,
      route,
    )
    if not self.db or not self.auth:
      raise RuntimeError("ServiceRoutesModule not ready")
    required_roles = route.get("required_roles", [])
    mask = self.auth.names_to_mask(required_roles)
    await self.db.run(
      upsert_route_request(UpsertRouteParams(
        path=route["path"],
        name=route["name"],
        icon=route.get("icon"),
        sequence=route.get("sequence", 0),
        roles=mask,
      ))
    )
    logging.debug(
      "[service_routes_upsert_route_v1] upserted route %s",
      route["path"],
    )
    return route

  async def delete_route(
    self,
    user_guid: str,
    roles: list[str],
    path: str,
  ) -> dict:
    logging.debug(
      "[service_routes_delete_route_v1] user=%s roles=%s payload={'path': %s}",
      user_guid,
      roles,
      path,
    )
    if not self.db:
      raise RuntimeError("ServiceRoutesModule not ready")
    await self.db.run(delete_route_request(RoutePathParams(path=path)))
    logging.debug(
      "[service_routes_delete_route_v1] deleted route %s",
      path,
    )
    return {"path": path}
