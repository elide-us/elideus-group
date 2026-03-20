import asyncio
import json
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from rpc.service.payment_requests import services as svc


class _FakeDb:
  def __init__(self, vendor_rows=None):
    self.vendor_rows = vendor_rows if vendor_rows is not None else [{"recid": 42}]
    self.requests = []

  async def on_ready(self):
    return None

  async def run(self, request):
    self.requests.append(request)
    if request.op == "db:finance:vendors:get_vendor_by_name:1":
      return SimpleNamespace(rows=self.vendor_rows)
    if request.op == "db:finance:staging:create_import:1":
      return SimpleNamespace(rows=[{"recid": 81}])
    if request.op in (
      "db:finance:staging_line_items:insert_line_items_batch:1",
      "db:finance:staging:update_import_status:1",
    ):
      return SimpleNamespace(rows=[])
    raise AssertionError(f"unexpected op {request.op}")


def _build_request(db):
  return SimpleNamespace(app=SimpleNamespace(state=SimpleNamespace(db=db)))


def test_service_payment_requests_create_v1_creates_pending_approval_import(monkeypatch):
  db = _FakeDb()

  async def fake_unbox(_request):
    return (
      SimpleNamespace(
        op="urn:service:payment_requests:create:1",
        version=1,
        payload={
          "vendor_name": "Anthropic",
          "amount": "25.00",
          "currency": "USD",
          "description": "Claude subscription",
          "service": "AI",
          "category": "Subscriptions",
          "period_start": "2026-03-01",
          "period_end": "2026-03-31",
          "renewal_recid": 55,
        },
      ),
      SimpleNamespace(user_guid="user-guid", roles=["ROLE_SERVICE_ADMIN"], role_mask=0),
      ["payment_requests", "create", "1"],
    )

  monkeypatch.setattr(svc, "unbox_request", fake_unbox)

  response = asyncio.run(svc.service_payment_requests_create_v1(_build_request(db)))

  assert response.payload["import_recid"] == 81
  assert response.payload["status"] == "pending_approval"

  create_request = next(req for req in db.requests if req.op == "db:finance:staging:create_import:1")
  assert create_request.payload["initial_status"] == 4
  assert create_request.payload["requested_by"] == "user-guid"

  line_item_request = next(
    req for req in db.requests if req.op == "db:finance:staging_line_items:insert_line_items_batch:1"
  )
  row = line_item_request.payload["rows"][0]
  assert row["element_record_type"] == "payment_request"
  assert json.loads(row["element_raw_json"]) == {
    "vendor_name": "Anthropic",
    "description": "Claude subscription",
    "renewal_recid": 55,
  }

  status_request = db.requests[-1]
  assert status_request.op == "db:finance:staging:update_import_status:1"
  assert status_request.payload["status"] == 4
  assert status_request.payload["row_count"] == 1


def test_service_payment_requests_create_v1_rejects_unknown_vendor(monkeypatch):
  db = _FakeDb(vendor_rows=[])

  async def fake_unbox(_request):
    return (
      SimpleNamespace(
        op="urn:service:payment_requests:create:1",
        version=1,
        payload={
          "vendor_name": "MissingVendor",
          "amount": "10.00",
          "description": "Unknown",
          "period_start": "2026-03-01",
          "period_end": "2026-03-31",
        },
      ),
      SimpleNamespace(user_guid="user-guid", roles=["ROLE_SERVICE_ADMIN"], role_mask=0),
      ["payment_requests", "create", "1"],
    )

  monkeypatch.setattr(svc, "unbox_request", fake_unbox)

  with pytest.raises(HTTPException, match="Unknown vendor"):
    asyncio.run(svc.service_payment_requests_create_v1(_build_request(db)))
