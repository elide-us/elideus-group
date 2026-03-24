"""RPC dispatch domains query registry request builders."""

from __future__ import annotations

from queryregistry.models import DBRequest

from .models import DeleteDomainParams, GetDomainParams, ListDomainsParams, UpsertDomainParams, GetByNameParams


def list_domains_request(params: ListDomainsParams | None = None) -> DBRequest:
  return DBRequest(op="db:rpcdispatch:domains:list:1", payload=(params or ListDomainsParams()).model_dump())

def get_domain_request(params: GetDomainParams) -> DBRequest:
  return DBRequest(op="db:rpcdispatch:domains:get:1", payload=params.model_dump())

def get_by_name_request(params: GetByNameParams) -> DBRequest:
  return DBRequest(op="db:rpcdispatch:domains:get_by_name:1", payload=params.model_dump())

def upsert_domain_request(params: UpsertDomainParams) -> DBRequest:
  return DBRequest(op="db:rpcdispatch:domains:upsert:1", payload=params.model_dump())

def delete_domain_request(params: DeleteDomainParams) -> DBRequest:
  return DBRequest(op="db:rpcdispatch:domains:delete:1", payload=params.model_dump())
