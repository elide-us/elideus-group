"""User namespace for profiles and authentication providers.

All subdomains require ROLE_REGISTERED.
"""

from .profile.handler import handle_profile_request
from .products.handler import handle_products_request
from .providers.handler import handle_providers_request


HANDLERS: dict[str, callable] = {
  "profile": handle_profile_request,
  "products": handle_products_request,
  "providers": handle_providers_request
}

