from pydantic import BaseModel


class AdminUsersGuid1(BaseModel):
  userGuid: str


class AdminUsersSetCredits1(AdminUsersGuid1):
  credits: int

