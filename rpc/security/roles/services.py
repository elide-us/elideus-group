from fastapi import HTTPException, Request

from rpc.helpers import get_rpcrequest_from_request
from rpc.models import RPCResponse
from server.modules.authz_module import ROLE_NAMES
from .models import SecurityRolesRoles1


async def security_roles_get_roles_v1(request: Request):
  rpc_request, auth_ctx, _ = await get_rpcrequest_from_request(request)
  if "ROLE_SECURITY_ADMIN" not in auth_ctx.roles:
    raise HTTPException(status_code=403, detail="Forbidden")
  payload = SecurityRolesRoles1(roles=list(ROLE_NAMES))
  return RPCResponse(
    op=rpc_request.op,
    payload=payload.model_dump(),
    version=rpc_request.version,
  )

async def security_roles_upsert_role_v1(request: Request):
  raise NotImplementedError("urn:security:roles:upsert_role:1")

async def security_roles_delete_role_v1(request: Request):
  raise NotImplementedError("urn:security:roles:delete_role:1")

async def security_roles_get_role_members_v1(request: Request):
  raise NotImplementedError("urn:security:roles:get_role_members:1")

async def security_roles_add_role_member_v1(request: Request):
  raise NotImplementedError("urn:security:roles:add_role_member:1")

async def security_roles_remove_role_member_v1(request: Request):
  raise NotImplementedError("urn:security:roles:remove_role_member:1")

