from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from fastapi import HTTPException

JSONValue = Any

__all__ = [
  "ErrorDetail",
  "RPCServiceError",
  "as_http_exception",
  "from_http_exception",
  "bad_request",
  "conflict",
  "forbidden",
  "internal_error",
  "not_found",
  "service_unavailable",
  "unauthorized",
]


@dataclass(slots=True, frozen=True)
class ErrorDetail:
  code: str
  status_code: int
  message: str
  public_details: JSONValue | None = None
  diagnostic: str | None = None


class RPCServiceError(Exception):
  def __init__(self, *, code: str, status_code: int, message: str, public_details: JSONValue | None = None, diagnostic: str | None = None):
    super().__init__(message)
    self.detail = ErrorDetail(
      code=code,
      status_code=status_code,
      message=message,
      public_details=public_details,
      diagnostic=diagnostic,
    )

  def to_http_exception(self) -> HTTPException:
    return as_http_exception(self)


def _http_detail(detail: ErrorDetail) -> dict[str, JSONValue]:
  payload: dict[str, JSONValue] = {
    "code": detail.code,
    "message": detail.message,
  }
  if detail.public_details is not None:
    payload["details"] = detail.public_details
  return payload


def as_http_exception(error: RPCServiceError) -> HTTPException:
  payload = _http_detail(error.detail)
  exc = HTTPException(status_code=error.detail.status_code, detail=payload)
  setattr(exc, "rpc_error", error.detail)
  return exc


def from_http_exception(exc: HTTPException, *, default_code: str | None = None) -> RPCServiceError:
  existing = getattr(exc, "rpc_error", None)
  if isinstance(existing, ErrorDetail):
    return RPCServiceError(
      code=existing.code,
      status_code=existing.status_code,
      message=existing.message,
      public_details=existing.public_details,
      diagnostic=existing.diagnostic,
    )
  detail = getattr(exc, "detail", None)
  code = default_code or f"rpc.http.{getattr(exc, 'status_code', 500)}"
  public_details: JSONValue | None = None
  diagnostic: str | None = None
  if isinstance(detail, dict):
    message = str(detail.get("message") or detail.get("detail") or "") or "RPC error"
    code = str(detail.get("code") or code)
    public_details = detail.get("details")
    diagnostic = detail.get("diagnostic") or message
  elif isinstance(detail, str):
    message = detail
    diagnostic = detail
  else:
    message = str(detail) if detail is not None else exc.__class__.__name__
    diagnostic = message
  return RPCServiceError(
    code=code,
    status_code=getattr(exc, "status_code", 500),
    message=message,
    public_details=public_details,
    diagnostic=diagnostic,
  )


def _factory(status_code: int, code: str, message: str, *, public_details: JSONValue | None = None, diagnostic: str | None = None) -> RPCServiceError:
  return RPCServiceError(
    code=code,
    status_code=status_code,
    message=message,
    public_details=public_details,
    diagnostic=diagnostic or message,
  )


def bad_request(message: str, *, code: str = "rpc.bad_request", public_details: JSONValue | None = None, diagnostic: str | None = None) -> RPCServiceError:
  return _factory(400, code, message, public_details=public_details, diagnostic=diagnostic)


def unauthorized(message: str, *, code: str = "rpc.unauthorized", public_details: JSONValue | None = None, diagnostic: str | None = None) -> RPCServiceError:
  return _factory(401, code, message, public_details=public_details, diagnostic=diagnostic)


def forbidden(message: str, *, code: str = "rpc.forbidden", public_details: JSONValue | None = None, diagnostic: str | None = None) -> RPCServiceError:
  return _factory(403, code, message, public_details=public_details, diagnostic=diagnostic)


def not_found(message: str, *, code: str = "rpc.not_found", public_details: JSONValue | None = None, diagnostic: str | None = None) -> RPCServiceError:
  return _factory(404, code, message, public_details=public_details, diagnostic=diagnostic)


def conflict(message: str, *, code: str = "rpc.conflict", public_details: JSONValue | None = None, diagnostic: str | None = None) -> RPCServiceError:
  return _factory(409, code, message, public_details=public_details, diagnostic=diagnostic)


def internal_error(message: str = "Internal server error", *, code: str = "rpc.internal", public_details: JSONValue | None = None, diagnostic: str | None = None) -> RPCServiceError:
  return _factory(500, code, message, public_details=public_details, diagnostic=diagnostic)


def service_unavailable(message: str, *, code: str = "rpc.unavailable", public_details: JSONValue | None = None, diagnostic: str | None = None) -> RPCServiceError:
  return _factory(503, code, message, public_details=public_details, diagnostic=diagnostic)
