import asyncio
import copy
from types import SimpleNamespace

import pytest

from server.modules import azure_billing_import_module as azure_mod
from server.modules.azure_billing_import_module import AzureBillingImportModule


class _FakeResponse:
  def __init__(self, status, *, text_data="", json_data=None, headers=None):
    self.status = status
    self._text_data = text_data
    self._json_data = json_data
    self.headers = headers or {}

  async def __aenter__(self):
    return self

  async def __aexit__(self, exc_type, exc, tb):
    return False

  async def text(self):
    return self._text_data

  async def json(self, content_type=None):
    return self._json_data


class _FakeClientSession:
  def __init__(self, post_responses, get_responses, post_bodies):
    self._post_responses = list(post_responses)
    self._get_responses = list(get_responses)
    self._post_bodies = post_bodies

  async def __aenter__(self):
    return self

  async def __aexit__(self, exc_type, exc, tb):
    return False

  def post(self, _url, headers=None, json=None):
    self._post_bodies.append(copy.deepcopy(json))
    return self._post_responses.pop(0)

  def get(self, _url, headers=None, params=None):
    return self._get_responses.pop(0)


class _FakeDb:
  def __init__(self):
    self.calls = 0

  async def run(self, _request):
    self.calls += 1
    if self.calls == 1:
      return SimpleNamespace(rows=[{"recid": 77}])
    if self.calls == 2:
      return SimpleNamespace(rows=[{"recid": 9}])
    return SimpleNamespace(rows=[])


def _build_module(monkeypatch, session_factory):
  module = AzureBillingImportModule.__new__(AzureBillingImportModule)
  module.app = SimpleNamespace(state=SimpleNamespace())
  module.db = _FakeDb()
  module.env = None
  module._subscription_id = "sub-123"
  module._tenant_id = None
  module._client_id = None
  module._client_secret = None
  module._credential = None
  module._credential_tenant_id = None
  module._credential_client_id = None
  module._credential_client_secret = None

  async def _fake_token():
    return "token-abc"

  monkeypatch.setattr(module, "_get_management_token", _fake_token)
  monkeypatch.setattr(azure_mod.aiohttp, "ClientSession", session_factory)

  async def _no_sleep(_seconds):
    return None

  monkeypatch.setattr(azure_mod.asyncio, "sleep", _no_sleep)
  return module


def test_import_cost_details_retries_when_start_date_must_be_after(monkeypatch, caplog):
  post_bodies = []
  post_responses = [
    _FakeResponse(
      400,
      text_data=(
        '{"error":"Start   date must be after 1/2/2024 3:04:05 PM"}'
      ),
    ),
    _FakeResponse(
      202,
      headers={"Location": "https://poll.example", "Retry-After": "1"},
    ),
  ]
  get_responses = [
    _FakeResponse(
      200,
      json_data={
        "status": "Completed",
        "manifest": {"blobs": [{"blobLink": "https://blob.example"}]},
      },
      headers={"Retry-After": "1"},
    ),
    _FakeResponse(200, text_data="Date,Cost\n2024-01-02,10\n"),
  ]

  module = _build_module(
    monkeypatch,
    lambda: _FakeClientSession(post_responses, get_responses, post_bodies),
  )

  with caplog.at_level("INFO"):
    result = asyncio.run(
      module.import_cost_details(
        period_start="2024-01-01T00:00:00",
        period_end="2024-01-31T23:59:59",
      )
    )

  assert result["status"] == "completed"
  assert len(post_bodies) == 2
  assert post_bodies[0]["timePeriod"]["start"] == "2024-01-01T00:00:00"
  assert post_bodies[1]["timePeriod"]["start"] == "2024-01-02T15:04:05"
  assert "Auto-corrected Azure Cost Details start date" in caplog.text


def test_import_cost_details_raises_immediately_for_non_matching_400(monkeypatch):
  post_bodies = []
  post_responses = [
    _FakeResponse(400, text_data='{"error":"some other 400"}'),
  ]

  module = _build_module(
    monkeypatch,
    lambda: _FakeClientSession(post_responses, [], post_bodies),
  )

  with pytest.raises(RuntimeError, match="Azure Cost Details report request failed"):
    asyncio.run(
      module.import_cost_details(
        period_start="2024-01-01T00:00:00",
        period_end="2024-01-31T23:59:59",
      )
    )

  assert len(post_bodies) == 1


