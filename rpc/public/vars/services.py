from fastapi import HTTPException, Request
from rpc.helpers import unbox_request
from server.models import RPCResponse
from typing import TYPE_CHECKING
if TYPE_CHECKING:
  from server.modules.public_vars_module import PublicVarsModule
from .models import (
  PublicVarsFfmpegVersion1,
  PublicVarsHostname1,
  PublicVarsRepo1,
  PublicVarsVersion1,
  PublicVarsOdbcVersion1,
)


async def public_vars_get_version_v1(request: Request):
  rpc_request, _, _ = await unbox_request(request)
  vars_mod: PublicVarsModule = request.app.state.public_vars
  version = await vars_mod.get_version()
  payload = PublicVarsVersion1(version=version)
  return RPCResponse(
    op=rpc_request.op,
    payload=payload.model_dump(),
    version=rpc_request.version,
  )

async def public_vars_get_hostname_v1(request: Request):
  rpc_request, _, _ = await unbox_request(request)
  vars_mod: PublicVarsModule = request.app.state.public_vars
  hostname = await vars_mod.get_hostname()
  payload = PublicVarsHostname1(hostname=hostname)
  return RPCResponse(
    op=rpc_request.op,
    payload=payload.model_dump(),
    version=rpc_request.version,
  )

async def public_vars_get_repo_v1(request: Request):
  rpc_request, _, _ = await unbox_request(request)
  vars_mod: PublicVarsModule = request.app.state.public_vars
  repo = await vars_mod.get_repo()
  payload = PublicVarsRepo1(repo=repo)
  return RPCResponse(
    op=rpc_request.op,
    payload=payload.model_dump(),
    version=rpc_request.version,
  )

async def public_vars_get_ffmpeg_version_v1(request: Request):
  rpc_request, _, _ = await unbox_request(request)
  vars_mod: PublicVarsModule = request.app.state.public_vars
  try:
    version_line = await vars_mod.get_ffmpeg_version()
  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))
  payload = PublicVarsFfmpegVersion1(ffmpeg_version=version_line)
  return RPCResponse(
    op=rpc_request.op,
    payload=payload.model_dump(),
    version=rpc_request.version,
  )

async def public_vars_get_odbc_version_v1(request: Request):
  rpc_request, _, _ = await unbox_request(request)
  vars_mod: PublicVarsModule = request.app.state.public_vars
  try:
    version_line = await vars_mod.get_odbc_version()
  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))
  payload = PublicVarsOdbcVersion1(odbc_version=version_line)
  return RPCResponse(
    op=rpc_request.op,
    payload=payload.model_dump(),
    version=rpc_request.version,
  )

