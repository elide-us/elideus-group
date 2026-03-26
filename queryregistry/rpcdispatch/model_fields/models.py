"""RPC dispatch model_fields query registry service models."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict

class ListModelFieldsParams(BaseModel):
  model_config = ConfigDict(extra="forbid")

class GetModelFieldParams(BaseModel):
  model_config = ConfigDict(extra="forbid")
  recid: int

class DeleteModelFieldParams(BaseModel):
  model_config = ConfigDict(extra="forbid")
  recid: int

class UpsertModelFieldParams(BaseModel):
  model_config = ConfigDict(extra="forbid")
  recid: int | None = None
  models_recid: int
  element_name: str
  element_edt_recid: int | None = None
  element_is_nullable: bool = False
  element_is_list: bool = False
  element_is_dict: bool = False
  element_ref_model_recid: int | None = None
  element_default_value: str | None = None
  element_max_length: int | None = None
  element_sort_order: int = 0
  element_status: int = 1

class ListByModelParams(BaseModel):
  model_config = ConfigDict(extra="forbid")
  models_recid: int
