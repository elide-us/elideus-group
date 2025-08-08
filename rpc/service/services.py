from fastapi import Request


async def service_health_check_v1(request: Request):
  raise NotImplementedError("urn:service:health_check:1")
