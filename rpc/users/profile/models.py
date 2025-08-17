from typing import List, Optional

from pydantic import BaseModel


class UsersProfileAuthProvider1(BaseModel):
  name: str
  display: str


class UsersProfileProfile1(BaseModel):
  guid: str
  display_name: str
  email: str
  display_email: bool
  credits: int
  profile_image: Optional[str] = None
  default_provider: str
  auth_providers: List[UsersProfileAuthProvider1] = []


class UsersProfileSetDisplay1(BaseModel):
  display_name: str


class UsersProfileSetOptin1(BaseModel):
  display_email: bool

