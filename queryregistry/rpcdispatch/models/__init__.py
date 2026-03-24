"""RPC dispatch models query registry request builders."""

from __future__ import annotations

from queryregistry.models import DBRequest

from .models import DeleteModelParams, GetModelParams, ListModelsParams, UpsertModelParams, GetByNameParams


def list_models_request(params: ListModelsParams | None = None) -> DBRequest:
  return DBRequest(op="db:rpcdispatch:models:list:1", payload=(params or ListModelsParams()).model_dump())

def get_model_request(params: GetModelParams) -> DBRequest:
  return DBRequest(op="db:rpcdispatch:models:get:1", payload=params.model_dump())

def get_by_name_request(params: GetByNameParams) -> DBRequest:
  return DBRequest(op="db:rpcdispatch:models:get_by_name:1", payload=params.model_dump())

def upsert_model_request(params: UpsertModelParams) -> DBRequest:
  return DBRequest(op="db:rpcdispatch:models:upsert:1", payload=params.model_dump())

def delete_model_request(params: DeleteModelParams) -> DBRequest:
  return DBRequest(op="db:rpcdispatch:models:delete:1", payload=params.model_dump())
