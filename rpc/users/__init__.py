"""User namespace for user-facing page and wiki RPCs.

All subdomains require ROLE_REGISTERED.
"""

from .pages.handler import handle_pages_request


HANDLERS: dict[str, callable] = {
  "pages": handle_pages_request
}
