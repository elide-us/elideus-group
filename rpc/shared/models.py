from pydantic import BaseModel


class ContentAccess(BaseModel):
  """Capability flags for a user's access to a content resource.

  Computed server-side by RoleModule.check_content_access() and included
  in RPC responses so the frontend can conditionally render controls
  (edit buttons, delete options, etc.) without inspecting tokens or GUIDs.
  """

  can_view: bool = True
  can_edit: bool = False
  can_delete: bool = False
  is_owner: bool = False
  is_admin: bool = False
