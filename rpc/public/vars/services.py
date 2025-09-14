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
  PublicVarsVersions1,
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
  rpc_request, auth_ctx, _ = await unbox_request(request)
  vars_mod: PublicVarsModule = request.app.state.public_vars
  required_mask = 0
  if vars_mod.auth:
    required_mask = vars_mod.auth.roles.get("ROLE_SERVICE_ADMIN", 0)
  if not (auth_ctx.role_mask & required_mask):
    raise HTTPException(status_code=403, detail="Forbidden")
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
  rpc_request, auth_ctx, _ = await unbox_request(request)
  vars_mod: PublicVarsModule = request.app.state.public_vars
  required_mask = 0
  if vars_mod.auth:
    required_mask = vars_mod.auth.roles.get("ROLE_SERVICE_ADMIN", 0)
  if not (auth_ctx.role_mask & required_mask):
    raise HTTPException(status_code=403, detail="Forbidden")
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

async def public_vars_get_versions_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  vars_mod: PublicVarsModule = request.app.state.public_vars
  data = await vars_mod.get_versions(auth_ctx.role_mask)
  payload = PublicVarsVersions1(**data)
  return RPCResponse(
    op=rpc_request.op,
    payload=payload.model_dump(exclude_none=True),
    version=rpc_request.version,
  )

