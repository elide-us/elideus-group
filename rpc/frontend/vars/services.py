import asyncio
from fastapi import Request, HTTPException
from rpc.frontend.vars.models import (
  FrontendVarsVersion1,
  FrontendVarsHostname1,
  FrontendVarsRepo1,
  FrontendVarsFfmpegVersion1,
  FrontendVarsVersion2,
  FrontendVarsHostname2,
  FrontendVarsRepo2,
)
from rpc.models import RPCResponse

async def get_version_v1(request: Request):
  db = request.app.state.database
  version = await db.get_config_value("Version")
  payload = FrontendVarsVersion1(version=version)
  return RPCResponse(op="urn:frontend:vars:version:1", payload=payload, version=1)

async def get_hostname_v1(request: Request):
  db = request.app.state.database
  hostname = await db.get_config_value("Hostname")
  payload = FrontendVarsHostname1(hostname=hostname)
  return RPCResponse(op="urn:frontend:vars:hostname:1", payload=payload, version=1)

async def get_repo_v1(request: Request):
  db = request.app.state.database
  repo = await db.get_config_value("Repo")
  payload = FrontendVarsRepo1(repo=repo)
  return RPCResponse(op="urn:frontend:vars:repo:1", payload=payload, version=1)

async def get_version_v2(request: Request):
  db = request.app.state.mssql
  version = await db.get_config_value("Version")
  payload = FrontendVarsVersion2(version=version)
  return RPCResponse(op="urn:frontend:vars:version:2", payload=payload, version=2)

async def get_hostname_v2(request: Request):
  db = request.app.state.mssql
  hostname = await db.get_config_value("Hostname")
  payload = FrontendVarsHostname2(hostname=hostname)
  return RPCResponse(op="urn:frontend:vars:hostname:2", payload=payload, version=2)

async def get_repo_v2(request: Request):
  db = request.app.state.mssql
  repo = await db.get_config_value("Repo")
  payload = FrontendVarsRepo2(repo=repo)
  return RPCResponse(op="urn:frontend:vars:repo:2", payload=payload, version=2)

async def get_ffmpeg_version_v1(request: Request):
  try:
    process = await asyncio.create_subprocess_exec(
      "ffmpeg", "-version",
      stdout=asyncio.subprocess.PIPE,
      stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await process.communicate()
    if stdout:
      version_line = stdout.decode().splitlines()[0]
    else:
      version_line = stderr.decode().splitlines()[0]
    payload = FrontendVarsFfmpegVersion1(ffmpeg_version=version_line)
    return RPCResponse(op="urn:frontend:vars:ffmpeg_version:1", payload=payload, version=1)
  except Exception as e:
    raise HTTPException(status_code=500, detail=f"Error checking ffmpeg: {e}")
