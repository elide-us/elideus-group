from pydantic import BaseModel

class FrontendVarsVersion1(BaseModel):
  version: str

class FrontendVarsHostname1(BaseModel):
  hostname: str

class FrontendVarsRepo1(BaseModel):
  repo: str

class FrontendVarsFfmpegVersion1(BaseModel):
  ffmpeg_version: str

class ViewDiscord1(BaseModel):
  content: str
