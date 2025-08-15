from fastapi import Request

from rpc.helpers import get_rpcrequest_from_request
from rpc.models import RPCResponse
from server.modules.db_module import DbModule
from .models import HomeLinks, LinkItem, NavbarRoute, NavbarRoutes


async def public_links_get_home_links_v1(request: Request):
  rpc_request, _, _ = await get_rpcrequest_from_request(request)
  db: DbModule = request.app.state.db
  res = await db.run(rpc_request.op, rpc_request.payload or {})
  links = [LinkItem(**row) for row in res.rows]
  payload = HomeLinks(links=links)
  return RPCResponse(
    op=rpc_request.op,
    payload=payload.model_dump(),
    version=rpc_request.version,
  )

async def public_links_get_navbar_routes_v1(request: Request):
  rpc_request, auth_ctx, _ = await get_rpcrequest_from_request(request)
  db: DbModule = request.app.state.db
  args = dict(rpc_request.payload or {})
  args["role_mask"] = getattr(auth_ctx, "role_mask", 0)
  res = await db.run(rpc_request.op, args)
  routes = [
    NavbarRoute(
      path=row.get("element_path", ""),
      name=row.get("element_name", ""),
      icon=row.get("element_icon"),
    )
    for row in res.rows
  ]
  payload = NavbarRoutes(routes=routes)
  return RPCResponse(
    op=rpc_request.op,
    payload=payload.model_dump(),
    version=rpc_request.version,
  )

