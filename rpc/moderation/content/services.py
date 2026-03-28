from fastapi import Request

from rpc.helpers import unbox_request
from server.models import RPCResponse
from server.modules.content_pages_module import ContentPagesModule


async def moderation_content_review_content_v1(request: Request):
  rpc_request, _, _ = await unbox_request(request)
  module: ContentPagesModule = request.app.state.content_pages
  await module.on_ready()
  result = await module.review_content(rpc_request.payload or {})
  return RPCResponse(
    op=rpc_request.op,
    payload=result,
    version=rpc_request.version,
  )
