"""Account namespace exposing account-level operations.

Requires ROLE_ACCOUNT_ADMIN.
"""

from .role.handler import handle_role_request

HANDLERS: dict[str, callable] = {
  "role": handle_role_request,
}
