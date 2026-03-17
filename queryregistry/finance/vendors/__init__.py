from __future__ import annotations

from queryregistry.models import DBRequest

from .models import (
  DeleteVendorParams,
  GetVendorByNameParams,
  GetVendorParams,
  ListVendorsParams,
  UpsertVendorParams,
)


def list_vendors_request(params: ListVendorsParams) -> DBRequest:
  return DBRequest(op="db:finance:vendors:list_vendors:1", payload=params.model_dump())


def get_vendor_request(params: GetVendorParams) -> DBRequest:
  return DBRequest(op="db:finance:vendors:get_vendor:1", payload=params.model_dump())


def get_vendor_by_name_request(params: GetVendorByNameParams) -> DBRequest:
  return DBRequest(op="db:finance:vendors:get_vendor_by_name:1", payload=params.model_dump())


def upsert_vendor_request(params: UpsertVendorParams) -> DBRequest:
  return DBRequest(op="db:finance:vendors:upsert_vendor:1", payload=params.model_dump())


def delete_vendor_request(params: DeleteVendorParams) -> DBRequest:
  return DBRequest(op="db:finance:vendors:delete_vendor:1", payload=params.model_dump())
