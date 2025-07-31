from datetime import datetime, timezone
from typing import Any, Optional

from pydantic import BaseModel, Field


class RPCRequest(BaseModel):
  op: str
  user_guid: str
  user_role: int
  payload: Optional[dict[str, Any]] = None
  version: int = 1

  timestamp: Optional[datetime] = Field(
    default_factory=lambda: datetime.now(timezone.utc),
    description="Client-supplied or default UTC timestamp"
  )

class RPCResponse(BaseModel):
  op: str
  payload: Any
  version: int = 1

  timestamp: Optional[datetime] = Field(
    default_factory=lambda: datetime.now(timezone.utc),
    description="Server UTC timestamp of response generation"
  )
