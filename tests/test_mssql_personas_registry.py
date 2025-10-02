from server.modules.providers import DbRunMode
from server.modules.providers.database.mssql_provider.db_helpers import Operation
from server.registry.assistant.personas import mssql as personas_mssql


def test_persona_lookup_query_targets_element_name():
  op = personas_mssql.get_by_name_v1({"name": "stark"})

  assert isinstance(op, Operation)
  assert op.kind is DbRunMode.JSON_ONE
  assert "FROM vw_personas vp" in op.sql
  assert "JOIN assistant_personas ap ON ap.element_name = vp.persona_name" in op.sql
  assert "WHERE vp.persona_name = ?" in op.sql
  assert "FOR JSON PATH" in op.sql
  assert "vp.model_name AS element_model" in op.sql
  assert op.params == ("stark",)
