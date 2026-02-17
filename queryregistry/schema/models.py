"""Pydantic models mirroring SQL table and view schemas for registry metadata.

View models are schema snapshots projected from SQL migration definitions and can
drift from a live database when migrations are applied out-of-band.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

__all__ = [
  "AccountActionsTable",
  "AccountUsersTable",
  "AssistantConversationsTable",
  "AssistantModelsTable",
  "AssistantPersonasTable",
  "AuthProvidersTable",
  "DiscordGuildsTable",
  "FrontendLinksTable",
  "FrontendRoutesTable",
  "ServicePagesTable",
  "SessionsDevicesTable",
  "StorageTypesTable",
  "SystemConfigTable",
  "SystemRolesTable",
  "UsersActionsLogTable",
  "UsersAuthTable",
  "UsersCreditsTable",
  "UsersEnablementsTable",
  "UsersProfileimgTable",
  "UsersRolesTable",
  "UsersSessionsTable",
  "UsersStorageCacheTable",
  "VwAccountUserProfile",
  "VwAccountUserSecurity",
  "VwAccountUserSessions",
  "VwConversationHistory",
  "VwPersonas",
  "VwUserSessionSecurity",
  "VwUsersStorageCache",
]


class SQLTableModel(BaseModel):
  """Base configuration for strict table schema payloads."""

  model_config = ConfigDict(extra="forbid")


class SQLViewModel(BaseModel):
  """Base configuration for strict SQL view projection payloads."""

  model_config = ConfigDict(extra="forbid")


class AuthProvidersTable(SQLTableModel):
  recid: int
  element_name: str
  element_display: str


class AccountUsersTable(SQLTableModel):
  recid: int
  element_guid: UUID
  element_rotkey: str
  element_rotkey_iat: datetime
  element_rotkey_exp: datetime
  element_email: str
  element_display: str
  providers_recid: int | None = None
  element_optin: bool
  element_created_on: datetime
  element_modified_on: datetime


class UsersSessionsTable(SQLTableModel):
  element_guid: UUID
  users_guid: UUID
  element_created_at: datetime
  element_token: str
  element_token_iat: datetime
  element_token_exp: datetime
  element_created_on: datetime
  element_modified_on: datetime


class StorageTypesTable(SQLTableModel):
  recid: int
  element_mimetype: str
  element_displaytype: str


class UsersAuthTable(SQLTableModel):
  recid: int
  users_guid: UUID
  providers_recid: int
  element_identifier: UUID
  element_linked: bool
  created_on: datetime
  modified_on: datetime


class AccountActionsTable(SQLTableModel):
  recid: int
  action_label: str
  action_description: str | None = None


class UsersStorageCacheTable(SQLTableModel):
  recid: int
  users_guid: UUID
  types_recid: int
  element_path: str
  element_filename: str
  element_public: bool
  element_created_on: datetime
  element_modified_on: datetime | None = None
  element_deleted: bool
  element_url: str | None = None
  element_reported: bool
  moderation_recid: int | None = None


class FrontendLinksTable(SQLTableModel):
  recid: int
  element_sequence: int
  element_title: str | None = None
  element_url: str | None = None


class FrontendRoutesTable(SQLTableModel):
  recid: int
  element_enablement: str
  element_roles: int
  element_sequence: int
  element_path: str | None = None
  element_name: str | None = None
  element_icon: str | None = None


class SystemConfigTable(SQLTableModel):
  recid: int
  element_key: str | None = None
  element_value: str | None = None


class UsersCreditsTable(SQLTableModel):
  users_guid: UUID
  element_credits: int
  element_reserve: int | None = None
  created_on: datetime
  modified_on: datetime


class UsersEnablementsTable(SQLTableModel):
  users_guid: UUID
  element_enablements: str
  created_on: datetime
  modified_on: datetime


class UsersProfileimgTable(SQLTableModel):
  users_guid: UUID
  element_base64: str | None = None
  providers_recid: int
  created_on: datetime
  modified_on: datetime


class UsersRolesTable(SQLTableModel):
  users_guid: UUID
  element_roles: int
  created_on: datetime
  modified_on: datetime


class SystemRolesTable(SQLTableModel):
  recid: int
  element_mask: int
  element_enablement: str
  element_name: str
  element_display: str | None = None


class DiscordGuildsTable(SQLTableModel):
  recid: int
  element_guild_id: str
  element_name: str
  element_joined_on: datetime
  element_member_count: int | None = None
  element_owner_id: str | None = None
  element_region: str | None = None
  element_left_on: datetime | None = None
  element_notes: str | None = None


class SessionsDevicesTable(SQLTableModel):
  element_guid: UUID
  sessions_guid: UUID
  element_token: str
  element_token_iat: datetime
  element_token_exp: datetime
  element_device_fingerprint: str | None = None
  element_user_agent: str | None = None
  element_ip_last_seen: str | None = None
  element_revoked_at: datetime | None = None
  providers_recid: int
  element_created_on: datetime
  element_modified_on: datetime
  element_rotkey: str
  element_rotkey_iat: datetime
  element_rotkey_exp: datetime


class UsersActionsLogTable(SQLTableModel):
  recid: int
  users_guid: UUID
  action_recid: int
  element_url: str | None = None
  element_logged_on: datetime
  element_notes: str | None = None


class AssistantModelsTable(SQLTableModel):
  recid: int
  element_name: str


class AssistantPersonasTable(SQLTableModel):
  recid: int
  element_name: str
  element_metadata: str | None = None
  element_created_on: datetime
  element_modified_on: datetime
  element_tokens: int
  element_prompt: str
  models_recid: int


class AssistantConversationsTable(SQLTableModel):
  recid: int
  personas_recid: int
  element_guild_id: str | None = None
  element_channel_id: str | None = None
  element_input: str | None = None
  element_output: str | None = None
  element_created_on: datetime
  element_tokens: int | None = None
  element_user_id: str | None = None
  models_recid: int


class ServicePagesTable(SQLTableModel):
  recid: int
  element_route_name: str
  element_pageblob: str
  element_version: int
  element_created_on: datetime
  element_modified_on: datetime
  element_created_by: UUID
  element_modified_by: UUID
  element_is_active: bool

class VwAccountUserSessions(SQLViewModel):
  user_guid: UUID
  user_roles: int
  user_created_on: datetime
  user_modified_on: datetime
  element_rotkey: str
  element_rotkey_iat: datetime
  element_rotkey_exp: datetime
  session_guid: UUID
  session_created_on: datetime
  session_modified_on: datetime
  device_guid: UUID
  device_created_on: datetime
  device_modified_on: datetime
  element_token: str
  element_token_iat: datetime
  element_token_exp: datetime
  element_revoked_at: datetime | None = None
  element_device_fingerprint: str | None = None
  element_user_agent: str | None = None
  element_ip_last_seen: str | None = None
  element_device_rotkey: str
  element_device_rotkey_iat: datetime
  element_device_rotkey_exp: datetime


class VwUserSessionSecurity(SQLViewModel):
  user_guid: UUID
  user_roles: int
  user_created_on: datetime
  user_modified_on: datetime
  element_rotkey: str
  element_rotkey_iat: datetime
  element_rotkey_exp: datetime
  session_guid: UUID
  session_created_on: datetime
  session_modified_on: datetime
  device_guid: UUID
  device_created_on: datetime
  device_modified_on: datetime
  element_token: str
  element_token_iat: datetime
  element_token_exp: datetime
  element_revoked_at: datetime | None = None
  element_device_fingerprint: str | None = None
  element_user_agent: str | None = None
  element_ip_last_seen: str | None = None
  element_device_rotkey: str
  element_device_rotkey_iat: datetime
  element_device_rotkey_exp: datetime


class VwAccountUserSecurity(SQLViewModel):
  user_guid: UUID
  element_rotkey: str
  element_rotkey_iat: datetime
  element_rotkey_exp: datetime
  session_guid: UUID
  device_guid: UUID
  element_token: str
  element_token_iat: datetime
  element_token_exp: datetime
  element_revoked_at: datetime | None = None
  element_device_fingerprint: str | None = None
  element_user_agent: str | None = None
  element_ip_last_seen: str | None = None
  element_device_rotkey: str
  element_device_rotkey_iat: datetime
  element_device_rotkey_exp: datetime


class VwAccountUserProfile(SQLViewModel):
  user_guid: UUID
  email: str
  display_name: str
  provider_name: str
  provider_display: str
  profile_image_base64: str | None = None
  opt_in: bool
  credits: int


class VwUsersStorageCache(SQLViewModel):
  recid: int
  users_guid: UUID
  types_recid: int
  element_path: str
  element_filename: str
  element_public: bool
  element_created_on: datetime
  element_modified_on: datetime | None = None
  element_deleted: bool
  element_mimetype: str
  element_displaytype: str


class VwConversationHistory(SQLViewModel):
  persona_name: str
  model_name: str
  element_token_allowance: int
  element_tokens_returned: int | None = None
  element_input: str | None = None
  element_output: str | None = None
  element_user_id: str | None = None
  element_guild_id: str | None = None
  element_channel_id: str | None = None


class VwPersonas(SQLViewModel):
  persona_name: str
  model_name: str
  token_allowance: int
  system_role_prompt: str
  element_created_on: datetime
  element_modified_on: datetime
