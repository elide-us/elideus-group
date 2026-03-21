import asyncio
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from rpc.finance.staging import services as svc


class _FakeFinanceModule:
  def __init__(self):
    self.approve_calls = []
    self.reject_calls = []

  async def on_ready(self):
    return None

  async def approve_import(self, imports_recid: int, user_guid: str):
    self.approve_calls.append((imports_recid, user_guid))
    return {
      "recid": imports_recid,
      "element_status": 1,
    }

  async def reject_import(self, imports_recid: int, user_guid: str, reason: str | None):
    self.reject_calls.append((imports_recid, user_guid, reason))
    return {
      "recid": imports_recid,
      "element_status": 5,
    }


def _build_request(finance_module):
  return SimpleNamespace(app=SimpleNamespace(state=SimpleNamespace(finance=finance_module)))


def test_finance_staging_approve_v1_returns_expected_payload(monkeypatch):
  finance_module = _FakeFinanceModule()

  async def fake_unbox(_request):
    return (
      SimpleNamespace(
        op="urn:finance:staging:approve:1",
        version=1,
        payload={"imports_recid": 77},
      ),
      SimpleNamespace(user_guid="manager-guid"),
      ["staging", "approve", "1"],
    )

  monkeypatch.setattr(svc, "unbox_request", fake_unbox)

  response = asyncio.run(svc.finance_staging_approve_v1(_build_request(finance_module)))

  assert finance_module.approve_calls == [(77, "manager-guid")]
  assert response.payload == {"imports_recid": 77, "approved": True}


def test_finance_staging_reject_v1_returns_expected_payload(monkeypatch):
  finance_module = _FakeFinanceModule()

  async def fake_unbox(_request):
    return (
      SimpleNamespace(
        op="urn:finance:staging:reject:1",
        version=1,
        payload={"imports_recid": 77, "reason": "Needs correction"},
      ),
      SimpleNamespace(user_guid="manager-guid"),
      ["staging", "reject", "1"],
    )

  monkeypatch.setattr(svc, "unbox_request", fake_unbox)

  response = asyncio.run(svc.finance_staging_reject_v1(_build_request(finance_module)))

  assert finance_module.reject_calls == [(77, "manager-guid", "Needs correction")]
  assert response.payload == {"imports_recid": 77, "rejected": True}


def test_finance_staging_approve_v1_maps_value_error_to_http_400(monkeypatch):
  finance_module = _FakeFinanceModule()

  async def fake_approve_import(imports_recid: int, user_guid: str):
    raise ValueError("Import is not awaiting approval")

  finance_module.approve_import = fake_approve_import

  async def fake_unbox(_request):
    return (
      SimpleNamespace(
        op="urn:finance:staging:approve:1",
        version=1,
        payload={"imports_recid": 77},
      ),
      SimpleNamespace(user_guid="manager-guid"),
      ["staging", "approve", "1"],
    )

  monkeypatch.setattr(svc, "unbox_request", fake_unbox)

  with pytest.raises(HTTPException, match="Import is not awaiting approval"):
    asyncio.run(svc.finance_staging_approve_v1(_build_request(finance_module)))
