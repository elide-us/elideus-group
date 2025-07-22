from fastapi import Request, HTTPException
from rpc.admin.roles.models import RoleItem, AdminRolesList1, AdminRoleUpdate1, AdminRoleDelete1
from rpc.models import RPCResponse
from server.modules.database_module import DatabaseModule
from server.helpers import roles as role_helper


def mask_to_bit(mask: int) -> int:
  if mask == 0:
    return 0
  return (mask.bit_length() - 1)

def bit_to_mask(bit: int) -> int:
  if bit < 0 or bit >= 63:
    raise HTTPException(status_code=400, detail='Invalid bit index')
  return 1 << bit

async def list_roles_v1(request: Request) -> RPCResponse:
  db: DatabaseModule = request.app.state.database
  rows = await db.list_roles()
  roles = [RoleItem(name=r['name'], bit=mask_to_bit(int(r['mask']))) for r in rows]
  roles.sort(key=lambda r: r.bit)
  payload = AdminRolesList1(roles=roles)
  return RPCResponse(op='urn:admin:roles:list:1', payload=payload, version=1)

async def set_role_v1(rpc_request, request: Request) -> RPCResponse:
  data = AdminRoleUpdate1(**(rpc_request.payload or {}))
  db: DatabaseModule = request.app.state.database
  mask = bit_to_mask(data.bit)
  await db.set_role(data.name, mask)
  await role_helper.load_roles(db)
  return await list_roles_v1(request)

async def delete_role_v1(rpc_request, request: Request) -> RPCResponse:
  data = AdminRoleDelete1(**(rpc_request.payload or {}))
  db: DatabaseModule = request.app.state.database
  await db.delete_role(data.name)
  await role_helper.load_roles(db)
  return await list_roles_v1(request)
