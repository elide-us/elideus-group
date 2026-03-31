"""Pydantic models for service.rpcdispatch RPC operations."""

from __future__ import annotations

from pydantic import BaseModel


class ServiceRpcdispatchDomainItem1(BaseModel):
  recid: int
  element_name: str
  element_required_role: str | None = None
  element_is_auth_exempt: bool = False
  element_is_public: bool = False
  element_is_discord: bool = False
  element_status: int = 1
  element_app_version: str | None = None
  element_iteration: int = 1
  element_created_on: str | None = None
  element_modified_on: str | None = None


class ServiceRpcdispatchDomainList1(BaseModel):
  domains: list[ServiceRpcdispatchDomainItem1]


class ServiceRpcdispatchSubdomainItem1(BaseModel):
  recid: int
  domains_guid: str
  element_name: str
  element_entitlement_mask: int = 0
  element_status: int = 1
  element_app_version: str | None = None
  element_iteration: int = 1
  element_created_on: str | None = None
  element_modified_on: str | None = None


class ServiceRpcdispatchSubdomainList1(BaseModel):
  subdomains: list[ServiceRpcdispatchSubdomainItem1]


class ServiceRpcdispatchFunctionItem1(BaseModel):
  recid: int
  subdomains_guid: str
  element_name: str
  element_version: int = 1
  element_module_attr: str
  element_method_name: str
  element_request_model_guid: str | None = None
  element_response_model_guid: str | None = None
  element_status: int = 1
  element_app_version: str | None = None
  element_iteration: int = 1
  element_created_on: str | None = None
  element_modified_on: str | None = None


class ServiceRpcdispatchFunctionList1(BaseModel):
  functions: list[ServiceRpcdispatchFunctionItem1]


class ServiceRpcdispatchModelItem1(BaseModel):
  recid: int
  element_name: str
  element_domain: str
  element_subdomain: str
  element_version: int = 1
  element_parent_recid: int | None = None
  element_status: int = 1
  element_app_version: str | None = None
  element_iteration: int = 1
  element_created_on: str | None = None
  element_modified_on: str | None = None


class ServiceRpcdispatchModelList1(BaseModel):
  models: list[ServiceRpcdispatchModelItem1]


class ServiceRpcdispatchModelFieldItem1(BaseModel):
  recid: int
  models_guid: str
  element_name: str
  element_edt_recid: int | None = None
  element_is_nullable: bool = False
  element_is_list: bool = False
  element_is_dict: bool = False
  element_ref_model_guid: str | None = None
  element_default_value: str | None = None
  element_max_length: int | None = None
  element_sort_order: int = 0
  element_status: int = 1
  element_created_on: str | None = None
  element_modified_on: str | None = None


class ServiceRpcdispatchModelFieldList1(BaseModel):
  fields: list[ServiceRpcdispatchModelFieldItem1]
