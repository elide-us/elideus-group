"""System renewals query registry request builders."""

from __future__ import annotations

from queryregistry.models import DBRequest

from .models import (
  DeleteRenewalParams,
  GetRenewalParams,
  ListRenewalsParams,
  UpsertRenewalParams,
)

__all__ = [
  "delete_renewal_request",
  "get_renewal_request",
  "list_renewals_request",
  "upsert_renewal_request",
]


def list_renewals_request(params: ListRenewalsParams) -> DBRequest:
  return DBRequest(op="db:system:renewals:list:1", payload=params.model_dump())


def get_renewal_request(params: GetRenewalParams) -> DBRequest:
  return DBRequest(op="db:system:renewals:get:1", payload=params.model_dump())


def upsert_renewal_request(params: UpsertRenewalParams) -> DBRequest:
  return DBRequest(op="db:system:renewals:upsert:1", payload=params.model_dump())


def delete_renewal_request(params: DeleteRenewalParams) -> DBRequest:
  return DBRequest(op="db:system:renewals:delete:1", payload=params.model_dump())
