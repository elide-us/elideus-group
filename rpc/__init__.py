"""RPC namespace root.

Exports handlers for each RPC domain with role-based access.
The auth and public domains are exempt from role checks.
"""

from .support.handler import handle_support_request
from .auth.handler import handle_auth_request
from .moderation.handler import handle_moderation_request
from .public.handler import handle_public_request
from .service.handler import handle_service_request
from .storage.handler import handle_storage_request
from .system.handler import handle_system_request
from .users.handler import handle_users_request
from .account.handler import handle_account_request
from .discord.handler import handle_discord_request


HANDLERS: dict[str, callable] = {
  "support": handle_support_request,
  "auth": handle_auth_request,
  "moderation": handle_moderation_request,
  "public": handle_public_request,
  "service": handle_service_request,
  "storage": handle_storage_request,
  "system": handle_system_request,
  "users": handle_users_request,
  "account": handle_account_request,
  "discord": handle_discord_request,
}


