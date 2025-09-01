from pydantic import BaseModel


class SupportUsersGuid1(BaseModel):
  userGuid: str


class SupportUsersSetCredits1(SupportUsersGuid1):
  credits: int


class SupportUsersStorageStatus1(SupportUsersGuid1):
  exists: bool

