from typing import Optional

from pydantic import BaseModel


class AccountUsersSetCredits1(BaseModel):
  guid: str
  credits: int

class AccountUsersSetDisplay1(BaseModel):
  guid: str
  display: str

class AccountUsersGetProfile1(BaseModel):
  guid: str
  provider: str
  username: str
  email: str
  backupEmail: Optional[str] = None
  profilePicture: Optional[str] = None
  credits: Optional[int] = None
  storageUsed: Optional[int] = None
  storageEnabled: bool | False
  displayEmail: bool = False

