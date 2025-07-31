from .microsoft.handler import handle_ms_request
from .session.handler import handle_session_request

HANDLERS: dict[str, callable] = {
  "microsoft": handle_ms_request,
  "session": handle_session_request,
}
