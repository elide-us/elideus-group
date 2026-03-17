from typing import Any

from pydantic import BaseModel


class StagingPurgeLogList1(BaseModel):
  purge_logs: list[dict[str, Any]]
