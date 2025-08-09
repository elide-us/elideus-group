from pydantic import BaseModel


class SessionToken(BaseModel):
  sub: str
  roles: list[str]
  iat: int
  exp: int
  jti: str
  session: str
  provider: str
