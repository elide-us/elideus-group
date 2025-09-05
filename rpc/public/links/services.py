from fastapi import Request
from rpc.helpers import unbox_request
from server.models import RPCResponse
from typing import TYPE_CHECKING
if TYPE_CHECKING:
  from server.modules.public_links_module import PublicLinksModule
from .models import (
  PublicLinksHomeLinks1,
  PublicLinksLinkItem1,
  PublicLinksNavBarRoute1,
  PublicLinksNavBarRoutes1,
)


async def public_links_get_home_links_v1(request: Request):
  rpc_request, _, _ = await unbox_request(request)
  links_mod: PublicLinksModule = request.app.state.public_links
  rows = await links_mod.get_home_links()
  links = [PublicLinksLinkItem1(**row) for row in rows]
  payload = PublicLinksHomeLinks1(links=links)
  return RPCResponse(
    op=rpc_request.op,
    payload=payload.model_dump(),
    version=rpc_request.version,
  )

async def public_links_get_navbar_routes_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  links_mod: PublicLinksModule = request.app.state.public_links
  rows = await links_mod.get_navbar_routes(auth_ctx.role_mask)
  routes = [PublicLinksNavBarRoute1(**row) for row in rows]
  payload = PublicLinksNavBarRoutes1(routes=routes)
  return RPCResponse(
    op=rpc_request.op,
    payload=payload.model_dump(),
    version=rpc_request.version,
  )

