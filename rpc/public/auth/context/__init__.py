from .services import public_auth_get_user_context_v1


DISPATCHERS: dict[tuple[str, str], callable] = {
  ('get_user_context', '1'): public_auth_get_user_context_v1,
}
