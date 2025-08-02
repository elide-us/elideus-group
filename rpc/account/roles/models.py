from pydantic import BaseModel


class AccountRolesMember1(BaseModel):
  guid: str
  display: str

class AccountRolesMemberList1(BaseModel):
  list: list[AccountRolesMember1]
  role: str
  mask: int

