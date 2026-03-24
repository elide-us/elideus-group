import asyncio
import json
from types import SimpleNamespace

from queryregistry.finance.staging_purge_log import mssql
from queryregistry.finance.staging_purge_log.services import append_purged_keys


def test_check_purged_key_v1_uses_openjson(monkeypatch):
  captured = {}

  async def fake_run_json_one(sql, params=()):
    captured["sql"] = sql
    captured["params"] = params
    return {"rows": {"found": 1}}

  monkeypatch.setattr(mssql, "run_json_one", fake_run_json_one)

  result = asyncio.run(mssql.check_purged_key_v1({"vendors_recid": 7, "key": "INV-001"}))

  assert "OPENJSON" in captured["sql"]
  assert "$.batch_purged" in captured["sql"]
  assert captured["params"] == (7, "INV-001")
  assert result == {"rows": {"found": 1}}


class _FakeDb:
  def __init__(self):
    self.requests = []
    self._current = None

  async def run(self, request):
    self.requests.append(request)
    if request.op.endswith(":get_purge_log:1"):
      if self._current is None:
        return SimpleNamespace(rows=[])
      return SimpleNamespace(rows=[{"element_purged_keys": self._current}])
    if request.op.endswith(":upsert_purge_log:1"):
      self._current = request.payload["purged_keys_json"]
      return SimpleNamespace(rows=[])
    raise AssertionError(f"unexpected op {request.op}")


def test_append_purged_keys_creates_then_merges():
  db = _FakeDb()

  asyncio.run(append_purged_keys(db, vendors_recid=3, period_key="2025-01", new_keys=["A", "B"]))
  asyncio.run(append_purged_keys(db, vendors_recid=3, period_key="2025-01", new_keys=["B", "C"]))

  upserts = [r for r in db.requests if r.op.endswith(":upsert_purge_log:1")]
  assert len(upserts) == 2
  first = json.loads(upserts[0].payload["purged_keys_json"])
  second = json.loads(upserts[1].payload["purged_keys_json"])
  assert first["batch_purged"] == ["A", "B"]
  assert second["batch_purged"] == ["A", "B", "C"]
  assert upserts[1].payload["purged_count"] == 3
