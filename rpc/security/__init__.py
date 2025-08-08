from .roles.handler import handle_roles_request
from .services import security_audit_log_v1

HANDLERS: dict[str, callable] = {
  "roles": handle_roles_request
}

DISPATCHERS: dict[tuple[str, str], callable] = {
  ("audit_log", "1"): security_audit_log_v1
}

