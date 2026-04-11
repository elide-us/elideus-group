from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import HTTPException, Request

from rpc.helpers import unbox_request
from server.models import RPCResponse

from .models import UserContext1

if TYPE_CHECKING:
  from server.modules.session_module import SessionModule


async def public_auth_get_user_context_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  if not auth_ctx.user_guid:
    raise HTTPException(status_code=401, detail='Missing or invalid session token')

  module: SessionModule = request.app.state.session
  await module.on_ready()

  claims = auth_ctx.claims or {}
  result: UserContext1 = UserContext1.model_validate(
    await module.get_user_context(
      auth_ctx.user_guid,
      str(claims.get('sid') or ''),
      str(claims.get('session_type') or 'browser'),
    )
  )
  return RPCResponse(op=rpc_request.op, payload=result.model_dump(), version=rpc_request.version)
