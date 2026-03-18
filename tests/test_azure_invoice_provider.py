import asyncio
import json
from types import SimpleNamespace

import pytest

from server.modules.providers.billing import azure_invoice_provider as azure_mod
from server.modules.providers.billing.azure_invoice_provider import AzureInvoiceProvider


class _FakeResponse:
  def __init__(self, status, *, text_data="", headers=None):
    self.status = status
    self._text_data = text_data
    self.headers = headers or {}

  async def __aenter__(self):
    return self

  async def __aexit__(self, exc_type, exc, tb):
    return False

  async def text(self):
    return self._text_data


class _FakeClientSession:
  def __init__(self, get_responses, get_calls):
    self._get_responses = list(get_responses)
    self._get_calls = get_calls

  async def __aenter__(self):
    return self

  async def __aexit__(self, exc_type, exc, tb):
    return False

  def get(self, url, headers=None, params=None):
    self._get_calls.append({"url": url, "headers": headers, "params": params})
    return self._get_responses.pop(0)


class _RecordingDb:
  def __init__(self):
    self.requests = []

  async def run(self, request):
    self.requests.append(request)
    if request.op == "db:finance:staging:create_import:1":
      return SimpleNamespace(rows=[{"recid": 88}])
    if request.op == "db:finance:vendors:get_vendor_by_name:1":
      return SimpleNamespace(rows=[{"recid": 9}])
    if request.op == "db:finance:staging_invoices:get_invoice_by_name:1":
      invoice_name = request.payload["invoice_name"]
      if invoice_name == "INV-EXISTING":
        return SimpleNamespace(rows=[{"element_invoice_name": invoice_name}])
      return SimpleNamespace(rows=[])
    if request.op == "db:finance:staging_purge_log:check_purged_key:1":
      key = request.payload["key"]
      if key == "INV-PURGED":
        return SimpleNamespace(rows={"found": 1})
      return SimpleNamespace(rows=None)
    if request.op in (
      "db:finance:staging_invoices:insert_invoice_batch:1",
      "db:finance:staging_line_items:insert_line_items_batch:1",
      "db:finance:staging:update_import_status:1",
    ):
      return SimpleNamespace(rows=[])
    raise AssertionError(f"unexpected op {request.op}")


def _build_provider(monkeypatch, session_factory):
  provider = AzureInvoiceProvider.__new__(AzureInvoiceProvider)
  provider.module = SimpleNamespace(app=SimpleNamespace(state=SimpleNamespace()))
  provider.db = _RecordingDb()
  provider.env = None
  provider._subscription_id = "sub-123"
  provider._tenant_id = None
  provider._client_id = None
  provider._client_secret = None
  provider._credential = None
  provider._credential_tenant_id = None
  provider._credential_client_id = None
  provider._credential_client_secret = None
  provider._azure_vendor_recid = None

  async def _fake_token():
    return "token-abc"

  monkeypatch.setattr(provider, "_get_management_token", _fake_token)
  monkeypatch.setattr(azure_mod.aiohttp, "ClientSession", session_factory)
  return provider


def test_import_invoices_uses_billing_periods_and_normalizes_invoice_rows(monkeypatch):
  get_calls = []
  billing_periods_payload = {
    "value": [
      {
        "name": "2025-04-1",
        "properties": {
          "billingPeriodStartDate": "2025-04-01",
          "billingPeriodEndDate": "2025-04-30",
          "invoiceIds": [
            "/subscriptions/sub-123/providers/Microsoft.Billing/invoices/INV-NEW",
            "/subscriptions/sub-123/providers/Microsoft.Billing/invoices/INV-EXISTING",
            "/subscriptions/sub-123/providers/Microsoft.Billing/invoices/INV-PURGED",
          ],
        },
      },
    ],
  }
  invoice_payload = {
    "name": "INV-NEW",
    "properties": {
      "invoiceDate": "2025-04-30T00:00:00Z",
      "invoicePeriodStartDate": "2025-04-01",
      "invoicePeriodEndDate": "2025-04-30",
      "dueDate": "2025-05-15",
      "invoiceType": "AzureServices",
      "status": "Due",
      "billedAmount": {"amount": 0, "currency": "USD"},
      "amountDue": {"amount": 0, "currency": "USD"},
      "subscriptionId": "sub-123",
      "subscriptionName": "Production",
      "purchaseOrder": "PO-42",
    },
  }
  responses = [
    _FakeResponse(200, text_data=json.dumps(billing_periods_payload)),
    _FakeResponse(200, text_data=json.dumps(invoice_payload)),
  ]

  provider = _build_provider(
    monkeypatch,
    lambda: _FakeClientSession(responses, get_calls),
  )

  result = asyncio.run(provider.import_invoices(period_month="2025-04"))

  assert result == {
    "import_recid": 88,
    "status": "completed",
    "invoice_count": 1,
    "skipped_count": 2,
    "message": "Imported 1 Azure invoice(s) for 2025-04; skipped 2.",
  }
  assert get_calls[0]["url"].endswith("/billingPeriods")
  assert get_calls[1]["url"].endswith("/billingSubscriptions/sub-123/invoices/INV-NEW")

  invoice_insert = next(
    request
    for request in provider.db.requests
    if request.op == "db:finance:staging_invoices:insert_invoice_batch:1"
  )
  invoice_row = invoice_insert.payload["rows"][0]
  assert invoice_row["element_invoice_name"] == "INV-NEW"
  assert invoice_row["element_billed_amount"] == "0.0"
  assert invoice_row["element_amount_due"] == "0.0"
  assert invoice_row["element_currency"] == "USD"
  assert invoice_row["element_purchase_order"] == "PO-42"

  line_item_insert = next(
    request
    for request in provider.db.requests
    if request.op == "db:finance:staging_line_items:insert_line_items_batch:1"
  )
  line_item_row = line_item_insert.payload["rows"][0]
  assert line_item_row["element_amount"] == "0.0"
  assert line_item_row["element_unit_price"] == "0.0"
  assert line_item_row["element_record_type"] == "invoice"
  assert line_item_row["element_description"] == "Azure invoice INV-NEW (PO-42)"

  status_update = provider.db.requests[-1]
  assert status_update.op == "db:finance:staging:update_import_status:1"
  assert status_update.payload["status"] == 1
  assert status_update.payload["row_count"] == 1


def test_import_invoices_rejects_invalid_period_month(monkeypatch):
  provider = _build_provider(monkeypatch, lambda: _FakeClientSession([], []))

  with pytest.raises(ValueError, match="period_month must be in YYYY-MM format"):
    asyncio.run(provider.import_invoices(period_month="2025/04"))
