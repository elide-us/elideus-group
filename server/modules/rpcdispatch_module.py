from __future__ import annotations

from dataclasses import dataclass, field
import logging

from fastapi import FastAPI

from queryregistry.rpcdispatch.domains import list_domains_request
from queryregistry.rpcdispatch.subdomains import list_subdomains_request
from queryregistry.rpcdispatch.functions import list_functions_request

from . import BaseModule
from .db_module import DbModule


@dataclass
class FunctionEntry:
  recid: int
  name: str
  version: int
  module_attr: str
  method_name: str
  request_model_recid: int | None
  response_model_recid: int | None


@dataclass
class SubdomainEntry:
  recid: int
  name: str
  entitlement_mask: int
  functions: dict[tuple[str, int], FunctionEntry] = field(default_factory=dict)


@dataclass
class DomainEntry:
  recid: int
  name: str
  required_role: str | None
  is_auth_exempt: bool
  is_public: bool
  is_discord: bool
  subdomains: dict[str, SubdomainEntry] = field(default_factory=dict)


class RpcdispatchModule(BaseModule):
  def __init__(self, app: FastAPI):
    super().__init__(app)
    self.db: DbModule | None = None
    self._domains: dict[str, DomainEntry] = {}

  async def startup(self):
    self.db = self.app.state.db
    await self.db.on_ready()
    await self.reload()
    self.mark_ready()

  async def shutdown(self):
    self._domains.clear()
    self.db = None

  async def reload(self) -> None:
    if self.db is None:
      raise RuntimeError("rpcdispatch module requires db module")
    domain_rows = (await self.db.run(list_domains_request())).rows
    subdomain_rows = (await self.db.run(list_subdomains_request())).rows
    function_rows = (await self.db.run(list_functions_request())).rows

    domains: dict[str, DomainEntry] = {}
    by_domain_recid: dict[int, DomainEntry] = {}
    by_subdomain_recid: dict[int, SubdomainEntry] = {}

    for row in domain_rows:
      entry = DomainEntry(
        recid=int(row.get("recid")),
        name=str(row.get("element_name")),
        required_role=row.get("element_required_role"),
        is_auth_exempt=bool(row.get("element_is_auth_exempt")),
        is_public=bool(row.get("element_is_public")),
        is_discord=bool(row.get("element_is_discord")),
      )
      domains[entry.name] = entry
      by_domain_recid[entry.recid] = entry

    for row in subdomain_rows:
      domain_entry = by_domain_recid.get(int(row.get("domains_recid")))
      if domain_entry is None:
        continue
      entry = SubdomainEntry(
        recid=int(row.get("recid")),
        name=str(row.get("element_name")),
        entitlement_mask=int(row.get("element_entitlement_mask") or 0),
      )
      domain_entry.subdomains[entry.name] = entry
      by_subdomain_recid[entry.recid] = entry

    for row in function_rows:
      subdomain_entry = by_subdomain_recid.get(int(row.get("subdomains_recid")))
      if subdomain_entry is None:
        continue
      entry = FunctionEntry(
        recid=int(row.get("recid")),
        name=str(row.get("element_name")),
        version=int(row.get("element_version") or 1),
        module_attr=str(row.get("element_module_attr")),
        method_name=str(row.get("element_method_name")),
        request_model_recid=row.get("element_request_model_recid"),
        response_model_recid=row.get("element_response_model_recid"),
      )
      subdomain_entry.functions[(entry.name, entry.version)] = entry

    self._domains = domains
    logging.info(
      "[rpcdispatch_startup] loaded domains=%d subdomains=%d functions=%d",
      len(domain_rows),
      len(subdomain_rows),
      len(function_rows),
    )

  async def get_domain(self, name: str) -> DomainEntry | None:
    return self._domains.get(name)

  async def get_subdomain(self, domain: str, subdomain: str) -> SubdomainEntry | None:
    domain_entry = self._domains.get(domain)
    if domain_entry is None:
      return None
    return domain_entry.subdomains.get(subdomain)

  async def get_function(
    self,
    domain: str,
    subdomain: str,
    function: str,
    version: int,
  ) -> FunctionEntry | None:
    subdomain_entry = await self.get_subdomain(domain, subdomain)
    if subdomain_entry is None:
      return None
    return subdomain_entry.functions.get((function, version))
