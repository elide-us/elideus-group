from datetime import datetime, timezone
from typing import Any, Optional

from pydantic import BaseModel, Field


"""
This is an internal domain class, when a user makes a request 
through the front end, we unpack the bearer token and get the
user GUID, we then look up their security details in the DB
and populate the below data structure which shepherds the 
request internallly until a response is generated.
"""
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


"""
This is the internal RPC response class and contains the main 
payload to be packaged into the server response object.
"""
class RPCResponse(BaseModel):
  op: str
  payload: Any
  version: int = 1

  timestamp: Optional[datetime] = Field(
    default_factory=lambda: datetime.now(timezone.utc),
    description="Server UTC timestamp of response generation",
  )


