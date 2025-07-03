from pydantic import BaseModel

class AdminVarsVersion1(BaseModel):
  version: str

class AdminVarsHostname1(BaseModel):
  hostname: str

