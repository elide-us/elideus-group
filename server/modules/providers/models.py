from pydantic import BaseModel


class DBResult(BaseModel):
  rows: list[dict] = []
  rowcount: int = 0
