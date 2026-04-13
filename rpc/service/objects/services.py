from fastapi import Request

from rpc.helpers import unbox_request
from server.models import RPCResponse
from server.modules.cms_workbench_module import CmsWorkbenchModule

from .models import ServiceObjectsReadChildrenParams1, ServiceObjectsReadDetailParams1


async def service_objects_read_object_tree_children_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  params = ServiceObjectsReadChildrenParams1.model_validate(rpc_request.payload or {})
  module: CmsWorkbenchModule = request.app.state.cms_workbench
  await module.on_ready()
  del auth_ctx

  result = await module.read_object_tree_children(params.categoryGuid, params.tableGuid)

  return RPCResponse(
    op=rpc_request.op,
    payload=result,
    version=rpc_request.version,
  )


async def service_objects_read_object_tree_detail_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  params = ServiceObjectsReadDetailParams1.model_validate(rpc_request.payload or {})
  module: CmsWorkbenchModule = request.app.state.cms_workbench
  await module.on_ready()
  del auth_ctx

  result = await module.read_object_tree_detail(params.tableGuid, params.maxRows)

  return RPCResponse(
    op=rpc_request.op,
    payload=result,
    version=rpc_request.version,
  )
