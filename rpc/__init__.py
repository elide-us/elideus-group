from .admin.handler import handle_admin_request
from .auth.handler import handle_auth_request
from .public.handler import handle_public_request
from .storage.handler import handle_storage_request
from .system.handler import handle_system_request
from .users.handler import handle_users_request


HANDLERS: dict[str, callable] = {
  "admin": handle_admin_request,
  "auth": handle_auth_request,
  "public": handle_public_request,
  "storage": handle_storage_request,
  "system": handle_system_request,
  "users": handle_users_request
}

