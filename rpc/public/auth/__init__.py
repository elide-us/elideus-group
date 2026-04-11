from .context.handler import handle_context_request


HANDLERS: dict[str, callable] = {
  'context': handle_context_request,
}
