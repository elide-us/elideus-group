from datetime import datetime, timezone
from typing import Any, Optional

from pydantic import BaseModel, Field


class RPCRequest(BaseModel):
  op: str
  payload: Optional[dict[str, Any]] = None
  version: int = 1

  timestamp: Optional[datetime] = Field(
    default_factory=lambda: datetime.now(timezone.utc),
    description="Client-supplied or default UTC timestamp",
  )

  user_guid: Optional[str] = Field(
    default=None,
    description="GUID extracted from bearer token",
  )
  roles: list[str] = Field(
    default_factory=list,
    description="Role names assigned to the user",
  )
  role_mask: int = Field(
    default=0,
    description="Bitmask representing user roles",
  )


class RPCResponse(BaseModel):
  op: str
  payload: Any
  version: int = 1

  timestamp: Optional[datetime] = Field(
    default_factory=lambda: datetime.now(timezone.utc),
    description="Server UTC timestamp of response generation",
  )


