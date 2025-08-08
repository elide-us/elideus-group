from fastapi import Request

async def admin_roles_get_members_v1(request: Request):
  raise NotImplementedError("urn:admin:roles:get_members:1")

async def admin_roles_add_member_v1(request: Request):
  raise NotImplementedError("urn:admin:roles:add_member:1")

async def admin_roles_remove_member_v1(request: Request):
  raise NotImplementedError("urn:admin:roles:remove_member:1")

