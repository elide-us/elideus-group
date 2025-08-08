from .services import security_audit_log_v1

DISPATCHERS: dict[tuple[str, str], callable] = {
  # Requires ROLE_SECURITY_ADMIN.
  ("audit_log", "1"): security_audit_log_v1
}
