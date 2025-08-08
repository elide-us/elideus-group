from fastapi import Request

async def security_roles_get_roles_v1(request: Request):
  raise NotImplementedError("urn:security:roles:get_roles:1")

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

