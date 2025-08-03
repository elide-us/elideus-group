from .account.handler import handle_account_request
from .auth.handler import handle_auth_request
from .public.handler import handle_frontend_request
from .storage.handler import handle_storage_request
from .system.handler import handle_system_request

HANDLERS: dict[str, callable] = {
  "system": handle_system_request,
  "account": handle_account_request,
  "auth": handle_auth_request,
  "frontend": handle_frontend_request,
  "storage": handle_storage_request
}
