from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import Request

from rpc.helpers import unbox_request
from server.models import RPCResponse

from .models import LoadPathParams1, ObjectTreeCategory1

if TYPE_CHECKING:
  from server.modules.cms_workbench_module import CmsWorkbenchModule


async def public_route_load_path_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  module: CmsWorkbenchModule = request.app.state.cms_workbench
  await module.on_ready()
  params = LoadPathParams1.model_validate(rpc_request.payload or {})
  result = await module.load_path(params.path, auth_ctx.model_dump())
  return RPCResponse(
    op=rpc_request.op,
    payload=result.model_dump(),
    version=rpc_request.version,
  )


async def public_route_read_navigation_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  module: CmsWorkbenchModule = request.app.state.cms_workbench
  await module.on_ready()

  user_roles = auth_ctx.roles if auth_ctx.user_guid else []
  result = await module.read_navigation(user_roles)

  return RPCResponse(
    op=rpc_request.op,
    payload={"elements": result},
    version=rpc_request.version,
  )


async def public_route_read_object_tree_categories_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  module: CmsWorkbenchModule = request.app.state.cms_workbench
  await module.on_ready()
  del auth_ctx

  result = await module.read_object_tree_categories()

  return RPCResponse(
    op=rpc_request.op,
    payload=[ObjectTreeCategory1(**item).model_dump() for item in result],
    version=rpc_request.version,
  )
