from datetime import datetime, timezone
from typing import Any, Optional

from pydantic import BaseModel, Field, PrivateAttr


class RPCRequest(BaseModel):
  op: str
  payload: Optional[dict[str, Any]] = None
  version: int = 1

  timestamp: Optional[datetime] = Field(
    default_factory=lambda: datetime.now(timezone.utc),
    description="Client-supplied or default UTC timestamp",
  )

  _user_guid: Optional[str] = PrivateAttr(None)
  _user_role: int = PrivateAttr(0)

  @property
  def user_guid(self) -> Optional[str]:
    return self._user_guid

  @user_guid.setter
  def user_guid(self, value: Optional[str]) -> None:
    self._user_guid = value

  @property
  def user_role(self) -> int:
    return self._user_role

  @user_role.setter
  def user_role(self, value: int) -> None:
    self._user_role = value

class RPCResponse(BaseModel):
  op: str
  payload: Any
  version: int = 1

  timestamp: Optional[datetime] = Field(
    default_factory=lambda: datetime.now(timezone.utc),
    description="Server UTC timestamp of response generation",
  )


class ViewSuffixDiscord1(BaseModel):
  content: str
