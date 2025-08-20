from pydantic import BaseModel


class SupportUsersGuid1(BaseModel):
  userGuid: str


class SupportUsersSetCredits1(SupportUsersGuid1):
  credits: int

