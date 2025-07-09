from pydantic import BaseModel

class AdminVarsVersion1(BaseModel):
  version: str

class AdminVarsHostname1(BaseModel):
  hostname: str

class AdminVarsRepo1(BaseModel):
  repo: str

class AdminVarsFfmpegVersion1(BaseModel):
  ffmpeg_version: str

