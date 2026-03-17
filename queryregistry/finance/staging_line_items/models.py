from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict


class InsertLineItemsBatchParams(BaseModel):
  model_config = ConfigDict(extra="forbid")

  imports_recid: int
  vendors_recid: int
  rows: list[dict[str, Any]] = []


class ListLineItemsByImportParams(BaseModel):
  model_config = ConfigDict(extra="forbid")

  imports_recid: int


class AggregateLineItemsParams(BaseModel):
  model_config = ConfigDict(extra="forbid")

  imports_recid: int


class DeleteLineItemsByImportParams(BaseModel):
  model_config = ConfigDict(extra="forbid")

  imports_recid: int
