"""Identity query registry namespace."""

from __future__ import annotations

from .accounts.handler import handle_accounts_request
from .audit.handler import handle_audit_request
from .profiles.handler import handle_profiles_request
from .providers.handler import handle_providers_request
from .role_memberships.handler import handle_role_memberships_request
from .sessions.handler import handle_sessions_request

__all__ = ["HANDLERS"]

HANDLERS = {
  "accounts": handle_accounts_request,
  "audit": handle_audit_request,
  "profiles": handle_profiles_request,
  "providers": handle_providers_request,
  "role_memberships": handle_role_memberships_request,
  "sessions": handle_sessions_request,
}
