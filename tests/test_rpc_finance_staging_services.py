import asyncio
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from rpc.finance.staging import services as svc


class _FakeDb:
  def __init__(self):
    self.requests = []

  async def on_ready(self):
    return None

  async def run(self, request):
    self.requests.append(request)
    return SimpleNamespace(rows=[])


def _request_with_db(db):
  return SimpleNamespace(app=SimpleNamespace(state=SimpleNamespace(db=db)))


def test_finance_staging_list_imports_v1_forwards_optional_status(monkeypatch):
  db = _FakeDb()

  async def fake_unbox(_request):
    return (
      SimpleNamespace(op="urn:finance:staging:list_imports:1", payload={"status": 4}, version=1),
      SimpleNamespace(user_guid="acct-guid", roles=["ROLE_FINANCE_ACCT"], role_mask=0),
      ["staging", "list_imports", "1"],
    )

  monkeypatch.setattr(svc, "unbox_request", fake_unbox)

  response = asyncio.run(svc.finance_staging_list_imports_v1(_request_with_db(db)))

  assert response.payload == {"imports": []}
  assert db.requests[0].op == "db:finance:staging:list_imports:1"
  assert db.requests[0].payload == {"status": 4}


def test_finance_staging_approve_v1_requires_manager_role(monkeypatch):
  db = _FakeDb()

  async def fake_unbox(_request):
    return (
      SimpleNamespace(op="urn:finance:staging:approve:1", payload={"imports_recid": 12}, version=1),
      SimpleNamespace(user_guid="acct-guid", roles=["ROLE_FINANCE_ACCT"], role_mask=0),
      ["staging", "approve", "1"],
    )

  monkeypatch.setattr(svc, "unbox_request", fake_unbox)

  with pytest.raises(HTTPException, match="Accounting manager"):
    asyncio.run(svc.finance_staging_approve_v1(_request_with_db(db)))


def test_finance_staging_reject_v1_submits_approval_metadata(monkeypatch):
  db = _FakeDb()

  async def fake_unbox(_request):
    return (
      SimpleNamespace(
        op="urn:finance:staging:reject:1",
        version=1,
        payload={"imports_recid": 15, "reason": "Duplicate charge"},
      ),
      SimpleNamespace(user_guid="mgr-guid", roles=["ROLE_FINANCE_APPR"], role_mask=0),
      ["staging", "reject", "1"],
    )

  monkeypatch.setattr(svc, "unbox_request", fake_unbox)

  response = asyncio.run(svc.finance_staging_reject_v1(_request_with_db(db)))

  assert response.payload == {"imports_recid": 15, "rejected": True}
  assert db.requests[0].op == "db:finance:staging:reject_import:1"
  assert db.requests[0].payload == {
    "imports_recid": 15,
    "approved_by": "mgr-guid",
    "reason": "Duplicate charge",
  }
