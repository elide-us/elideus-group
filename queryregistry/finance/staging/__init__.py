"""Finance staging query registry request builders."""

from __future__ import annotations

from queryregistry.models import DBRequest

from .models import (
  AggregateCostByServiceParams,
  CreateImportParams,
  DeleteImportParams,
  InsertCostDetailBatchParams,
  ListCostDetailsByImportParams,
  ListImportsParams,
  UpdateImportStatusParams,
)

__all__ = [
  "aggregate_cost_by_service_request",
  "create_import_request",
  "delete_import_request",
  "insert_cost_detail_batch_request",
  "list_cost_details_by_import_request",
  "list_imports_request",
  "update_import_status_request",
]


def create_import_request(params: CreateImportParams) -> DBRequest:
  return DBRequest(op="db:finance:staging:create_import:1", payload=params.model_dump())


def update_import_status_request(params: UpdateImportStatusParams) -> DBRequest:
  return DBRequest(op="db:finance:staging:update_import_status:1", payload=params.model_dump())


def insert_cost_detail_batch_request(params: InsertCostDetailBatchParams) -> DBRequest:
  return DBRequest(
    op="db:finance:staging:insert_cost_detail_batch:1",
    payload=params.model_dump(),
  )


def list_imports_request(params: ListImportsParams) -> DBRequest:
  return DBRequest(op="db:finance:staging:list_imports:1", payload=params.model_dump())


def list_cost_details_by_import_request(params: ListCostDetailsByImportParams) -> DBRequest:
  return DBRequest(
    op="db:finance:staging:list_cost_details_by_import:1",
    payload=params.model_dump(),
  )


def delete_import_request(params: DeleteImportParams) -> DBRequest:
  return DBRequest(op="db:finance:staging:delete_import:1", payload=params.model_dump())


def aggregate_cost_by_service_request(params: AggregateCostByServiceParams) -> DBRequest:
  return DBRequest(op="db:finance:staging:aggregate_cost_by_service:1", payload=params.model_dump())
