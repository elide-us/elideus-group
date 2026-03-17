"""System namespace for managing configuration and roles.

Requires ROLE_SYSTEM_ADMIN.
"""

from .batch_jobs.handler import handle_batch_jobs_request
from .config.handler import handle_config_request
from .conversations.handler import handle_conversations_request
from .models.handler import handle_models_request
from .roles.handler import handle_roles_request
from .storage.handler import handle_storage_request
from .tasks.handler import handle_tasks_request

HANDLERS: dict[str, callable] = {
  "batch_jobs": handle_batch_jobs_request,
  "config": handle_config_request,
  "conversations": handle_conversations_request,
  "models": handle_models_request,
  "roles": handle_roles_request,
  "storage": handle_storage_request,
  "tasks": handle_tasks_request,
}

