from pydantic import BaseModel


class VersionInfo(BaseModel):
  version: str


class PublicVarsHostname1(BaseModel):
  hostname: str


class RepoInfo(BaseModel):
  repo: str


class FfmpegVersion(BaseModel):
  ffmpeg_version: str


class OdbcVersion(BaseModel):
  odbc_version: str

