import logging

from fastapi import HTTPException, Request

from rpc import HANDLERS
from rpc.helpers import get_rpcrequest_from_request
from rpc.models import RPCResponse


# Mapping of URN domains to the roles allowed to invoke them.
# Sub-routes with special rules are specified using a ``:`` delimited
# path excluding the terminal version component.
DOMAIN_ROLE_MAP: dict[str, dict[str, list[str]]] = {
  "admin": {"": ["ROLE_ADMIN_SUPPORT"]},
  "security": {
    "": ["ROLE_SECURITY_ADMIN"],
    "roles:get_roles": ["ROLE_SECURITY_ADMIN", "ROLE_SYSTEM_ADMIN"],
  },
  "moderation": {"": ["ROLE_MODERATION_SUPPORT"]},
  "service": {"": ["ROLE_SERVICE_ADMIN"]},
  "storage": {"": ["ROLE_STORAGE_ENABLED"]},
  "system": {"": ["ROLE_SYSTEM_ADMIN"]},
  "users": {"": ["ROLE_USERS_ENABLED"]},
}


async def handle_rpc_request(request: Request) -> RPCResponse:
  rpc_request, auth_ctx, parts = await get_rpcrequest_from_request(request)

  if parts[:1] != ["urn"]:
    raise HTTPException(400, "Invalid URN prefix")

  try:
    domain = parts[1]
    remainder = parts[2:]

    rules = DOMAIN_ROLE_MAP.get(domain)
    if rules:
      subroute = ":".join(remainder[:-1]) if remainder else ""
      role_names = rules.get(subroute, rules.get("", []))
      if role_names:
        auth = request.app.state.auth
        required_mask = auth.names_to_mask(role_names)
        if not (auth_ctx.role_mask & required_mask):
          raise HTTPException(status_code=403, detail="Forbidden")

    handler = HANDLERS.get(domain)
    if not handler:
      raise HTTPException(status_code=404, detail="Unknown RPC domain")
    response = await handler(remainder, request)

    logging.info(f"RPC completed: {rpc_request.op}")
    return response
  except Exception:
    logging.exception(f"RPC failed: {rpc_request.op}")
    raise

