from pydantic import BaseModel


class SupportRolesGetMembersRequest1(BaseModel):
  role: str


class SupportRolesRoleMemberUpdate1(BaseModel):
  role: str
  userGuid: str


class SupportRolesUserItem1(BaseModel):
  guid: str
  displayName: str


class SupportRolesMembers1(BaseModel):
  members: list[SupportRolesUserItem1]
  nonMembers: list[SupportRolesUserItem1]

