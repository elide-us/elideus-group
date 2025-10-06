from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from datetime import date, datetime, timezone
from decimal import Decimal
from uuid import UUID, uuid4
from typing import Any, Optional, TypeAlias

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

JSONPrimitive: TypeAlias = None | bool | int | float | str
JSONValue: TypeAlias = Any

URN_PATTERN = re.compile(r"^urn:(?:[a-z0-9_]+:){3,}[0-9]+$")

__all__ = [
  "AuthContext",
  "JSONValue",
  "RPCError",
  "RPCRequest",
  "RPCResponse",
  "ensure_json_serializable",
]


def ensure_json_serializable(value: Any, *, field_name: str) -> JSONValue:
  """Ensure the provided value can be serialised as JSON."""

  if value is None or isinstance(value, (str, int, float, bool)):
    return value
  if isinstance(value, (datetime, date)):
    return value.isoformat()
  if isinstance(value, UUID):
    return str(value)
  if isinstance(value, Decimal):
    return float(value)
  if isinstance(value, Mapping):
    return {
      str(key): ensure_json_serializable(sub_value, field_name=field_name)
      for key, sub_value in value.items()
    }
  if isinstance(value, set):
    return [ensure_json_serializable(item, field_name=field_name) for item in value]
  if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
    return [ensure_json_serializable(item, field_name=field_name) for item in value]
  raise TypeError(f"{field_name} must be JSON-serializable")


class AuthContext(BaseModel):
  user_guid: Optional[str] = None
  role_mask: int = 0
  roles: list[str] = Field(default_factory=list)
  provider: Optional[str] = None
  claims: dict[str, Any] = Field(default_factory=dict)


"""
This is an internal domain class, when a user makes a request
through the front end, we unpack the bearer token and get the
user GUID, we then look up their security details in the DB
and populate the below data structure which shepherds the
request internally until a response is generated.
"""
class RPCError(BaseModel):
  """Structured error returned from RPC handlers."""

  code: str
  message: str
  details: JSONValue | None = None

  model_config = ConfigDict(frozen=True, extra="forbid")


class RPCRequest(BaseModel):
  op: str = Field(pattern=URN_PATTERN.pattern)
  payload: JSONValue | None = None
  version: int
  request_id: str = Field(
    default_factory=lambda: str(uuid4()),
    description="Unique identifier generated for each RPC request",
  )

  timestamp: Optional[datetime] = Field(
    default_factory=lambda: datetime.now(timezone.utc),
    description="Client-supplied or default UTC timestamp",
  )

  user_guid: Optional[str] = Field(
    default=None,
    description="GUID extracted from bearer token",
  )
  roles: list[str] = Field(
    default_factory=list,
    description="Role names assigned to the user",
  )
  role_mask: int = Field(
    default=0,
    description="Bitmask representing user roles",
  )

  model_config = ConfigDict(extra="forbid")

  @field_validator("payload")
  @classmethod
  def _validate_payload(cls, value: Any | None):
    if value is None:
      return None
    return ensure_json_serializable(value, field_name="payload")

  @model_validator(mode="after")
  def _validate_version(self):
    parts = self.op.split(":")
    if len(parts) < 5:
      raise ValueError("op must include domain, subdomain, name, and version segments")
    version_segment = parts[-1]
    try:
      op_version = int(version_segment)
    except ValueError as exc:  # pragma: no cover - guarded by regex but defensive
      raise ValueError("op must terminate with an integer version segment") from exc
    if self.version != op_version:
      raise ValueError("version must match the operation version suffix")
    return self


"""
This is the internal RPC response class and contains the main
payload to be packaged into the server response object.
"""
class RPCResponse(BaseModel):
  op: str = Field(pattern=URN_PATTERN.pattern)
  payload: Any | None = None
  error: RPCError | None = None
  version: int

  timestamp: Optional[datetime] = Field(
    default_factory=lambda: datetime.now(timezone.utc),
    description="Server UTC timestamp of response generation",
  )

  model_config = ConfigDict(extra="forbid")

  @field_validator("payload")
  @classmethod
  def _validate_payload(cls, value: Any | None):
    if value is None:
      return None
    return ensure_json_serializable(value, field_name="payload")

  @field_validator("error")
  @classmethod
  def _freeze_error(cls, value: RPCError | None):
    return value

  @model_validator(mode="after")
  def _validate_version(self):
    parts = self.op.split(":")
    if len(parts) < 5:
      raise ValueError("op must include domain, subdomain, name, and version segments")
    version_segment = parts[-1]
    try:
      op_version = int(version_segment)
    except ValueError as exc:  # pragma: no cover
      raise ValueError("op must terminate with an integer version segment") from exc
    if self.version != op_version:
      raise ValueError("version must match the operation version suffix")
    if self.error and self.payload is not None:
      raise ValueError("payload must be null when an error is supplied")
    return self
