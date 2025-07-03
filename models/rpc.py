from pydantic import BaseModel
from typing import Any

class RPCRequest(BaseModel):
  op: str
  payload: dict[str, Any] | None = None
  version: int = 1

class RPCResponse(BaseModel):
  op: str
  payload: Any
  version: int = 1
