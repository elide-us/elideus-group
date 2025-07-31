from .services import user_login_v1

DISPATCHERS: dict[tuple[str, str], callable] = {
  ("user_login", "1"): user_login_v1
}
