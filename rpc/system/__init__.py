from .users.handler import handle_users_request
from .roles.handler import handle_roles_request
from .routes.handler import handle_routes_request
from .config.handler import handle_config_request

HANDLERS: dict[str, callable] = {
    "users": handle_users_request,
    "roles": handle_roles_request,
    "routes": handle_routes_request,
    "config": handle_config_request
}

