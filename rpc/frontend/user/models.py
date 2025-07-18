from pydantic import BaseModel

class FrontendUserSetDisplayName1(BaseModel):
  bearerToken: str
  displayName: str
