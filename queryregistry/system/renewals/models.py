"""System renewals query registry models."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict

__all__ = [
  "DeleteRenewalParams",
  "GetRenewalParams",
  "ListRenewalsParams",
  "UpsertRenewalParams",
]


class ListRenewalsParams(BaseModel):
  model_config = ConfigDict(extra="forbid")

  category: str | None = None
  status: int | None = None


class GetRenewalParams(BaseModel):
  model_config = ConfigDict(extra="forbid")

  recid: int


class UpsertRenewalParams(BaseModel):
  model_config = ConfigDict(extra="forbid")

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


class DeleteRenewalParams(BaseModel):
  model_config = ConfigDict(extra="forbid")

  recid: int
