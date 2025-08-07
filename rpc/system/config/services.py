from fastapi import Request

async def system_config_get_configs_v1(request: Request):
  raise NotImplementedError("urn:system:config:get_configs:1")

async def system_config_upsert_config_v1(request: Request):
  raise NotImplementedError("urn:system:config:upsert_config:1")

async def system_config_delete_config_v1(request: Request):
  raise NotImplementedError("urn:system:config:delete_config:1")

