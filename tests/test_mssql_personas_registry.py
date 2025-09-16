from server.modules.providers import DbRunMode
from server.modules.providers.database.mssql_provider import registry


def test_persona_lookup_query_targets_element_name():
  handler = registry.get_handler("db:assistant:personas:get_by_name:1")
  mode, sql, params = handler({"name": "stark"})

  assert mode is DbRunMode.ROW_ONE
  assert "FROM assistant_personas ap" in sql
  assert "WHERE ap.element_name = ?;" in sql
  assert "am.element_name AS element_model" in sql
  assert params == ("stark",)
