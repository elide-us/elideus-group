"""Finance status code query registry request builders."""

from __future__ import annotations

from queryregistry.models import DBRequest

from .models import GetStatusCodeParams, ListStatusCodesParams

__all__ = [
  "get_status_code_request",
  "list_status_codes_request",
]


def list_status_codes_request(params: ListStatusCodesParams) -> DBRequest:
  return DBRequest(op="db:finance:status:list:1", payload=params.model_dump())


def get_status_code_request(params: GetStatusCodeParams) -> DBRequest:
  return DBRequest(op="db:finance:status:get_by_domain_code:1", payload=params.model_dump())
