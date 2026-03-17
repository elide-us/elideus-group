from __future__ import annotations

from datetime import date
from decimal import ROUND_HALF_UP, Decimal
from typing import Any

from pydantic import BaseModel

from queryregistry.finance.staging import (
  list_imports_request,
  update_import_status_request,
)
from queryregistry.finance.staging.models import (
  ListImportsParams,
  UpdateImportStatusParams,
)
from queryregistry.finance.staging_line_items import (
  aggregate_line_items_request,
  list_line_items_by_import_request,
)
from queryregistry.finance.staging_line_items.models import (
  AggregateLineItemsParams,
  ListLineItemsByImportParams,
)
from queryregistry.finance.staging_account_map import (
  resolve_account_request,
)
from queryregistry.finance.staging_account_map.models import ResolveAccountParams
from server.modules.async_task_handlers import PipelineHandler


class BillingImportPipelinePayload(BaseModel):
  imports_recid: int


class BillingImportPipelineHandler(PipelineHandler):
  payload_model = BillingImportPipelinePayload

  steps = [
    ("validate_import", lambda app, payload, context: BillingImportPipelineHandler.validate_import(app, payload, context)),
    ("classify_costs", lambda app, payload, context: BillingImportPipelineHandler.classify_costs(app, payload, context)),
    ("create_journal", lambda app, payload, context: BillingImportPipelineHandler.create_journal(app, payload, context)),
    ("mark_promoted", lambda app, payload, context: BillingImportPipelineHandler.mark_promoted(app, payload, context)),
  ]

  @staticmethod
  async def validate_import(app, payload: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    del context
    db = app.state.db
    await db.on_ready()

    imports_recid = int(payload["imports_recid"])
    res = await db.run(list_imports_request(ListImportsParams()))
    import_row = next((dict(row) for row in (res.rows or []) if int(row.get("recid") or 0) == imports_recid), None)
    if not import_row:
      raise ValueError(f"Import {imports_recid} not found")

    status = int(import_row.get("element_status") or 0)
    row_count = int(import_row.get("element_row_count") or 0)
    if status == 3:
      raise ValueError(f"Import {imports_recid} is already promoted")
    if status != 1:
      raise ValueError(f"Import {imports_recid} must be completed before promotion")
    if row_count <= 0:
      raise ValueError(f"Import {imports_recid} has no rows to promote")

    return {
      "imports_recid": imports_recid,
      "import_metadata": import_row,
    }

  @staticmethod
  async def classify_costs(app, payload: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    del payload
    db = app.state.db
    finance = app.state.finance
    await db.on_ready()
    await finance.on_ready()

    imports_recid = int(context["imports_recid"])
    aggregate_res = await db.run(
      aggregate_line_items_request(AggregateLineItemsParams(imports_recid=imports_recid))
    )
    line_items_res = await db.run(
      list_line_items_by_import_request(ListLineItemsByImportParams(imports_recid=imports_recid))
    )
    vendor_recid = None
    if line_items_res.rows:
      vendor_recid = int(line_items_res.rows[0].get("vendors_recid") or 0) or None

    accounts = await finance.list_accounts()
    accounts_by_guid = {str(acct["guid"]): acct for acct in accounts}

    warnings: list[dict[str, Any]] = []
    classified: list[dict[str, Any]] = []

    for row in aggregate_res.rows or []:
      service = row.get("element_service")
      meter_category = row.get("element_category")
      amount = Decimal(str(row.get("element_total_amount") or "0"))
      row_count = int(row.get("element_row_count") or 0)

      resolved = await db.run(
        resolve_account_request(
          ResolveAccountParams(
            service_name=str(service or ""),
            meter_category=str(meter_category) if meter_category is not None else None,
            vendors_recid=vendor_recid,
          )
        )
      )
      if not resolved.rows:
        raise ValueError(
          f"No staging account mapping for service='{service}' meter_category='{meter_category}'",
        )

      resolved_row = dict(resolved.rows[0])
      accounts_guid = str(resolved_row["accounts_guid"])
      account = accounts_by_guid.get(accounts_guid)
      account_number = resolved_row.get("account_number")
      account_name = resolved_row.get("account_name")
      if account:
        account_number = account_number or account.get("number")
        account_name = account_name or account.get("name")

      if str(resolved_row.get("element_service_pattern") or "") == "*":
        warnings.append(
          {
            "service": service,
            "meter_category": meter_category,
            "accounts_guid": accounts_guid,
            "warning": "service matched wildcard catch-all",
          }
        )

      classified.append(
        {
          "accounts_guid": accounts_guid,
          "account_number": account_number,
          "account_name": account_name,
          "service": service,
          "meter_category": meter_category,
          "amount": str(amount),
          "row_count": row_count,
        }
      )

    return {
      "classified_costs": classified,
      "warnings": warnings,
    }

  @staticmethod
  async def create_journal(app, payload: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    del payload
    finance = app.state.finance
    await finance.on_ready()

    imports_recid = int(context["imports_recid"])
    import_metadata = context["import_metadata"]
    classified_costs = context.get("classified_costs") or []

    period_start_raw = str(import_metadata.get("element_period_start") or "")
    period_start = date.fromisoformat(period_start_raw[:10])

    periods = await finance.list_periods()
    matching_period = None
    for period in periods:
      start_date = date.fromisoformat(str(period["start_date"])[:10])
      end_date = date.fromisoformat(str(period["end_date"])[:10])
      if start_date <= period_start <= end_date:
        matching_period = period
        break
    if not matching_period:
      raise ValueError(f"No fiscal period found for import date {period_start.isoformat()}")

    ap_account_guid = await finance._get_account_guid_by_number("2200")

    total = Decimal("0")
    lines: list[dict[str, Any]] = []
    line_number = 1
    for bucket in classified_costs:
      amount = Decimal(str(bucket.get("amount") or "0")).quantize(Decimal("0.00001"), rounding=ROUND_HALF_UP)
      total += amount
      lines.append(
        {
          "line_number": line_number,
          "accounts_guid": bucket["accounts_guid"],
          "debit": str(amount),
          "credit": "0",
          "description": f"Azure {bucket.get('service') or 'Unclassified'} / {bucket.get('meter_category') or 'General'}",
          "dimension_recids": [15, 4],
        }
      )
      line_number += 1

    lines.append(
      {
        "line_number": line_number,
        "accounts_guid": ap_account_guid,
        "debit": "0",
        "credit": str(total),
        "description": f"Azure billing import {imports_recid}",
        "dimension_recids": [15, 4],
      }
    )

    posting_key = f"AZURE-IMPORT-{imports_recid}"
    journal = await finance.create_journal(
      name=f"AZURE-IMPORT-{imports_recid}",
      description=f"Azure billing import promotion for staging import {imports_recid}",
      posting_key=posting_key,
      source_type="azure_billing_import",
      source_id=str(imports_recid),
      periods_guid=matching_period["guid"],
      lines=lines,
      post=True,
    )

    if int(journal.get("status") or 0) != 1:
      journal = await finance.post_journal(int(journal["recid"]))

    return {
      "journal_recid": int(journal["recid"]),
      "posting_summary": {
        "posting_key": posting_key,
        "periods_guid": matching_period["guid"],
        "line_count": len(lines),
        "total": str(total),
      },
    }

  @staticmethod
  async def mark_promoted(app, payload: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    del payload
    db = app.state.db
    await db.on_ready()

    imports_recid = int(context["imports_recid"])
    import_metadata = context["import_metadata"]
    journal_recid = int(context["journal_recid"])

    await db.run(
      update_import_status_request(
        UpdateImportStatusParams(
          recid=imports_recid,
          status=3,
          row_count=int(import_metadata.get("element_row_count") or 0),
          error=None,
        )
      )
    )
    return {
      "imports_recid": imports_recid,
      "import_status": 3,
      "journal_recid": journal_recid,
    }
