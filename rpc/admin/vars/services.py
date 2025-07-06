import asyncio
from fastapi import Request, HTTPException
from rpc.admin.vars.models import AdminVarsVersion1, AdminVarsHostname1, AdminVarsRepo1, AdminVarsFfmpegVersion1
from rpc.models import RPCResponse

async def get_version_v1(request: Request):
  version = request.app.state.version
  payload = AdminVarsVersion1(version=version)
  return RPCResponse(op="urn:admin:vars:version:1", payload=payload, version=1)

async def get_hostname_v1(request: Request):
  hostname = request.app.state.hostname
  payload = AdminVarsHostname1(hostname=hostname)
  return RPCResponse(op="urn:admin:vars:hostname:1", payload=payload, version=1)

async def get_repo_v1(request: Request):
  repo = request.app.state.repo
  payload = AdminVarsRepo1(repo=repo, build=f"{repo}/actions")
  return RPCResponse(op="urn:admin:vars:repo:1", payload=payload, version=1)

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
    payload = AdminVarsFfmpegVersion1(ffmpeg_version=version_line)
    return RPCResponse(op="urn:admin:vars:ffmpeg_version:1", payload=payload, version=1)
  except Exception as e:
    raise HTTPException(status_code=500, detail=f"Error checking ffmpeg: {e}")
