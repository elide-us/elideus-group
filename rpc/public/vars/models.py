from pydantic import BaseModel


class PublicVarsVersion1(BaseModel):
  version: str


class PublicVarsHostname1(BaseModel):
  hostname: str


class PublicVarsRepo1(BaseModel):
  repo: str


class PublicVarsFfmpegVersion1(BaseModel):
  ffmpeg_version: str


class PublicVarsOdbcVersion1(BaseModel):
  odbc_version: str
