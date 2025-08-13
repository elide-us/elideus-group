from fastapi import Request

from rpc.helpers import get_rpcrequest_from_request
from rpc.models import RPCResponse
from server.modules.db_module import DbModule
from .models import HomeLinks, LinkItem


async def public_links_get_home_links_v1(request: Request):
  rpc_request, _ = await get_rpcrequest_from_request(request)
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
  raise NotImplementedError("urn:public:links:get_navbar_routes:1")

