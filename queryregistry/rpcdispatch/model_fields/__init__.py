"""RPC dispatch model_fields query registry request builders."""

from __future__ import annotations

from queryregistry.models import DBRequest

from .models import DeleteModelFieldParams, GetModelFieldParams, ListModelFieldsParams, UpsertModelFieldParams, ListByModelParams


def list_model_fields_request(params: ListModelFieldsParams | None = None) -> DBRequest:
  return DBRequest(op="db:rpcdispatch:model_fields:list:1", payload=(params or ListModelFieldsParams()).model_dump())

def get_model_field_request(params: GetModelFieldParams) -> DBRequest:
  return DBRequest(op="db:rpcdispatch:model_fields:get:1", payload=params.model_dump())

def list_by_model_request(params: ListByModelParams) -> DBRequest:
  return DBRequest(op="db:rpcdispatch:model_fields:list_by_model:1", payload=params.model_dump())

def upsert_model_field_request(params: UpsertModelFieldParams) -> DBRequest:
  return DBRequest(op="db:rpcdispatch:model_fields:upsert:1", payload=params.model_dump())

def delete_model_field_request(params: DeleteModelFieldParams) -> DBRequest:
  return DBRequest(op="db:rpcdispatch:model_fields:delete:1", payload=params.model_dump())
