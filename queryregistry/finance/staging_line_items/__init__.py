from __future__ import annotations

from queryregistry.models import DBRequest

from .models import (
  AggregateLineItemsParams,
  DeleteLineItemsByImportParams,
  InsertLineItemsBatchParams,
  ListLineItemsByImportParams,
)


def insert_line_items_batch_request(params: InsertLineItemsBatchParams) -> DBRequest:
  return DBRequest(op="db:finance:staging_line_items:insert_line_items_batch:1", payload=params.model_dump())


def list_line_items_by_import_request(params: ListLineItemsByImportParams) -> DBRequest:
  return DBRequest(op="db:finance:staging_line_items:list_line_items_by_import:1", payload=params.model_dump())


def aggregate_line_items_request(params: AggregateLineItemsParams) -> DBRequest:
  return DBRequest(op="db:finance:staging_line_items:aggregate_line_items:1", payload=params.model_dump())


def delete_line_items_by_import_request(params: DeleteLineItemsByImportParams) -> DBRequest:
  return DBRequest(op="db:finance:staging_line_items:delete_line_items_by_import:1", payload=params.model_dump())
