"""Query registry namespace root.

Routes query operations to domain-specific handlers.
"""

from .account.handler import handle_account_request
from .content.handler import handle_content_request
from .finance.handler import handle_finance_request
from .handler import dispatch_query_request
from .identity.handler import handle_identity_request
from .system.handler import handle_system_request

HANDLERS: dict[str, callable] = {
  "account": handle_account_request,
  "content": handle_content_request,
  "finance": handle_finance_request,
  "identity": handle_identity_request,
  "system": handle_system_request,
}

__all__ = [
  "HANDLERS",
  "dispatch_query_request",
]
