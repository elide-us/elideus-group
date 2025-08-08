from .config.handler import handle_config_request
from .routes.handler import handle_routes_request


HANDLERS: dict[str, callable] = {
    "routes": handle_routes_request,
    "config": handle_config_request
}

