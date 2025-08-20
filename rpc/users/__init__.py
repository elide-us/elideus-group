"""User namespace for profiles and authentication providers.

All subdomains require ROLE_REGISTERED.
"""

from .profile.handler import handle_profile_request
from .providers.handler import handle_providers_request


HANDLERS: dict[str, callable] = {
  "profile": handle_profile_request,
  "providers": handle_providers_request
}

