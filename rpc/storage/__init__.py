"""Storage namespace for file handling operations.

Requires ROLE_STORAGE.
"""

from .files.handler import handle_files_request
from .provision.handler import handle_provision_request


HANDLERS: dict[str, callable] = {
  "files": handle_files_request,
  "provision": handle_provision_request,
}

