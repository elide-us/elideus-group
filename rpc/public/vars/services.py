from fastapi import Request

from rpc.helpers import get_rpcrequest_from_request
from rpc.models import RPCResponse
from server.modules.db_module import DbModule
from .models import PublicVarsHostname1


async def public_vars_get_version_v1(request: Request):
  raise NotImplementedError("urn:public:vars:get_version:1")

async def public_vars_get_hostname_v1(request: Request):
  rpc_request, _ = await get_rpcrequest_from_request(request)
  db: DbModule = request.app.state.db
  res = await db.run(rpc_request.op, rpc_request.payload or {})
  hostname = res.rows[0].get("hostname") if res.rows else ""
  payload = PublicVarsHostname1(hostname=hostname)
  return RPCResponse(
    op=rpc_request.op,
    payload=payload.model_dump(),
    version=rpc_request.version,
  )

async def public_vars_get_repo_v1(request: Request):
  raise NotImplementedError("urn:public:vars:get_repo:1")

async def public_vars_get_ffmpeg_version_v1(request: Request):
  raise NotImplementedError("urn:public:vars:get_ffmpeg_version:1")

async def public_vars_get_odbc_version_v1(request: Request):
  raise NotImplementedError("urn:public:vars:get_odbc_version:1")

