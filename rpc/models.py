from pydantic import BaseModel, Field
from typing import Any, Optional
from datetime import datetime, timezone

class RPCRequest(BaseModel):
  op: str
  payload: Optional[dict[str, Any]] = None
  version: int = 1

  timestamp: Optional[datetime] = Field(
    default_factory=lambda: datetime.now(timezone.utc),
    description="Client-supplied or default UTC timestamp"
  )
  metadata: Optional[dict[str, Any]] = Field(
    default=None,
    description="Optional context (e.g. client app version, debug flags)"
  )

class RPCResponse(BaseModel):
  op: str
  payload: Any
  version: int = 1

  timestamp: datetime = Field(
    default_factory=lambda: datetime.now(timezone.utc),
    description="Server UTC timestamp of response generation"
  )
  metadata: Optional[dict[str, Any]] = Field(
    default=None,
    description="Optional metadata like processing time or status notes"
  )

# ###REVIEW### Unused model, verify necessity
class UserData(BaseModel):
  bearerToken: str

class BrowserSessionData1(BaseModel):
  bearerToken: Optional[str] = None
  rotationToken: Optional[str] = None
  rotationExpires: Optional[datetime] = None

