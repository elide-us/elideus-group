import asyncio
from fastapi import HTTPException, Request

from rpc.helpers import get_rpcrequest_from_request
from rpc.models import RPCResponse
from server.modules.db_module import DbModule
from .models import (
  PublicVarsFfmpegVersion1,
  PublicVarsHostname1,
  PublicVarsRepo1,
  PublicVarsVersion1,
)


async def public_vars_get_version_v1(request: Request):
  rpc_request, _, _ = await get_rpcrequest_from_request(request)
  db: DbModule = request.app.state.db
  res = await db.run(rpc_request.op, rpc_request.payload or {})
  version = res.rows[0].get("version") if res.rows else ""
  payload = PublicVarsVersion1(version=version)
  return RPCResponse(
    op=rpc_request.op,
    payload=payload.model_dump(),
    version=rpc_request.version,
  )

async def public_vars_get_hostname_v1(request: Request):
  rpc_request, _, _ = await get_rpcrequest_from_request(request)
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
  rpc_request, _, _ = await get_rpcrequest_from_request(request)
  db: DbModule = request.app.state.db
  res = await db.run(rpc_request.op, rpc_request.payload or {})
  repo = res.rows[0].get("repo") if res.rows else ""
  payload = PublicVarsRepo1(repo=repo)
  return RPCResponse(
    op=rpc_request.op,
    payload=payload.model_dump(),
    version=rpc_request.version,
  )

async def public_vars_get_ffmpeg_version_v1(request: Request):
  rpc_request, _, _ = await get_rpcrequest_from_request(request)
  try:
    process = await asyncio.create_subprocess_exec(
      "ffmpeg",
      "-version",
      stdout=asyncio.subprocess.PIPE,
      stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await process.communicate()
    if stdout:
      version_line = stdout.decode().splitlines()[0]
    else:
      version_line = stderr.decode().splitlines()[0]
    payload = PublicVarsFfmpegVersion1(ffmpeg_version=version_line)
    return RPCResponse(
      op=rpc_request.op,
      payload=payload.model_dump(),
      version=rpc_request.version,
    )
  except Exception as e:
    raise HTTPException(status_code=500, detail=f"Error checking ffmpeg: {e}")

async def public_vars_get_odbc_version_v1(request: Request):
  raise NotImplementedError("urn:public:vars:get_odbc_version:1")

