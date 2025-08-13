from fastapi import Request

from rpc.models import RPCResponse
from server.modules.db_module import DbModule
from .models import HomeLinks, LinkItem


async def public_links_get_home_links_v1(request: Request):
  db: DbModule = request.app.state.db
  res = await db.run("db:public:links:get_home_links:1", {})
  links = [LinkItem(**row) for row in res.rows]
  payload = HomeLinks(links=links)
  return RPCResponse(
    op="urn:public:links:get_home_links:1",
    payload=payload.model_dump(),
    version=1,
  )

async def public_links_get_navbar_routes_v1(request: Request):
  raise NotImplementedError("urn:public:links:get_navbar_routes:1")

