from fastapi import Request

async def users_auth_set_provider_v1(request: Request):
  raise NotImplementedError("urn:users:auth:set_provider:1")

async def users_auth_link_provider_v1(request: Request):
  raise NotImplementedError("urn:users:auth:link_provider:1")

async def users_auth_unlink_provider_v1(request: Request):
  raise NotImplementedError("urn:users:auth:unlink_provider:1")

