"""Regression tests for identity domain subdomain reorganization and RoleModule extraction."""

import importlib

import pytest


class TestSubdomainRenames:
  """Verify renamed subdomains are wired and old names are gone."""

  def test_identity_handler_subdomains(self):
    from queryregistry.identity.handler import HANDLERS

    expected = {
      "users", "auth", "sessions", "profiles",
      "roles", "enablements", "mcp_agents", "audit",
    }
    assert set(HANDLERS.keys()) == expected

  def test_old_subdomain_names_absent(self):
    from queryregistry.identity.handler import HANDLERS

    for old in ("accounts", "providers", "role_memberships"):
      assert old not in HANDLERS, f"Legacy subdomain '{old}' still registered"

  def test_accounts_package_gone(self):
    with pytest.raises(ImportError):
      importlib.import_module("queryregistry.identity.accounts")

  def test_providers_package_gone(self):
    with pytest.raises(ImportError):
      importlib.import_module("queryregistry.identity.providers")

  def test_role_memberships_package_gone(self):
    with pytest.raises(ImportError):
      importlib.import_module("queryregistry.identity.role_memberships")


class TestUsersSubdomain:
  """Verify identity.users op strings."""

  def test_exists_op(self):
    from queryregistry.identity.users import account_exists_request

    req = account_exists_request({"user_guid": "00000000-0000-0000-0000-000000000001"})
    assert req.op == "db:identity:users:exists:1"

  def test_read_by_discord_op(self):
    from queryregistry.identity.users import read_by_discord_request

    req = read_by_discord_request("123456")
    assert req.op == "db:identity:users:read_by_discord:1"


class TestAuthSubdomain:
  """Verify identity.auth op strings."""

  def test_get_by_provider_op(self):
    from queryregistry.identity.auth import get_by_provider_identifier_request

    req = get_by_provider_identifier_request(
      provider="microsoft",
      provider_identifier="00000000-0000-0000-0000-000000000001",
    )
    assert req.op == "db:identity:auth:get_by_provider_identifier:1"

  def test_create_from_provider_op(self):
    from queryregistry.identity.auth import create_from_provider_request

    req = create_from_provider_request(
      provider="google",
      provider_identifier="00000000-0000-0000-0000-000000000001",
      email="test@test.com",
      displayname="Test",
    )
    assert req.op == "db:identity:auth:create_from_provider:1"


class TestRolesSubdomain:
  """Verify identity.roles has membership ops + absorbed role ops from profiles."""

  def test_roles_dispatchers(self):
    from queryregistry.identity.roles.handler import DISPATCHERS

    expected_keys = {
      ("list", "1"), ("list_all", "1"), ("list_non_members", "1"),
      ("create", "1"), ("delete", "1"),
      ("get_roles", "1"), ("set_roles", "1"),
    }
    assert expected_keys == set(DISPATCHERS.keys())

  def test_membership_op(self):
    from queryregistry.identity.roles import list_all_role_memberships_request

    req = list_all_role_memberships_request()
    assert req.op == "db:identity:roles:list_all:1"

  def test_get_roles_op(self):
    from queryregistry.identity.roles import get_roles_request
    from queryregistry.identity.roles.models import UserGuidParams

    req = get_roles_request(UserGuidParams(guid="00000000-0000-0000-0000-000000000001"))
    assert req.op == "db:identity:roles:get_roles:1"

  def test_set_roles_op(self):
    from queryregistry.identity.roles import set_roles_request
    from queryregistry.identity.roles.models import SetRolesParams

    req = set_roles_request(SetRolesParams(guid="00000000-0000-0000-0000-000000000001", roles=1))
    assert req.op == "db:identity:roles:set_roles:1"


class TestProfilesNarrowed:
  """Verify profiles no longer has role operations."""

  def test_profiles_dispatchers_no_roles(self):
    from queryregistry.identity.profiles.handler import DISPATCHERS

    assert ("get_roles", "1") not in DISPATCHERS
    assert ("set_roles", "1") not in DISPATCHERS

  def test_profiles_retains_core_ops(self):
    from queryregistry.identity.profiles.handler import DISPATCHERS

    expected = {
      ("read", "1"), ("update", "1"), ("set_display", "1"),
      ("set_optin", "1"), ("set_profile_image", "1"),
      ("update_if_unedited", "1"), ("get_public_profile", "1"),
    }
    assert expected == set(DISPATCHERS.keys())


class TestRoleModuleExists:
  """Verify RoleModule is importable and has expected interface."""

  def test_import_role_module(self):
    from server.modules.role_module import RoleModule

    assert RoleModule is not None

  def test_role_module_has_expected_methods(self):
    from server.modules.role_module import RoleModule

    for method in (
      "load_roles", "refresh_role_cache", "upsert_role", "delete_role",
      "mask_to_names", "names_to_mask", "get_role_names",
      "get_user_roles", "user_has_role", "refresh_user_roles",
      "load_domain_role_map",
    ):
      assert hasattr(RoleModule, method), f"RoleModule missing method: {method}"


class TestAuthModuleNoRoleCache:
  """Verify AuthModule no longer contains RoleCache."""

  def test_no_role_cache_class(self):
    import inspect
    import server.modules.auth_module as mod

    source = inspect.getsource(mod)
    assert "class RoleCache" not in source, "RoleCache class still in auth_module.py"


class TestNoLegacyOpStrings:
  """Verify no legacy op string patterns exist in request builders."""

  def test_no_accounts_ops(self):
    from queryregistry.identity.users import account_exists_request

    req = account_exists_request({"user_guid": "00000000-0000-0000-0000-000000000001"})
    assert "identity:accounts:" not in req.op

  def test_no_providers_ops(self):
    from queryregistry.identity.auth import set_provider_request

    req = set_provider_request(
      guid="00000000-0000-0000-0000-000000000001",
      provider="microsoft",
    )
    assert "identity:providers:" not in req.op

  def test_no_role_memberships_ops(self):
    from queryregistry.identity.roles import list_all_role_memberships_request

    req = list_all_role_memberships_request()
    assert "identity:role_memberships:" not in req.op

  def test_no_profile_role_ops(self):
    from queryregistry.identity.profiles import __all__ as exports

    assert "get_roles_request" not in exports
    assert "set_roles_request" not in exports
