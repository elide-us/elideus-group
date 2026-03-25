import asyncio
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from rpc.service.payment_requests import services as svc


class _FakeFinance:
  def __init__(self, *, should_fail: str | None = None):
    self.should_fail = should_fail
    self.calls = []

  async def on_ready(self):
    return None

  async def create_payment_request(self, payload, requested_by):
    self.calls.append((payload, requested_by))
    if self.should_fail:
      raise ValueError(self.should_fail)
    return {
      "import_recid": 81,
      "status": "pending_approval",
      "message": "ok",
    }


def _build_request(finance):
  return SimpleNamespace(app=SimpleNamespace(state=SimpleNamespace(finance=finance)))


def test_service_payment_requests_create_v1_creates_pending_approval_import(monkeypatch):
  finance = _FakeFinance()

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

  response = asyncio.run(svc.service_payment_requests_create_v1(_build_request(finance)))

  assert response.payload["import_recid"] == 81
  assert response.payload["status"] == "pending_approval"

  assert finance.calls[0][1] == "user-guid"
  assert finance.calls[0][0]["vendor_name"] == "Anthropic"
  assert finance.calls[0][0]["renewal_recid"] == 55


def test_service_payment_requests_create_v1_rejects_unknown_vendor(monkeypatch):
  finance = _FakeFinance(should_fail="Unknown vendor: MissingVendor")

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
    asyncio.run(svc.service_payment_requests_create_v1(_build_request(finance)))
