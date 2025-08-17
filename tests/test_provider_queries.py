from uuid import uuid4
from server.modules.providers.mssql_provider.registry import get_handler as get_mssql_handler
from server.modules.providers.postgres_provider.registry import get_handler as get_pg_handler

def test_mssql_get_by_provider_identifier_uses_user_view():
  handler = get_mssql_handler("urn:users:providers:get_by_provider_identifier:1")
  _, sql, _ = handler({"provider": "microsoft", "provider_identifier": str(uuid4())})
  sql = sql.lower()
  assert "vw_account_user_profile" in sql
  assert "v.credits" in sql
  assert "users_credits" not in sql

def test_pg_get_by_provider_identifier_uses_user_view():
  handler = get_pg_handler("urn:users:providers:get_by_provider_identifier:1")
  _, sql, _ = handler({"provider": "microsoft", "provider_identifier": str(uuid4())})
  sql = sql.lower()
  assert "vw_account_user_profile" in sql
  assert "v.credits" in sql
  assert "users_credits" not in sql

def test_mssql_get_profile_uses_profile_view():
  handler = get_mssql_handler("urn:users:profile:get_profile:1")
  _, sql, _ = handler({"guid": "gid"})
  sql = sql.lower()
  assert "vw_account_user_profile" in sql
  assert "v.credits" in sql
  assert "users_credits" not in sql

def test_mssql_get_rotkey_uses_security_view():
  handler = get_mssql_handler("db:users:session:get_rotkey:1")
  _, sql, _ = handler({"guid": "gid"})
  assert "vw_account_user_security" in sql.lower()

def test_pg_get_rotkey_uses_security_view():
  handler = get_pg_handler("db:users:session:get_rotkey:1")
  _, sql, _ = handler({"guid": "gid"})
  assert "vw_account_user_security" in sql.lower()

def test_mssql_get_by_access_token_uses_security_view():
  handler = get_mssql_handler("db:auth:session:get_by_access_token:1")
  _, sql, _ = handler({"access_token": "tok"})
  assert "vw_account_user_security" in sql.lower()
