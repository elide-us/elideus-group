from server.modules.providers import DbRunMode
from server.modules.providers.database.mssql_provider import registry


def test_persona_lookup_query_targets_element_name():
  handler = registry.get_handler("db:assistant:personas:get_by_name:1")
  mode, sql, params = handler({"name": "stark"})

  assert mode is DbRunMode.ROW_ONE
  assert "FROM vw_personas vp" in sql
  assert "JOIN assistant_personas ap ON ap.element_name = vp.persona_name" in sql
  assert "WHERE vp.persona_name = ?;" in sql
  assert "vp.model_name AS element_model" in sql
  assert params == ("stark",)
