"""Identity enablements query registry models."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict

__all__ = ["GetUserEnablementsParams", "UpsertUserEnablementsParams"]


class GetUserEnablementsParams(BaseModel):
  model_config = ConfigDict(extra="forbid")

  users_guid: str


class UpsertUserEnablementsParams(BaseModel):
  model_config = ConfigDict(extra="forbid")

  users_guid: str
  element_enablements: str
