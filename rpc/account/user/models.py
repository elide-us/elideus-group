from pydantic import BaseModel


class AccountUserGuid1(BaseModel):
  userGuid: str


class AccountUserSetCredits1(AccountUserGuid1):
  credits: int


class AccountUserStorageStatus1(AccountUserGuid1):
  exists: bool
