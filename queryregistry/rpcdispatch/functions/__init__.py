"""RPC dispatch functions query registry request builders."""

from __future__ import annotations

from queryregistry.models import DBRequest

from .models import DeleteFunctionParams, GetFunctionParams, ListFunctionsParams, UpsertFunctionParams, ListBySubdomainParams


def list_functions_request(params: ListFunctionsParams | None = None) -> DBRequest:
  return DBRequest(op="db:rpcdispatch:functions:list:1", payload=(params or ListFunctionsParams()).model_dump())

def get_function_request(params: GetFunctionParams) -> DBRequest:
  return DBRequest(op="db:rpcdispatch:functions:get:1", payload=params.model_dump())

def list_by_subdomain_request(params: ListBySubdomainParams) -> DBRequest:
  return DBRequest(op="db:rpcdispatch:functions:list_by_subdomain:1", payload=params.model_dump())

def upsert_function_request(params: UpsertFunctionParams) -> DBRequest:
  return DBRequest(op="db:rpcdispatch:functions:upsert:1", payload=params.model_dump())

def delete_function_request(params: DeleteFunctionParams) -> DBRequest:
  return DBRequest(op="db:rpcdispatch:functions:delete:1", payload=params.model_dump())
