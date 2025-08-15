from pydantic import BaseModel


class AuthSessionSessionToken(BaseModel):
  sub: str
  roles: list[str]
  iat: int
  exp: int
  jti: str
  session: str
  provider: str


class AuthSessionAuthTokens(BaseModel):
  bearerToken: str
  session: AuthSessionSessionToken
