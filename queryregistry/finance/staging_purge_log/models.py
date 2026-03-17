from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class ListPurgeLogsParams(BaseModel):
  model_config = ConfigDict(extra="forbid")

  vendors_recid: int | None = None


class GetPurgeLogParams(BaseModel):
  model_config = ConfigDict(extra="forbid")

  vendors_recid: int
  period_key: str


class CheckPurgedKeyParams(BaseModel):
  model_config = ConfigDict(extra="forbid")

  vendors_recid: int
  key: str


class UpsertPurgeLogParams(BaseModel):
  model_config = ConfigDict(extra="forbid")

  vendors_recid: int
  period_key: str
  purged_keys_json: str
  purged_count: int
