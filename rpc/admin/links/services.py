
from fastapi import Request
from rpc.models import RPCResponse
from rpc.admin.links.models import AdminLinksHome1, LinkItem, AdminLinksRoutes1, RouteItem
from server.modules.database_module import DatabaseModule

async def get_home_v1(request: Request) -> RPCResponse:
    db: DatabaseModule = request.app.state.database
    data = await db.select_links()
    links = [
        LinkItem(title=row["title"], url=row["url"]) for row in data
    ]

    payload = AdminLinksHome1(links=links)
    return RPCResponse(op="urn:admin:links:home:1", payload=payload, version=1)


async def get_routes_v1(request: Request) -> RPCResponse:
  db: DatabaseModule = request.app.state.database
  data = await db.select_routes()
  routes = [
    RouteItem(path=row['path'], name=row['name'], icon=row['icon']) for row in data
  ]

  payload = AdminLinksRoutes1(routes=routes)
  return RPCResponse(op="urn:admin:links:routes:1", payload=payload, version=1)
