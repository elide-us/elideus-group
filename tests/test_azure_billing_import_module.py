import asyncio
import copy
from types import SimpleNamespace

import pytest

from server.modules.providers.billing import azure_cost_details_provider as azure_mod
from server.modules.providers.billing.azure_cost_details_provider import AzureCostDetailsProvider


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
  module = AzureCostDetailsProvider.__new__(AzureCostDetailsProvider)
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
  assert row["element_quantity"] == "2"
  assert row["element_unit_price"] == "3.5"
  assert row["element_amount"] == "7.0"
  assert row["element_currency"] == "USD"


def test_cost_details_decimal_and_date_helpers_preserve_precision_and_iso_dates():
  assert AzureCostDetailsProvider._to_decimal("0.000033") == "0.000033"
  assert AzureCostDetailsProvider._to_decimal("3.3e-05") == "0.000033"
  assert AzureCostDetailsProvider._to_decimal("0.0006") == "0.0006"
  assert AzureCostDetailsProvider._to_decimal("  ") is None
  assert AzureCostDetailsProvider._to_decimal("not-a-number") is None

  assert AzureCostDetailsProvider._to_iso_date("02/04/2026") == "2026-02-04"
  assert AzureCostDetailsProvider._to_iso_date("2026-02-04T12:34:56Z") == "2026-02-04"
  assert AzureCostDetailsProvider._to_iso_date("2026-02-04") == "2026-02-04"
