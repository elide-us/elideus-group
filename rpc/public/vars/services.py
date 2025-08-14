import asyncio
import subprocess
from fastapi import HTTPException, Request

from rpc.helpers import get_rpcrequest_from_request
from rpc.models import RPCResponse
from server.modules.db_module import DbModule
from .models import (
  PublicVarsFfmpegVersion1,
  PublicVarsHostname1,
  PublicVarsRepo1,
  PublicVarsVersion1,
  PublicVarsOdbcVersion1,
)


async def _run_command(*cmd: str):
  try:
    process = await asyncio.create_subprocess_exec(
      *cmd,
      stdout=asyncio.subprocess.PIPE,
      stderr=asyncio.subprocess.PIPE,
    )
    return await process.communicate()
  except NotImplementedError:
    result = await asyncio.to_thread(
      subprocess.run, cmd, capture_output=True
    )
    return result.stdout, result.stderr


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
    stdout, stderr = await _run_command("ffmpeg", "-version")
    if stdout:
      version_line = stdout.decode().splitlines()[0]
    else:
      version_line = stderr.decode().splitlines()[0]
  except FileNotFoundError:
    version_line = "ffmpeg library not found (Windows)"
  except Exception as e:
    raise HTTPException(status_code=500, detail=f"Error checking ffmpeg: {e}")

  payload = PublicVarsFfmpegVersion1(ffmpeg_version=version_line)
  return RPCResponse(
    op=rpc_request.op,
    payload=payload.model_dump(),
    version=rpc_request.version,
  )

async def public_vars_get_odbc_version_v1(request: Request):
  rpc_request, _, _ = await get_rpcrequest_from_request(request)
  system = __import__("platform").system()
  try:
    if system == "Windows":
      stdout, stderr = await _run_command(
        "cmd",
        "/c",
        "reg query \"HKLM\\SOFTWARE\\ODBC\\ODBCINST.INI\\ODBC Driver 18 for SQL Server\" /v Version",
      )
      output = stdout.decode() or stderr.decode()
      version_line = ""
      for line in output.splitlines():
        if line.strip().startswith("Version"):
          parts = line.split()
          version_line = f"ODBC Driver 18 for SQL Server {parts[-1]}"
          break
      if not version_line:
        version_line = "odbc library not found (Windows)"
    else:
      packages = ["msodbcsql18", "unixodbc", "libodbc2"]
      stdout, stderr = await _run_command(
        "dpkg-query",
        "-W",
        "-f",
        "${Package} ${Version}\\n",
        *packages,
      )
      if stdout:
        version_line = stdout.decode().strip().replace("\n", "; ")
      else:
        version_line = stderr.decode().strip() or "odbc library not found"
  except FileNotFoundError:
    version_line = "odbc library not found" if system != "Windows" else "odbc library not found (Windows)"
  except Exception as e:
    raise HTTPException(status_code=500, detail=f"Error checking odbc: {e}")

  payload = PublicVarsOdbcVersion1(odbc_version=version_line)
  return RPCResponse(
    op=rpc_request.op,
    payload=payload.model_dump(),
    version=rpc_request.version,
  )

