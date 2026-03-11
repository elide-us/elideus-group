"""Finance credits query registry models."""

from __future__ import annotations

from typing import TypedDict

from pydantic import BaseModel, ConfigDict

__all__ = ["CreditsRecord", "GetCreditsParams", "SetCreditsParams"]


class GetCreditsParams(BaseModel):
  model_config = ConfigDict(extra="forbid")

  guid: str


class SetCreditsParams(BaseModel):
  model_config = ConfigDict(extra="forbid")

  guid: str
  credits: int


class CreditsRecord(TypedDict):
  users_guid: str
  element_credits: int
  element_reserve: int | None
