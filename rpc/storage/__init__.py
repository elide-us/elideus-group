"""Storage namespace for file handling operations.

Requires ROLE_STORAGE_ENABLED.
"""

from .files.handler import handle_files_request


HANDLERS: dict[str, callable] = {
  "files": handle_files_request,
}