class _FakeInvoicesDb:
  def __init__(self):
    self.requests = []

  async def run(self, request):
    self.requests.append(request)
    if request.op == "db:finance:vendors:get_vendor_by_name:1":
      return SimpleNamespace(rows=[{"recid": 9}])
    if request.op == "db:finance:staging:create_import:1":
      return SimpleNamespace(rows=[{"recid": 101}])
    if request.op == "db:finance:staging_invoices:get_invoice_by_name:1":
      if request.payload.get("invoice_name") == "INV-ACTIVE":
        return SimpleNamespace(rows={"recid": 1})
      return SimpleNamespace(rows=None)
    if request.op == "db:finance:staging_purge_log:check_purged_key:1":
      if request.payload.get("key") == "INV-PURGED":
        return SimpleNamespace(rows={"found": 1})
      return SimpleNamespace(rows=None)
    if request.op in (
      "db:finance:staging_invoices:insert_invoice_batch:1",
      "db:finance:staging_line_items:insert_line_items_batch:1",
      "db:finance:staging:update_import_status:1",
    ):
      return SimpleNamespace(rows=[])
    raise AssertionError(f"unexpected op {request.op}")


def test_import_invoices_dedups_against_active_and_purged(monkeypatch, caplog):
  invoices_payload = {
    "value": [
      {"name": "INV-ACTIVE", "properties": {"invoiceDate": "2025-01-02", "invoicePeriodStartDate": "2025-01-01T00:00:00Z", "invoicePeriodEndDate": "2025-01-31T23:59:59Z", "billedAmount": {"value": "10", "currency": "USD"}, "invoiceType": "AzureServices", "subscriptionDisplayName": "Prod"}},
      {"name": "INV-PURGED", "properties": {"invoiceDate": "2025-01-03", "invoicePeriodStartDate": "1/1/2025", "invoicePeriodEndDate": "1/31/2025", "billedAmount": {"value": "20", "currency": "USD"}, "invoiceType": "AzureServices", "subscriptionDisplayName": "Prod"}},
      {"name": "INV-NEW", "properties": {"invoiceDate": "2025-01-04", "invoicePeriodStartDate": "2025-01-01", "invoicePeriodEndDate": "2025-01-31", "billedAmount": {"value": "30", "currency": "USD"}, "invoiceType": "AzureServices", "subscriptionDisplayName": "Prod"}},
      {"name": "INV-OTHER-MONTH", "properties": {"invoiceDate": "2025-02-04", "invoicePeriodStartDate": "2025-02-01", "invoicePeriodEndDate": "2025-02-28", "billedAmount": {"value": "40", "currency": "USD"}, "invoiceType": "AzureServices", "subscriptionDisplayName": "Prod"}},
    ],
    "nextLink": None,
  }

  module = AzureBillingImportModule.__new__(AzureBillingImportModule)
  module.app = SimpleNamespace(state=SimpleNamespace())
  module.db = _FakeInvoicesDb()
  module.env = None
  module._subscription_id = "sub-123"
  module._tenant_id = None
  module._client_id = None
  module._client_secret = None
  module._credential = None
  module._credential_tenant_id = None
  module._credential_client_id = None
  module._credential_client_secret = None
  module._azure_vendor_recid = None

  async def _fake_token():
    return "token-abc"

  monkeypatch.setattr(module, "_get_management_token", _fake_token)
  monkeypatch.setattr(
    azure_mod.aiohttp,
    "ClientSession",
    lambda: _FakeClientSession([], [_FakeResponse(200, json_data=invoices_payload)], []),
  )

  with caplog.at_level("INFO"):
    result = asyncio.run(module.import_invoices("2025-01"))

  assert result["status"] == "completed"
  assert result["invoice_count"] == 1
  assert result["skipped_count"] == 2
  assert result["message"] is None
  assert "Invoice API returned 4 total invoices, 3 matched month 2025-01, 1 inserted, 2 skipped" in caplog.text

  line_item_insert = next(r for r in module.db.requests if r.op == "db:finance:staging_line_items:insert_line_items_batch:1")
  assert line_item_insert.payload["rows"][0]["element_record_type"] == "invoice"

  create_request = next(
    request
    for request in module.db.requests
    if request.op == "db:finance:staging:create_import:1"
  )
  assert create_request.payload["period_start"] == "2025-01-01"
  assert create_request.payload["period_end"] == "2025-01-31"


