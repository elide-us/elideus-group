"""Compatibility proxy for profile MSSQL implementations."""

from server.registry.account.profile.mssql import (  # noqa: F401
  get_profile_v1,
  set_display_v1,
  set_optin_v1,
  set_profile_image_v1,
  set_roles_v1,
  update_if_unedited_v1,
)
