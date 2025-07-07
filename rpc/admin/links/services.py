
from fastapi import Request
from rpc.models import RPCResponse
from rpc.admin.links.models import AdminLinksHome1, LinkItem, AdminLinksRoutes1, RouteItem

async def get_home_v1(request: Request) -> RPCResponse:
  links = [
    LinkItem(title="Discord", url="https://discord.gg/xXUZFTuzSw"),
    LinkItem(title="GitHub", url="https://github.com/elide-us"),
    LinkItem(title="TikTok", url="https://www.tiktok.com/@elide.us"),
    LinkItem(title="BlueSky", url="https://bsky.app/profile/elideusgroup.com"),
    LinkItem(title="Suno", url="https://suno.com/@elideus"),
    LinkItem(title="Patreon", url="https://patreon.com/Elideus"),
  ]

  payload = AdminLinksHome1(links=links)
  return RPCResponse(op="urn:admin:links:home:1", payload=payload, version=1)

async def get_routes_v1(request: Request) -> RPCResponse:
  routes = [
    RouteItem(path='/', name='Home', icon='home'),
  ]

  payload = AdminLinksRoutes1(routes=routes)
  return RPCResponse(op="urn:admin:links:routes:1", payload=payload, version=1)
