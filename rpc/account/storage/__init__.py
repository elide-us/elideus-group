"""Account storage namespace for storage operations requiring account admin."""

from .provision.handler import handle_provision_request

HANDLERS: dict[str, callable] = {
  "provision": handle_provision_request,
}
