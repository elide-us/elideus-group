from fastapi import Request

from rpc.helpers import get_rpcrequest_from_request
from rpc.models import RPCResponse
from server.modules.db_module import DbModule
from .models import (
  PublicLinksHomeLinks1,
  PublicLinksLinkItem1,
  PublicLinksNavBarRoute1,
  PublicLinksNavBarRoutes1,
)


async def public_links_get_home_links_v1(request: Request):
  rpc_request, _, _ = await get_rpcrequest_from_request(request)
  db: DbModule = request.app.state.db
  res = await db.run(rpc_request.op, rpc_request.payload or {})
  links = [PublicLinksLinkItem1(**row) for row in res.rows]
  payload = PublicLinksHomeLinks1(links=links)
  return RPCResponse(
    op=rpc_request.op,
    payload=payload.model_dump(),
    version=rpc_request.version,
  )

async def public_links_get_navbar_routes_v1(request: Request):
  rpc_request, auth_ctx, _ = await get_rpcrequest_from_request(request)
  db: DbModule = request.app.state.db
  res = await db.run("urn:public:links:get_navbar_routes:1", {"role_mask": auth_ctx.role_mask})
  routes = [PublicLinksNavBarRoute1(**row) for row in res.rows]
  payload = PublicLinksNavBarRoutes1(routes=routes)
  return RPCResponse(
    op=rpc_request.op,
    payload=payload.model_dump(),
    version=rpc_request.version,
  )

