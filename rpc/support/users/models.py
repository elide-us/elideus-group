from pydantic import BaseModel


class SupportUsersGuid1(BaseModel):
  userGuid: str


class SupportUsersSetCredits1(SupportUsersGuid1):
  credits: int


class SupportUsersDisplayName1(SupportUsersGuid1):
  displayName: str


class SupportUsersCredits1(SupportUsersGuid1):
  credits: int
