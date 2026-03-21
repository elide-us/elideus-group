"""Finance pipeline config query registry request builders."""

from __future__ import annotations

from queryregistry.models import DBRequest

from .models import (
  DeletePipelineConfigParams,
  GetPipelineConfigParams,
  ListPipelineConfigsParams,
  UpsertPipelineConfigParams,
)

__all__ = [
  "delete_pipeline_config_request",
  "get_pipeline_config_request",
  "list_pipeline_configs_request",
  "upsert_pipeline_config_request",
]


def list_pipeline_configs_request(params: ListPipelineConfigsParams) -> DBRequest:
  return DBRequest(op="db:finance:pipeline_config:list:1", payload=params.model_dump())


def get_pipeline_config_request(params: GetPipelineConfigParams) -> DBRequest:
  return DBRequest(op="db:finance:pipeline_config:get:1", payload=params.model_dump())


def upsert_pipeline_config_request(params: UpsertPipelineConfigParams) -> DBRequest:
  return DBRequest(op="db:finance:pipeline_config:upsert:1", payload=params.model_dump())


def delete_pipeline_config_request(params: DeletePipelineConfigParams) -> DBRequest:
  return DBRequest(op="db:finance:pipeline_config:delete:1", payload=params.model_dump())
