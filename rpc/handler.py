import logging

from fastapi import HTTPException, Request

from rpc import HANDLERS
from rpc.helpers import get_rpcrequest_from_request
from rpc.models import RPCResponse
from rpc.suffix import apply_suffixes, split_suffix


async def handle_rpc_request(request: Request) -> RPCResponse:
  rpc_request, parts = get_rpcrequest_from_request(request)

  if parts[:1] != ["urn"]:
    raise HTTPException(400, "Invalid URN prefix")

  try:
    domain = parts[1]
    remainder = parts[2:]
    base_parts, suffixes = split_suffix(remainder)

    handler = HANDLERS.get(domain)
    if not handler:
      raise HTTPException(status_code=404, detail="Unknown RPC domain")
    response = await handler(base_parts, request)

    response = apply_suffixes(response, suffixes, rpc_request.op)
    logging.info(f"RPC completed: {rpc_request.op}")
    return response
  except Exception:
    logging.exception(f"RPC failed: {rpc_request.op}")
    raise

