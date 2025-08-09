from fastapi import Request

async def users_providers_set_provider_v1(request: Request):
  raise NotImplementedError("urn:users:providers:set_provider:1")

async def users_providers_link_provider_v1(request: Request):
  raise NotImplementedError("urn:users:providers:link_provider:1")

async def users_providers_unlink_provider_v1(request: Request):
  raise NotImplementedError("urn:users:providers:unlink_provider:1")

async def users_providers_get_by_provider_identifier_v1(request: Request):
  raise NotImplementedError("urn:users:providers:get_by_provider_identifier:1")

async def users_providers_create_from_provider_v1(request: Request):
  raise NotImplementedError("urn:users:providers:create_from_provider:1")

