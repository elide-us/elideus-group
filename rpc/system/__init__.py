"""System namespace for managing configuration and roles.

Requires ROLE_SYSTEM_ADMIN.
"""

from .roles.handler import handle_roles_request
from .scheduled_tasks.handler import handle_scheduled_tasks_request
from .workflows.handler import handle_workflows_request

HANDLERS: dict[str, callable] = {
  "roles": handle_roles_request,
  "scheduled_tasks": handle_scheduled_tasks_request,
  "workflows": handle_workflows_request,
}
