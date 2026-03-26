"""RPC dispatch subdomains query registry request builders."""

from __future__ import annotations

from queryregistry.models import DBRequest

from .models import DeleteSubdomainParams, GetSubdomainParams, ListSubdomainsParams, UpsertSubdomainParams, ListByDomainParams


def list_subdomains_request(params: ListSubdomainsParams | None = None) -> DBRequest:
  return DBRequest(op="db:rpcdispatch:subdomains:list:1", payload=(params or ListSubdomainsParams()).model_dump())

def get_subdomain_request(params: GetSubdomainParams) -> DBRequest:
  return DBRequest(op="db:rpcdispatch:subdomains:get:1", payload=params.model_dump())

def list_by_domain_request(params: ListByDomainParams) -> DBRequest:
  return DBRequest(op="db:rpcdispatch:subdomains:list_by_domain:1", payload=params.model_dump())

def upsert_subdomain_request(params: UpsertSubdomainParams) -> DBRequest:
  return DBRequest(op="db:rpcdispatch:subdomains:upsert:1", payload=params.model_dump())

def delete_subdomain_request(params: DeleteSubdomainParams) -> DBRequest:
  return DBRequest(op="db:rpcdispatch:subdomains:delete:1", payload=params.model_dump())
