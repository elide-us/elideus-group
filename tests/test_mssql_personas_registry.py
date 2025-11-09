import asyncio
from typing import Any

from server.registry import get_handler
from server.registry.system.personas import mssql as personas_mssql
from server.registry.types import DBResponse


def test_persona_lookup_query_targets_element_name(monkeypatch):
  captured: dict[str, Any] = {}

  async def fake_run_json_one(sql, params):
    captured["sql"] = sql
    captured["params"] = tuple(params)
    return DBResponse(rows=[{"model_name": "mock", "element_model": "mock"}])

  monkeypatch.setattr(personas_mssql, "run_json_one", fake_run_json_one)

  handler = get_handler("db:system:personas:get_by_name:1")
  result = asyncio.run(handler({"name": "stark"}))

  sql = captured["sql"]
  assert "FROM vw_content_personas vp" in sql
  assert "JOIN assistant_personas ap ON ap.element_name = vp.persona_name" in sql
  assert "WHERE vp.persona_name = ?" in sql
  assert "FOR JSON PATH" in sql
  assert "vp.model_name AS element_model" in sql
  assert captured["params"] == ("stark",)
  assert result.rowcount == 1