def test_import_invoices_returns_message_when_month_has_no_invoice(monkeypatch, caplog):
  invoices_payload = {
    "value": [
      {"name": "INV-FEB", "properties": {"invoiceDate": "2025-02-04", "invoicePeriodStartDate": "2025-02-01", "invoicePeriodEndDate": "2025-02-28", "billedAmount": {"value": "40", "currency": "USD"}, "invoiceType": "AzureServices", "subscriptionDisplayName": "Prod"}},
    ],
    "nextLink": None,
  }

  module = AzureBillingImportModule.__new__(AzureBillingImportModule)
  module.app = SimpleNamespace(state=SimpleNamespace())
  module.db = _FakeInvoicesDb()
  module.env = None
  module._subscription_id = "sub-123"
  module._tenant_id = None
  module._client_id = None
  module._client_secret = None
  module._credential = None
  module._credential_tenant_id = None
  module._credential_client_id = None
  module._credential_client_secret = None
  module._azure_vendor_recid = None

  async def _fake_token():
    return "token-abc"

  monkeypatch.setattr(module, "_get_management_token", _fake_token)
  monkeypatch.setattr(
    azure_mod.aiohttp,
    "ClientSession",
    lambda: _FakeClientSession([], [_FakeResponse(200, json_data=invoices_payload)], []),
  )

  with caplog.at_level("INFO"):
    result = asyncio.run(module.import_invoices("2025-01"))

  assert result["status"] == "completed"
  assert result["invoice_count"] == 0
  assert result["skipped_count"] == 0
  assert result["message"] == (
    "No Azure invoice matched billing period month 2025-01. "
    "The invoice may not have been generated yet for that period."
  )
  assert "Invoice API returned 1 total invoices, 0 matched month 2025-01, 0 inserted, 0 skipped" in caplog.text

  update_request = next(
    request
    for request in module.db.requests
    if request.op == "db:finance:staging:update_import_status:1"
  )
  assert update_request.payload["error"] == result["message"]


class _RecordingDb:
  def __init__(self):
    self.requests = []

  async def run(self, request):
    self.requests.append(request)
    if request.op == "db:finance:staging:create_import:1":
      return SimpleNamespace(rows=[{"recid": 77}])
    if request.op == "db:finance:vendors:get_vendor_by_name:1":
      return SimpleNamespace(rows=[{"recid": 9}])
    if request.op in (
      "db:finance:staging:insert_cost_detail_batch:1",
      "db:finance:staging_line_items:insert_line_items_batch:1",
      "db:finance:staging:update_import_status:1",
    ):
      return SimpleNamespace(rows=[])
    raise AssertionError(f"unexpected op {request.op}")


def test_import_cost_details_normalizes_camel_case_csv_headers(monkeypatch):
  post_bodies = []
  post_responses = [
    _FakeResponse(
      202,
      headers={"Location": "https://poll.example", "Retry-After": "1"},
    ),
  ]
  get_responses = [
    _FakeResponse(
      200,
      json_data={
        "status": "Completed",
        "manifest": {"blobs": [{"blobLink": "https://blob.example"}]},
      },
      headers={"Retry-After": "1"},
    ),
    _FakeResponse(
      200,
      text_data=(
        "date,consumedService,meterCategory,meterName,quantity,effectivePrice,"
        "costInBillingCurrency,billingCurrency\n"
        "2024-01-02T00:00:00Z,Microsoft.Sql,Databases,SQL Database,2,3.5,7.0,USD\n"
      ),
    ),
  ]

  module = _build_module(
    monkeypatch,
    lambda: _FakeClientSession(post_responses, get_responses, post_bodies),
  )
  module.db = _RecordingDb()

  result = asyncio.run(
    module.import_cost_details(
      period_start="2024-01-01T00:00:00",
      period_end="2024-01-31T23:59:59",
    )
  )

  assert result["status"] == "completed"

  cost_detail_insert = next(
    request
    for request in module.db.requests
    if request.op == "db:finance:staging:insert_cost_detail_batch:1"
  )
  assert cost_detail_insert.payload["rows"][0]["consumedService"] == "Microsoft.Sql"
  assert cost_detail_insert.payload["rows"][0]["costInBillingCurrency"] == "7.0"

  line_item_insert = next(
    request
    for request in module.db.requests
    if request.op == "db:finance:staging_line_items:insert_line_items_batch:1"
  )
  row = line_item_insert.payload["rows"][0]
  assert row["element_date"] == "2024-01-02"
  assert row["element_service"] == "Microsoft.Sql"
  assert row["element_category"] == "Databases"
  assert row["element_description"] == "SQL Database"
  assert row["element_quantity"] == "2.0"
  assert row["element_unit_price"] == "3.5"
  assert row["element_amount"] == "7.0"
  assert row["element_currency"] == "USD"
