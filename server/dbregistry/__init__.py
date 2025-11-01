"""Database registry namespace root.

Routes database operations to domain-specific handlers.
"""

from .account.handler import handle_account_request
from .finance.handler import handle_finance_request
from .handler import dispatch_db_request
from .system.handler import handle_system_request

HANDLERS: dict[str, callable] = {
  "account": handle_account_request,
  "finance": handle_finance_request,
  "system": handle_system_request,
}
