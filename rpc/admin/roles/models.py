from pydantic import BaseModel


class AdminRolesRoleMemberUpdate1(BaseModel):
  role: str
  userGuid: str


class AdminRolesUserItem1(BaseModel):
  guid: str
  displayName: str


class AdminRolesMembers1(BaseModel):
  members: list[AdminRolesUserItem1]
  nonMembers: list[AdminRolesUserItem1]

