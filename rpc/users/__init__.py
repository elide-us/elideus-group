from .profile.handler import handle_profile_request
from .auth.handler import handle_auth_request


HANDLERS: dict[str, callable] = {
  "profile": handle_profile_request,
  "auth": handle_auth_request
}

