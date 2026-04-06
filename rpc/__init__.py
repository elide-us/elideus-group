"""RPC namespace root.

Exports handlers for each RPC domain with role-based access.
The auth and public domains are exempt from role checks.
"""

from .auth.handler import handle_auth_request
from .moderation.handler import handle_moderation_request
from .public.handler import handle_public_request
from .service.handler import handle_service_request
from .storage.handler import handle_storage_request
from .users.handler import handle_users_request
from .discord.handler import handle_discord_request
from .finance.handler import handle_finance_request


HANDLERS: dict[str, callable] = {
  "auth": handle_auth_request,
  "moderation": handle_moderation_request,
  "public": handle_public_request,
  "service": handle_service_request,
  "storage": handle_storage_request,
  "users": handle_users_request,
  "discord": handle_discord_request,
  "finance": handle_finance_request,
}

