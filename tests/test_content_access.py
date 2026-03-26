"""Tests for generalized content access control."""

import pathlib
import sys
import types

from server.models import ContentAccess

# Ensure local rpc package resolution during tests.
rpc_pkg = types.ModuleType("rpc")
rpc_pkg.__path__ = [str(pathlib.Path(__file__).resolve().parent.parent / "rpc")]
sys.modules.setdefault("rpc", rpc_pkg)


class TestContentAccessModel:
  """Verify ContentAccess defaults and field behavior."""

  def test_default_anonymous(self):
    access = ContentAccess()
    assert access.can_view is True
    assert access.can_edit is False
    assert access.can_delete is False
    assert access.is_owner is False
    assert access.is_admin is False

  def test_all_true(self):
    access = ContentAccess(
      can_view=True,
      can_edit=True,
      can_delete=True,
      is_owner=True,
      is_admin=True,
    )
    assert access.can_edit is True
    assert access.is_admin is True


class TestCheckContentAccess:
  """Verify RoleModule.check_content_access logic."""

  def _make_role_module(self):
    """Create a minimal RoleModule with mocked role data."""
    from unittest.mock import MagicMock

    from server.modules.role_module import RoleModule

    app = MagicMock()
    module = RoleModule(app)
    module.roles = {
      "ROLE_REGISTERED": 1,
      "ROLE_SERVICE_ADMIN": 4611686018427387904,
    }
    return module

  def test_anonymous_user(self):
    rm = self._make_role_module()
    access = rm.check_content_access(
      user_guid=None,
      role_mask=0,
      owner_guid="aaa-bbb",
    )
    assert access.can_edit is False
    assert access.can_delete is False
    assert access.is_owner is False
    assert access.is_admin is False
    assert access.can_view is True

  def test_owner_match(self):
    rm = self._make_role_module()
    access = rm.check_content_access(
      user_guid="aaa-bbb",
      role_mask=1,
      owner_guid="aaa-bbb",
    )
    assert access.is_owner is True
    assert access.can_edit is True
    assert access.can_delete is False
    assert access.is_admin is False

  def test_non_owner_registered(self):
    rm = self._make_role_module()
    access = rm.check_content_access(
      user_guid="ccc-ddd",
      role_mask=1,
      owner_guid="aaa-bbb",
    )
    assert access.is_owner is False
    assert access.can_edit is False
    assert access.can_delete is False

  def test_service_admin_not_owner(self):
    rm = self._make_role_module()
    access = rm.check_content_access(
      user_guid="ccc-ddd",
      role_mask=4611686018427387904,
      owner_guid="aaa-bbb",
    )
    assert access.is_owner is False
    assert access.is_admin is True
    assert access.can_edit is True
    assert access.can_delete is True

  def test_owner_and_admin(self):
    rm = self._make_role_module()
    access = rm.check_content_access(
      user_guid="aaa-bbb",
      role_mask=4611686018427387905,
      owner_guid="aaa-bbb",
    )
    assert access.is_owner is True
    assert access.is_admin is True
    assert access.can_edit is True
    assert access.can_delete is True

  def test_custom_admin_mask(self):
    rm = self._make_role_module()
    rm.roles["ROLE_CONTENT_ADMIN"] = 64
    access = rm.check_content_access(
      user_guid="ccc-ddd",
      role_mask=64,
      owner_guid="aaa-bbb",
      admin_mask=64,
    )
    assert access.is_admin is True
    assert access.can_edit is True

  def test_no_owner_guid(self):
    rm = self._make_role_module()
    access = rm.check_content_access(
      user_guid="aaa-bbb",
      role_mask=1,
      owner_guid=None,
    )
    assert access.is_owner is False
    assert access.can_edit is False


class TestPublicPagesPermissionsModel:
  """Verify the RPC permissions model exists and has expected fields."""

  def test_import_and_defaults(self):
    from rpc.public.pages.models import PublicPagesPermissions1

    perms = PublicPagesPermissions1()
    assert perms.can_edit is False
    assert perms.can_delete is False
    assert perms.is_owner is False

  def test_get_page_model_has_permissions(self):
    from rpc.public.pages.models import PublicPagesGetPage1

    page = PublicPagesGetPage1(slug="test", title="Test", page_type="article")
    assert hasattr(page, "permissions")
    assert page.permissions.can_edit is False
