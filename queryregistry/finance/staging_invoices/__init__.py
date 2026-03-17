from __future__ import annotations

from queryregistry.models import DBRequest

from .models import (
  DeleteInvoicesByImportParams,
  GetInvoiceByNameParams,
  InsertInvoiceBatchParams,
  ListInvoicesByImportParams,
)


def insert_invoice_batch_request(params: InsertInvoiceBatchParams) -> DBRequest:
  return DBRequest(op="db:finance:staging_invoices:insert_invoice_batch:1", payload=params.model_dump())


def list_invoices_by_import_request(params: ListInvoicesByImportParams) -> DBRequest:
  return DBRequest(op="db:finance:staging_invoices:list_invoices_by_import:1", payload=params.model_dump())


def get_invoice_by_name_request(params: GetInvoiceByNameParams) -> DBRequest:
  return DBRequest(op="db:finance:staging_invoices:get_invoice_by_name:1", payload=params.model_dump())


def delete_invoices_by_import_request(params: DeleteInvoicesByImportParams) -> DBRequest:
  return DBRequest(op="db:finance:staging_invoices:delete_invoices_by_import:1", payload=params.model_dump())
