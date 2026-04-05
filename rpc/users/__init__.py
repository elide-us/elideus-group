"""User namespace for user-facing page and wiki RPCs.

All subdomains require ROLE_REGISTERED.
"""

from .pages.handler import handle_pages_request
from .wiki.handler import handle_wiki_request


HANDLERS: dict[str, callable] = {
  "pages": handle_pages_request,
  "wiki": handle_wiki_request
}

