from .microsoft.handler import handle_microsoft_request
from .session.handler import handle_session_request
from .google.handler import handle_google_request
from .discord.handler import handle_discord_request
from .providers.handler import handle_providers_request


HANDLERS: dict[str, callable] = {
  "microsoft": handle_microsoft_request,
  "session": handle_session_request,
  "google": handle_google_request,
  "discord": handle_discord_request,
  "providers": handle_providers_request,
}

