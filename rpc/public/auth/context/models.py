from pydantic import BaseModel


class UserContext1(BaseModel):
  display: str
  email: str
  roles: list[str]
  entitlements: list[str]
  providers: list[str]
  sessionType: str
  isAuthenticated: bool
