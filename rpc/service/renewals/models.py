"""Service renewals RPC models."""

from __future__ import annotations

from pydantic import BaseModel


class ServiceRenewalsItem1(BaseModel):
  recid: int
  element_guid: str | None = None
  element_name: str
  element_category: str
  element_vendor: str | None = None
  element_reference: str | None = None
  element_expires_on: str | None = None
  element_renew_by: str | None = None
  element_renewal_cost: str | None = None
  element_currency: str | None = None
  element_auto_renew: bool = False
  element_owner: str | None = None
  element_notes: str | None = None
  element_status: int = 1
  element_created_on: str | None = None
  element_modified_on: str | None = None


class ServiceRenewalsList1(BaseModel):
  renewals: list[ServiceRenewalsItem1]


class ServiceRenewalsUpsert1(BaseModel):
  recid: int | None = None
  element_name: str
  element_category: str
  element_vendor: str | None = None
  element_reference: str | None = None
  element_expires_on: str | None = None
  element_renew_by: str | None = None
  element_renewal_cost: str | None = None
  element_currency: str | None = None
  element_auto_renew: bool = False
  element_owner: str | None = None
  element_notes: str | None = None
  element_status: int = 1


class ServiceRenewalsDelete1(BaseModel):
  recid: int


class ServiceRenewalsDeleteResult1(BaseModel):
  recid: int
  deleted: bool


class ServiceRenewalsListParams1(BaseModel):
  category: str | None = None
  status: int | None = None
