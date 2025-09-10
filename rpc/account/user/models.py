from pydantic import BaseModel


class AccountUserGuid1(BaseModel):
  userGuid: str


class AccountUserSetCredits1(AccountUserGuid1):
  credits: int


class AccountUserDisplayName1(AccountUserGuid1):
  displayName: str


class AccountUserCredits1(AccountUserGuid1):
  credits: int


class AccountUserCreateFolder1(AccountUserGuid1):
  path: str
