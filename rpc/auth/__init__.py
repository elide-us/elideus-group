from .microsoft.handler import handle_microsoft_request
from .session.handler import handle_session_request


HANDLERS: dict[str, callable] = {
  "microsoft": handle_microsoft_request,
  "session": handle_session_request,
}

