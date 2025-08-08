from fastapi import Request

async def admin_users_get_profile_v1(request: Request):
  raise NotImplementedError("urn:admin:users:get_profile:1")

async def admin_users_set_credits_v1(request: Request):
  raise NotImplementedError("urn:admin:users:set_credits:1")

async def admin_users_reset_display_v1(request: Request):
  raise NotImplementedError("urn:admin:users:reset_display:1")

async def admin_users_enable_storage_v1(request: Request):
  raise NotImplementedError("urn:admin:users:enable_storage:1")

