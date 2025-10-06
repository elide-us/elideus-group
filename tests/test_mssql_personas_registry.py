import asyncio

from server.registry.content.assistant.personas import mssql as personas_mssql
from server.registry.types import DBResponse


def test_persona_lookup_query_targets_element_name(monkeypatch):
  captured: dict[str, object] = {}

  async def fake_run_json_one(sql, params=(), *, meta=None):
    captured["sql"] = sql
    captured["params"] = params
    return DBResponse()

  monkeypatch.setattr(personas_mssql, "run_json_one", fake_run_json_one)

  asyncio.run(personas_mssql.get_by_name_v1({"name": "stark"}))

  sql = captured["sql"].lower()
  assert "from vw_personas vp" in sql
  assert "join assistant_personas ap on ap.element_name = vp.persona_name" in sql
  assert "where vp.persona_name = ?" in sql
  assert "for json path" in sql
  assert "vp.model_name as element_model" in sql
  assert captured["params"] == ("stark",)
