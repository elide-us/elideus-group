from .services import auth_microsoft_user_login_v1


DISPATCHERS: dict[tuple[str, str], callable] = {
  ("user_login", "1"): auth_microsoft_user_login_v1
}

