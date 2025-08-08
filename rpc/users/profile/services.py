from fastapi import Request

async def users_profile_get_profile_v1(request: Request):
  raise NotImplementedError("urn:users:profile:get_profile:1")

async def users_profile_set_display_v1(request: Request):
  raise NotImplementedError("urn:users:profile:set_display:1")

async def users_profile_set_optin_v1(request: Request):
  raise NotImplementedError("urn:users:profile:set_optin:1")

