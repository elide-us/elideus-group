from pydantic import BaseModel, Field
from typing import Any, Optional
from datetime import datetime, timezone

class RPCRequest(BaseModel):
  op: str
  user_guid: str | None = None
  user_role: int | None = None
  payload: dict[str, Any] | None = None
  version: int = 1

  timestamp: Optional[datetime] = Field(
    default_factory=lambda: datetime.now(timezone.utc),
    description="Client-supplied or default UTC timestamp"
  )

class RPCResponse(BaseModel):
  op: str
  payload: Any
  version: int = 1

  timestamp: datetime = Field(
    default_factory=lambda: datetime.now(timezone.utc),
    description="Server UTC timestamp of response generation"
  )

# ###REVIEW### Unused model, verify necessity
class UserData(BaseModel):
  bearerToken: str

class BrowserSessionData1(BaseModel):
  bearerToken: str | None = None
  rotationToken: str | None = None
  rotationExpires: datetime | None = None

class AccessToken1(BaseModel):
  accessSubject: str | None = None
  accessToken: str | None = None
  accessExpires: datetime | None = None

