import asyncio
from fastapi import Request, HTTPException
from rpc.system.vars.models import SystemVarsVersion1, SystemVarsHostname1, SystemVarsRepo1, SystemVarsFfmpegVersion1
from rpc.models import RPCResponse

async def get_version_v1(request: Request):
  db = request.app.state.database
  version = await db.get_config_value("Version")
  payload = SystemVarsVersion1(version=version)
  return RPCResponse(op="urn:system:vars:version:1", payload=payload, version=1)

async def get_hostname_v1(request: Request):
  db = request.app.state.database
  hostname = await db.get_config_value("Hostname")
  payload = SystemVarsHostname1(hostname=hostname)
  return RPCResponse(op="urn:system:vars:hostname:1", payload=payload, version=1)

async def get_repo_v1(request: Request):
  db = request.app.state.database
  repo = await db.get_config_value("Repo")
  payload = SystemVarsRepo1(repo=repo)
  return RPCResponse(op="urn:system:vars:repo:1", payload=payload, version=1)

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
    payload = SystemVarsFfmpegVersion1(ffmpeg_version=version_line)
    return RPCResponse(op="urn:system:vars:ffmpeg_version:1", payload=payload, version=1)
  except Exception as e:
    raise HTTPException(status_code=500, detail=f"Error checking ffmpeg: {e}")
