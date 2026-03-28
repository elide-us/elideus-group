from __future__ import annotations

from fastapi import Request
from rpc.helpers import unbox_request
from server.models import RPCResponse
from typing import TYPE_CHECKING

from .models import PublicVarsVersions1

if TYPE_CHECKING:
  from server.modules.public_vars_module import PublicVarsModule


async def public_vars_get_versions_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  module: PublicVarsModule = request.app.state.public_vars
  data = await module.get_versions(getattr(auth_ctx, "role_mask", 0))
  payload = PublicVarsVersions1(**data)
  return RPCResponse(
    op=rpc_request.op,
    payload=payload.model_dump(exclude_none=True),
    version=rpc_request.version,
  )

