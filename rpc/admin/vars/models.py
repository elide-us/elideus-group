from pydantic import BaseModel

class AdminVarsVersion1(BaseModel):
  version: str

class AdminVarsHostname1(BaseModel):
  hostname: str

class AdminVarsRepo1(BaseModel):
  repo: str
  build: str

