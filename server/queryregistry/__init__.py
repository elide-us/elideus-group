"""Query registry namespace root.

Routes query operations to domain-specific handlers.
"""

from .account.handler import handle_account_request
from .finance.handler import handle_finance_request
from .handler import dispatch_query_request
from .public.handler import handle_public_request
from .system.handler import handle_system_request

HANDLERS: dict[str, callable] = {
  "account": handle_account_request,
  "finance": handle_finance_request,
  "public": handle_public_request,
  "system": handle_system_request,
}

__all__ = [
  "HANDLERS",
  "dispatch_query_request",
]
