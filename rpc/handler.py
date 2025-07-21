from fastapi import Request, HTTPException
import logging
from rpc.admin.handler import handle_admin_request
from rpc.auth.handler import handle_auth_request
from rpc.frontend.handler import handle_frontend_request
from rpc.models import RPCRequest, RPCResponse
from rpc.suffix import split_suffix, apply_suffixes
from server.modules.auth_module import AuthModule
from server.modules.database_module import DatabaseModule
from server.helpers.roles import ROLE_REGISTERED


async def _populate_request_roles(request: Request) -> None:
  request.state.role_mask = 0
  header = request.headers.get('authorization')
  if not header or not header.lower().startswith('bearer '):
    return
  token = header.split(' ', 1)[1].strip()
  auth: AuthModule | None = getattr(request.app.state, 'auth', None)
  db: DatabaseModule | None = getattr(request.app.state, 'database', None)
  if not auth or not db:
    return
  try:
    data = await auth.decode_bearer_token(token)
  except Exception:
    logging.info('Invalid bearer token provided')
    return
  guid = data.get('guid')
  if not guid:
    return
  request.state.user_guid = guid
  request.state.role_mask = (await db.get_user_roles(guid)) | ROLE_REGISTERED


async def handle_rpc_request(rpc_request: RPCRequest, request: Request) -> RPCResponse:
  await _populate_request_roles(request)
  parts = rpc_request.op.split(":")
  logging.debug(
    "handle_rpc_request op=%s parts=%s payload=%s",
    rpc_request.op,
    parts,
    rpc_request.payload,
  )

  if parts[:1] != ["urn"]:
    raise HTTPException(400, "Invalid URN prefix")

  try:
    domain = parts[1]
    remainder = parts[2:]
    base_parts, suffixes = split_suffix(remainder)
    match domain:
      case "admin":
        response = await handle_admin_request(base_parts, rpc_request, request)
      case "auth":
        response = await handle_auth_request(base_parts, rpc_request, request)
      case "frontend":
        response = await handle_frontend_request(base_parts, rpc_request, request)
      case _:
        raise HTTPException(status_code=404, detail="Unknown RPC domain")
    response = apply_suffixes(response, suffixes, rpc_request.op)
    logging.info(f"RPC completed: {rpc_request.op}")
    return response
  except Exception:
    logging.exception(f"RPC failed: {rpc_request.op}")
    raise
