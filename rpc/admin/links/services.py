
from fastapi import Request
from rpc.models import RPCResponse
from rpc.admin.links.models import AdminLinksHome1, LinkItem, AdminLinksRoutes1, RouteItem
from server.modules.database_module import DatabaseModule
from server.modules.permcap_module import PermCapModule

async def get_home_v1(request: Request) -> RPCResponse:
    db: DatabaseModule = request.app.state.database
    permcap: PermCapModule = request.app.state.permcap
    role_mask = getattr(request.state, 'role_mask', 0)
    data = await db.select_links(role_mask)
    data = permcap.filter_routes(data, role_mask)
    links = [LinkItem(title=row["title"], url=row["url"]) for row in data]

    payload = AdminLinksHome1(links=links)
    return RPCResponse(op="urn:admin:links:home:1", payload=payload, version=1)


async def get_routes_v1(request: Request) -> RPCResponse:
  db: DatabaseModule = request.app.state.database
  permcap: PermCapModule = request.app.state.permcap
  role_mask = getattr(request.state, 'role_mask', 0)
  data = await db.select_routes(role_mask)
  data = permcap.filter_routes(data, role_mask)
  routes = [RouteItem(path=row['path'], name=row['name'], icon=row['icon']) for row in data]

  payload = AdminLinksRoutes1(routes=routes)
  return RPCResponse(op="urn:admin:links:routes:1", payload=payload, version=1)
