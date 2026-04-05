"""System namespace for system administration RPCs.

Requires ROLE_SYSTEM_ADMIN.
"""

from .scheduled_tasks.handler import handle_scheduled_tasks_request
from .workflows.handler import handle_workflows_request

HANDLERS: dict[str, callable] = {
  "scheduled_tasks": handle_scheduled_tasks_request,
  "workflows": handle_workflows_request,
}
