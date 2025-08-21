from .microsoft.handler import handle_microsoft_request
from .session.handler import handle_session_request
from .google.handler import handle_google_request


HANDLERS: dict[str, callable] = {
  "microsoft": handle_microsoft_request,
  "session": handle_session_request,
  "google": handle_google_request,
}

