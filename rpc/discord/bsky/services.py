from fastapi import HTTPException, Request

from rpc.helpers import unbox_request
from server.models import RPCResponse
from server.modules.bsky_module import BskyModule

from .models import DiscordBskyPostRequest1, DiscordBskyPostResponse1


async def discord_bsky_post_message_v1(request: Request):
  rpc_request, _, _ = await unbox_request(request)
  payload_dict = rpc_request.payload or {}
  req = DiscordBskyPostRequest1(**payload_dict)
  module: BskyModule = request.app.state.bsky
  await module.on_ready()
  try:
    result = await module.post_message(req.message)
  except ValueError as exc:
    raise HTTPException(status_code=400, detail=str(exc)) from exc
  payload = DiscordBskyPostResponse1(
    uri=result.uri,
    cid=result.cid,
    handle=result.handle,
    display_name=result.display_name,
  )
  return RPCResponse(
    op=rpc_request.op,
    payload=payload.model_dump(),
    version=rpc_request.version,
  )
