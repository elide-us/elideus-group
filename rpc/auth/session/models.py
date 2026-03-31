from typing import Any

from pydantic import BaseModel, Field


class AuthSessionGetTokenRequest1(BaseModel):
  provider: str
  id_token: str
  access_token: str
  fingerprint: str
  confirm: bool | None = None
  reauthToken: str | None = Field(default=None, alias='reAuthToken')


class AuthSessionRefreshTokenRequest1(BaseModel):
  fingerprint: str


class AuthSessionGetTokenResponse1(BaseModel):
  token: str
  profile: dict[str, Any]


class AuthSessionRefreshTokenResponse1(BaseModel):
  token: str


class AuthSessionOkResponse1(BaseModel):
  ok: bool = True


class AuthSessionGetSessionResponse1(BaseModel):
  session_guid: str | None = None
  device_guid: str | None = None
  user_guid: str | None = None
  issued_at: str | None = None
  expires_at: str | None = None
  device_fingerprint: str | None = None
  user_agent: str | None = None
  ip_last_seen: str | None = None
