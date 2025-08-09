from typing import Any, Dict, Protocol
from pydantic import BaseModel


class DBResult(BaseModel):
  rows: list[dict] = []
  rowcount: int = 0


class Provider(Protocol):
  async def init(**cfg) -> None: ...
  async def dispatch(op: str, args: Dict[str, Any]) -> Dict[str, Any] | DBResult: ...
