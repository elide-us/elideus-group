from pydantic import BaseModel

class SystemVarsVersion1(BaseModel):
  version: str

class SystemVarsHostname1(BaseModel):
  hostname: str

class SystemVarsRepo1(BaseModel):
  repo: str

class SystemVarsFfmpegVersion1(BaseModel):
  ffmpeg_version: str

class ViewDiscord1(BaseModel):
  content: str
