from fastapi import Request

async def system_roles_get_roles_v1(request: Request):
  raise NotImplementedError("urn:system:roles:get_roles:1")

async def system_roles_upsert_role_v1(request: Request):
  raise NotImplementedError("urn:system:roles:upsert_role:1")

async def system_roles_delete_role_v1(request: Request):
  raise NotImplementedError("urn:system:roles:delete_role:1")

async def system_roles_get_role_members_v1(request: Request):
  raise NotImplementedError("urn:system:roles:get_role_members:1")

async def system_roles_add_role_member_v1(request: Request):
  raise NotImplementedError("urn:system:roles:add_role_member:1")

async def system_roles_remove_member_v1(request: Request):
  raise NotImplementedError("urn:system:roles:remove_role_member:1")

