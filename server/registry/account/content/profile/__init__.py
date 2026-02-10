"""Compatibility layer for moved profile registry bindings."""

from server.registry.account.profile import (  # noqa: F401
  get_profile_request,
  get_roles_request,
  set_display_request,
  set_optin_request,
  set_profile_image_request,
  set_roles_request,
  update_if_unedited_request,
)
from server.registry.account.profile.model import (  # noqa: F401
  GuidParams,
  ProfileRecord,
  SetDisplayParams,
  SetOptInParams,
  SetProfileImageParams,
  SetRolesParams,
  UpdateIfUneditedParams,
)
