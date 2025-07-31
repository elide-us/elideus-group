from pydantic import BaseModel

class BrowserSessionData1(BaseModel):
  bearerToken: str

