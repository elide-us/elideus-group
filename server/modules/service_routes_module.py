from __future__ import annotations

import logging
from fastapi import FastAPI

from rpc.service.routes.models import (
  ServiceRoutesDeleteRoute1,
  ServiceRoutesList1,
  ServiceRoutesRouteItem1,
)
from server.registry.system.routes import (
  delete_route_request,
  get_routes_request,
  upsert_route_request,
)

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
  ) -> ServiceRoutesList1:
    logging.debug(
      "[service_routes_get_routes_v1] user=%s roles=%s",
      user_guid,
      roles,
    )
    if not self.db or not self.auth:
      raise RuntimeError("ServiceRoutesModule not ready")
    res = await self.db.run(get_routes_request())
    routes: list[ServiceRoutesRouteItem1] = []
    for row in res.rows:
      mask = int(row.get("element_roles", 0))
      required_roles = self.auth.mask_to_names(mask)
      route = ServiceRoutesRouteItem1(
        path=row.get("element_path", ""),
        name=row.get("element_name", ""),
        icon=row.get("element_icon"),
        sequence=int(row.get("element_sequence", 0)),
        required_roles=required_roles,
      )
      routes.append(route)
    logging.debug(
      "[service_routes_get_routes_v1] returning %d routes",
      len(routes),
    )
    return ServiceRoutesList1(routes=routes)

  async def upsert_route(
    self,
    user_guid: str,
    roles: list[str],
    route: ServiceRoutesRouteItem1,
  ) -> ServiceRoutesRouteItem1:
    logging.debug(
      "[service_routes_upsert_route_v1] user=%s roles=%s payload=%s",
      user_guid,
      roles,
      route.model_dump(),
    )
    if not self.db or not self.auth:
      raise RuntimeError("ServiceRoutesModule not ready")
    mask = self.auth.names_to_mask(route.required_roles)
    await self.db.run(
      upsert_route_request(
        path=route.path,
        name=route.name,
        icon=route.icon,
        sequence=route.sequence,
        roles=mask,
      )
    )
    logging.debug(
      "[service_routes_upsert_route_v1] upserted route %s",
      route.path,
    )
    return route

  async def delete_route(
    self,
    user_guid: str,
    roles: list[str],
    path: str,
  ) -> ServiceRoutesDeleteRoute1:
    logging.debug(
      "[service_routes_delete_route_v1] user=%s roles=%s payload={'path': %s}",
      user_guid,
      roles,
      path,
    )
    if not self.db:
      raise RuntimeError("ServiceRoutesModule not ready")
    await self.db.run(delete_route_request(path))
    logging.debug(
      "[service_routes_delete_route_v1] deleted route %s",
      path,
    )
    return ServiceRoutesDeleteRoute1(path=path)
