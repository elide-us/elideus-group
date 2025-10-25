from pydantic import BaseModel


class PublicVarsVersions1(BaseModel):
  hostname: str
  version: str
  repo: str | None = None
  ffmpeg_version: str | None = None
  odbc_version: str | None = None
