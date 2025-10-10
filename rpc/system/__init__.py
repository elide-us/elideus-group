"""System namespace for managing configuration and storage services.

Requires ROLE_SYSTEM_ADMIN.
"""

from .config.handler import handle_config_request
from .storage.handler import handle_storage_request

HANDLERS: dict[str, callable] = {
  "config": handle_config_request,
  "storage": handle_storage_request,
}

