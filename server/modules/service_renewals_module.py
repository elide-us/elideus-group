"""Service renewals domain module."""

from typing import Any

from fastapi import FastAPI

from queryregistry.system.renewals import (
  delete_renewal_request,
  get_renewal_request,
  list_renewals_request,
  upsert_renewal_request,
)
from queryregistry.system.renewals.models import (
  DeleteRenewalParams,
  GetRenewalParams,
  ListRenewalsParams,
  UpsertRenewalParams,
)

from . import BaseModule
from .db_module import DbModule


class ServiceRenewalsModule(BaseModule):
  def __init__(self, app: FastAPI):
    super().__init__(app)
    self.db: DbModule | None = None

  async def startup(self):
    self.db = self.app.state.db
    await self.db.on_ready()
    self.app.state.service_renewals = self
    self.mark_ready()

  async def shutdown(self):
    self.db = None

  async def list_renewals(self, category: str | None = None, status: int | None = None) -> list[dict[str, Any]]:
    assert self.db
    result = await self.db.run(
      list_renewals_request(ListRenewalsParams(category=category, status=status)),
    )
    return list(result.rows or [])

  async def get_renewal(self, recid: int | None) -> dict[str, Any] | None:
    assert self.db
    result = await self.db.run(get_renewal_request(GetRenewalParams(recid=recid)))
    return dict(result.rows[0]) if result.rows else None

  async def upsert_renewal(self, payload: dict[str, Any]) -> dict[str, Any]:
    assert self.db
    params = UpsertRenewalParams(**payload)
    await self.db.run(upsert_renewal_request(params))
    return params.model_dump()

  async def delete_renewal(self, recid: int) -> dict[str, Any]:
    assert self.db
    await self.db.run(delete_renewal_request(DeleteRenewalParams(recid=recid)))
    return {"recid": recid, "deleted": True}
