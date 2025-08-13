from fastapi import Request

from rpc.models import RPCResponse
from server.modules.db_module import DbModule


async def public_links_get_home_links_v1(request: Request):
  db: DbModule = request.app.state.db
  res = await db.run("db:public:links:get_home_links:1", {})
  payload = {"links": res.rows}
  return RPCResponse(
    op="urn:public:links:get_home_links:1",
    payload=payload,
    version=1,
  )


async def public_links_get_navbar_routes_v1(request: Request):
  raise NotImplementedError("urn:public:links:get_navbar_routes:1")

