"""RPC package initializer."""

# Import view registrations so that handlers are available
from . import admin  # noqa: F401
from .admin.vars import views as _admin_vars_views  # noqa: F401

from .views import format_response, register_formatter, get_view_registry

__all__ = ["format_response", "register_formatter", "get_view_registry"]
