from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict


class InsertInvoiceBatchParams(BaseModel):
  model_config = ConfigDict(extra="forbid")

  imports_recid: int
  rows: list[dict[str, Any]] = []


class ListInvoicesByImportParams(BaseModel):
  model_config = ConfigDict(extra="forbid")

  imports_recid: int


class GetInvoiceByNameParams(BaseModel):
  model_config = ConfigDict(extra="forbid")

  invoice_name: str


class DeleteInvoicesByImportParams(BaseModel):
  model_config = ConfigDict(extra="forbid")

  imports_recid: int
