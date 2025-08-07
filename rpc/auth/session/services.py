from fastapi import Request

async def auth_session_get_token_v1(request: Request):
  raise NotImplementedError("urn:auth:session:get_token:1")

async def auth_session_refresh_token_v1(request: Request):
  raise NotImplementedError("urn:auth:session:refresh_token:1")

async def auth_session_invalidate_token_v1(request: Request):
  raise NotImplementedError("urn:auth:session:invalidate_token:1")

