from .user.handler import (handle_user_request,
                           handle_auth_request)

HANDLERS: dict[str, callable] = {
  "user": handle_user_request,
  "auth": handle_auth_request
}
