from server.modules.providers.mssql_provider.registry import get_handler as get_mssql_handler
from server.modules.providers.postgres_provider.registry import get_handler as get_pg_handler


def test_mssql_get_by_provider_identifier_joins_sessions_tables():
  handler = get_mssql_handler("urn:users:providers:get_by_provider_identifier:1")
  _, sql, _ = handler({"provider": "microsoft", "provider_identifier": "pid"})
  sql_lower = sql.lower()
  assert "users_sessions" in sql_lower
  assert "sessions_devices" in sql_lower


def test_pg_get_by_provider_identifier_joins_sessions_tables():
  handler = get_pg_handler("urn:users:providers:get_by_provider_identifier:1")
  _, sql, _ = handler({"provider": "microsoft", "provider_identifier": "pid"})
  sql_lower = sql.lower()
  assert "users_sessions" in sql_lower
  assert "sessions_devices" in sql_lower
