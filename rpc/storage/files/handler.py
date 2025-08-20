"""Storage files RPC handler.

Dispatches file operations requiring ROLE_STORAGE_ENABLED.
"""

import logging

from fastapi import HTTPException, Request

from rpc.helpers import get_rpcrequest_from_request
from rpc.models import RPCResponse

from . import DISPATCHERS


async def handle_files_request(parts: list[str], request: Request) -> RPCResponse:
  _, auth_ctx, _ = await get_rpcrequest_from_request(request)
  auth = request.app.state.auth
  required_mask = auth.roles.get("ROLE_STORAGE_ENABLED", 0)
  expected_mask = 0x0000000000000002
  has_role = (auth_ctx.role_mask & required_mask) == required_mask
  logging.debug(
    "[Storage] user roles=%s mask=%#018x required_mask=%#018x (ROLE_STORAGE_ENABLED expected %#018x) has_role=%s",
    auth_ctx.roles,
    auth_ctx.role_mask,
    required_mask,
    expected_mask,
    has_role,
  )
  if not has_role:
    raise HTTPException(status_code=403, detail='Forbidden')
  key = tuple(parts[:2])
  handler = DISPATCHERS.get(key)
  if not handler:
    raise HTTPException(status_code=404, detail='Unknown RPC operation')
  return await handler(request)

