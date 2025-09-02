from pydantic import BaseModel


class AuthProvidersUnlinkLastProvider1(BaseModel):
  guid: str
  provider: str
