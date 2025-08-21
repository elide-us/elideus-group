from .services import auth_google_oauth_login_v1


DISPATCHERS: dict[tuple[str, str], callable] = {
  ("oauth_login", "1"): auth_google_oauth_login_v1
}
