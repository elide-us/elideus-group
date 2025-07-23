from fastapi import Request
from rpc.models import RPCRequest, RPCResponse
from rpc.system.routes.models import SystemRoutesList1, SystemRouteItem, SystemRouteUpdate1, SystemRouteDelete1
from server.modules.database_module import DatabaseModule
from server.helpers.roles import mask_to_names, names_to_mask

async def list_routes_v1(request: Request) -> RPCResponse:
  db: DatabaseModule = request.app.state.database
  rows = await db.list_routes()
  routes = [
    SystemRouteItem(
      path=r['path'],
      name=r['name'],
      icon=r['icon'],
      sequence=r['sequence'],
      requiredRoles=mask_to_names(int(r['required_roles'] or 0)),
    )
    for r in rows
  ]
  payload = SystemRoutesList1(routes=routes)
  return RPCResponse(op='urn:system:routes:list:1', payload=payload, version=1)

async def set_route_v1(rpc_request: RPCRequest, request: Request) -> RPCResponse:
  data = SystemRouteUpdate1(**(rpc_request.payload or {}))
  db: DatabaseModule = request.app.state.database
  mask = names_to_mask(data.requiredRoles)
  await db.set_route(data.path, data.name, data.icon, mask, data.sequence)
  return await list_routes_v1(request)

async def delete_route_v1(rpc_request: RPCRequest, request: Request) -> RPCResponse:
  data = SystemRouteDelete1(**(rpc_request.payload or {}))
  db: DatabaseModule = request.app.state.database
  await db.delete_route(data.path)
  return await list_routes_v1(request)
