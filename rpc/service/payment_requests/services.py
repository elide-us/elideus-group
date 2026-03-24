"""Service payment requests RPC service functions."""

from __future__ import annotations

import json

from fastapi import HTTPException, Request

from queryregistry.finance.staging import create_import_request, update_import_status_request
from queryregistry.finance.staging.models import CreateImportParams, UpdateImportStatusParams
from queryregistry.finance.staging_line_items import insert_line_items_batch_request
from queryregistry.finance.staging_line_items.models import InsertLineItemsBatchParams
from queryregistry.finance.vendors import get_vendor_by_name_request
from queryregistry.finance.vendors.models import GetVendorByNameParams
from rpc.helpers import unbox_request
from server.models import RPCResponse
from server.modules.db_module import DbModule
from server.modules.models.finance_statuses import IMPORT_PENDING_APPROVAL

from .models import PaymentRequestCreate1, PaymentRequestCreateResult1


async def service_payment_requests_create_v1(request: Request):
  rpc_request, auth_ctx, _ = await unbox_request(request)
  payload = PaymentRequestCreate1(**(rpc_request.payload or {}))
  db: DbModule = request.app.state.db
  await db.on_ready()

  vendor_result = await db.run(
    get_vendor_by_name_request(GetVendorByNameParams(element_name=payload.vendor_name)),
  )
  if not vendor_result.rows:
    raise HTTPException(status_code=404, detail=f"Unknown vendor: {payload.vendor_name}")
  vendor_recid = int(vendor_result.rows[0]["recid"])

  create_result = await db.run(
    create_import_request(
      CreateImportParams(
        source="payment_request",
        scope=f"vendor/{payload.vendor_name}",
        metric="PaymentRequest",
        period_start=payload.period_start,
        period_end=payload.period_end,
        requested_by=auth_ctx.user_guid,
        initial_status=IMPORT_PENDING_APPROVAL,
      ),
    ),
  )
  if not create_result.rows:
    raise RuntimeError("Failed to create staging import record")
  import_recid = int(create_result.rows[0]["recid"])

  raw_data = {
    "vendor_name": payload.vendor_name,
    "description": payload.description,
  }
  if payload.renewal_recid is not None:
    raw_data["renewal_recid"] = payload.renewal_recid

  line_item = {
    "element_date": payload.period_start,
    "element_service": payload.service or payload.vendor_name,
    "element_category": payload.category or "PaymentRequest",
    "element_description": payload.description,
    "element_quantity": "1.0",
    "element_unit_price": payload.amount,
    "element_amount": payload.amount,
    "element_currency": payload.currency,
    "element_raw_json": json.dumps(raw_data),
    "element_record_type": "payment_request",
  }

  await db.run(
    insert_line_items_batch_request(
      InsertLineItemsBatchParams(
        imports_recid=import_recid,
        vendors_recid=vendor_recid,
        rows=[line_item],
      ),
    ),
  )

  await db.run(
    update_import_status_request(
      UpdateImportStatusParams(
        recid=import_recid,
        status=IMPORT_PENDING_APPROVAL,
        row_count=1,
        error=None,
      ),
    ),
  )

  result = PaymentRequestCreateResult1(
    import_recid=import_recid,
    status="pending_approval",
    message=(
      f"Payment request for {payload.vendor_name} ({payload.amount} {payload.currency}) "
      "submitted for approval."
    ),
  )
  return RPCResponse(
    op=rpc_request.op,
    payload=result.model_dump(),
    version=rpc_request.version,
  )
