from __future__ import annotations
import asyncio, subprocess
from fastapi import FastAPI
from . import BaseModule
from .db_module import DbModule

class PublicVarsModule(BaseModule):
  def __init__(self, app: FastAPI):
    super().__init__(app)
    self.db: DbModule | None = None

  async def startup(self):
    self.db = self.app.state.db
    await self.db.on_ready()
    self.mark_ready()

  async def shutdown(self):
    self.db = None

  async def _run_command(self, *cmd: str):
    try:
      process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
      )
      return await process.communicate()
    except NotImplementedError:
      result = await asyncio.to_thread(subprocess.run, cmd, capture_output=True)
      return result.stdout, result.stderr

  async def get_version(self) -> str:
    res = await self.db.run("urn:public:vars:get_version:1", {})
    return res.rows[0].get("version") if res.rows else ""

  async def get_hostname(self) -> str:
    res = await self.db.run("urn:public:vars:get_hostname:1", {})
    return res.rows[0].get("hostname") if res.rows else ""

  async def get_repo(self) -> str:
    res = await self.db.run("urn:public:vars:get_repo:1", {})
    return res.rows[0].get("repo") if res.rows else ""

  async def get_ffmpeg_version(self) -> str:
    try:
      stdout, stderr = await self._run_command("ffmpeg", "-version")
      if stdout:
        return stdout.decode().splitlines()[0]
      return stderr.decode().splitlines()[0]
    except FileNotFoundError:
      return "ffmpeg library not found (Windows)"
    except Exception as e:
      raise RuntimeError(f"Error checking ffmpeg: {e}")

  async def get_odbc_version(self) -> str:
    system = __import__("platform").system()
    try:
      if system == "Windows":
        stdout, stderr = await self._run_command(
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
        stdout, stderr = await self._run_command(
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
      raise RuntimeError(f"Error checking odbc: {e}")
    return version_line
