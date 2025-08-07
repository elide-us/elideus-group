from fastapi import Request

async def system_routes_get_routes_v1(request: Request):
  raise NotImplementedError("urn:system:routes:get_routes:1")

async def system_routes_upsert_route_v1(request: Request):
  raise NotImplementedError("urn:system:routes:upsert_route:1")

async def system_routes_delete_route_v1(request: Request):
  raise NotImplementedError("urn:system:routes:delete_route:1")

