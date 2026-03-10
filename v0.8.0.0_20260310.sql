SET ANSI_NULLS ON;
SET QUOTED_IDENTIFIER ON;

CREATE TABLE [dbo].[account_actions] (
  [recid] bigint identity(1,1) NOT NULL,
  [action_label] NVARCHAR(64) NOT NULL,
  [action_description] NVARCHAR(1024) NULL,
  CONSTRAINT [PK_account_actions] PRIMARY KEY ([recid])
);
CREATE TABLE [dbo].[auth_providers] (
  [recid] bigint identity(1,1) NOT NULL,
  [element_name] NVARCHAR(1024) NOT NULL,
  [element_display] NVARCHAR(1024) NOT NULL,
  CONSTRAINT [PK_auth_providers] PRIMARY KEY ([recid])
);
CREATE TABLE [dbo].[account_users] (
  [recid] bigint identity(1,1) NOT NULL,
  [element_guid] UNIQUEIDENTIFIER NOT NULL,
  [element_rotkey] nvarchar(max) NOT NULL,
  [element_rotkey_iat] datetimeoffset(7) NOT NULL DEFAULT (sysutcdatetime()),
  [element_rotkey_exp] datetimeoffset(7) NOT NULL,
  [element_email] NVARCHAR(1024) NOT NULL,
  [element_display] NVARCHAR(1024) NOT NULL,
  [providers_recid] BIGINT NULL,
  [element_optin] BIT NOT NULL DEFAULT ((0)),
  [element_created_on] datetimeoffset(7) NOT NULL DEFAULT (sysutcdatetime()),
  [element_modified_on] datetimeoffset(7) NOT NULL DEFAULT (sysutcdatetime()),
  CONSTRAINT [PK_account_users] PRIMARY KEY ([recid])
);
CREATE TABLE [dbo].[assistant_models] (
  [recid] bigint identity(1,1) NOT NULL,
  [element_name] NVARCHAR(50) NOT NULL,
  CONSTRAINT [PK_assistant_models] PRIMARY KEY ([recid])
);
CREATE TABLE [dbo].[assistant_personas] (
  [recid] bigint identity(1,1) NOT NULL,
  [element_name] NVARCHAR(256) NOT NULL,
  [element_metadata] nvarchar(max) NULL,
  [element_created_on] datetimeoffset(7) NOT NULL DEFAULT (sysutcdatetime()),
  [element_modified_on] datetimeoffset(7) NOT NULL DEFAULT (sysutcdatetime()),
  [element_tokens] INT NOT NULL,
  [element_prompt] nvarchar(max) NOT NULL,
  [models_recid] BIGINT NOT NULL,
  CONSTRAINT [PK_assistant_personas] PRIMARY KEY ([recid])
);
CREATE TABLE [dbo].[assistant_conversations] (
  [recid] bigint identity(1,1) NOT NULL,
  [personas_recid] BIGINT NOT NULL,
  [element_guild_id] NVARCHAR(64) NULL,
  [element_channel_id] NVARCHAR(64) NULL,
  [element_input] nvarchar(max) NULL,
  [element_output] nvarchar(max) NULL,
  [element_created_on] datetimeoffset(7) NOT NULL DEFAULT (sysutcdatetime()),
  [element_tokens] INT NULL,
  [element_user_id] NVARCHAR(64) NULL,
  [models_recid] BIGINT NOT NULL,
  CONSTRAINT [PK_assistant_conversations] PRIMARY KEY ([recid])
);
CREATE TABLE [dbo].[builder_categories] (
  [recid] bigint identity(1,1) NOT NULL,
  [element_name] NVARCHAR(1024) NULL,
  [element_sequence] INT NULL,
  CONSTRAINT [PK_builder_categories] PRIMARY KEY ([recid])
);
CREATE TABLE [dbo].[discord_guilds] (
  [recid] bigint identity(1,1) NOT NULL,
  [element_guild_id] NVARCHAR(64) NOT NULL,
  [element_name] NVARCHAR(256) NOT NULL,
  [element_joined_on] datetimeoffset(7) NOT NULL DEFAULT (sysutcdatetime()),
  [element_member_count] INT NULL,
  [element_owner_id] NVARCHAR(64) NULL,
  [element_region] NVARCHAR(128) NULL,
  [element_left_on] datetimeoffset(7) NULL,
  [element_notes] nvarchar(max) NULL,
  CONSTRAINT [PK_discord_guilds] PRIMARY KEY ([recid])
);
CREATE TABLE [dbo].[finance_accounts] (
  [element_guid] UNIQUEIDENTIFIER NOT NULL,
  [element_number] NVARCHAR(10) NOT NULL,
  [element_name] NVARCHAR(200) NOT NULL,
  [element_type] TINYINT NOT NULL,
  [element_parent] UNIQUEIDENTIFIER NULL,
  [is_posting] BIT NOT NULL DEFAULT ((1)),
  [element_status] TINYINT NOT NULL DEFAULT ((1)),
  [element_created_on] datetimeoffset(7) NOT NULL DEFAULT (sysutcdatetime()),
  [element_modified_on] datetimeoffset(7) NOT NULL DEFAULT (sysutcdatetime()),
  CONSTRAINT [PK_finance_accounts] PRIMARY KEY ([element_guid])
);
CREATE TABLE [dbo].[finance_numbers] (
  [recid] bigint identity(1,1) NOT NULL,
  [accounts_guid] UNIQUEIDENTIFIER NOT NULL,
  [element_prefix] NVARCHAR(10) NULL,
  [element_account_number] NVARCHAR(10) NOT NULL,
  [element_last_number] BIGINT NOT NULL DEFAULT ((1000)),
  [element_allocation_size] INT NOT NULL DEFAULT ((10)),
  [element_reset_policy] NVARCHAR(20) NOT NULL DEFAULT ('Never'),
  [element_created_on] datetimeoffset(7) NOT NULL DEFAULT (sysutcdatetime()),
  [element_modified_on] datetimeoffset(7) NOT NULL DEFAULT (sysutcdatetime()),
  CONSTRAINT [PK_finance_numbers] PRIMARY KEY ([recid])
);
CREATE TABLE [dbo].[finance_periods] (
  [element_guid] UNIQUEIDENTIFIER NOT NULL,
  [element_year] INT NOT NULL,
  [element_period_number] TINYINT NOT NULL,
  [element_period_name] NVARCHAR(50) NOT NULL,
  [element_start_date] DATE NOT NULL,
  [element_end_date] DATE NOT NULL,
  [element_days_in_period] TINYINT NOT NULL,
  [element_quarter_number] TINYINT NOT NULL,
  [element_has_closing_week] BIT NOT NULL DEFAULT ((0)),
  [element_is_leap_adjustment] BIT NOT NULL DEFAULT ((0)),
  [element_anchor_event] NVARCHAR(50) NULL,
  [element_close_type] TINYINT NOT NULL DEFAULT ((0)),
  [element_status] TINYINT NOT NULL DEFAULT ((1)),
  [element_created_on] datetimeoffset(7) NOT NULL DEFAULT (sysutcdatetime()),
  [element_modified_on] datetimeoffset(7) NOT NULL DEFAULT (sysutcdatetime()),
  CONSTRAINT [PK_finance_periods] PRIMARY KEY ([element_guid])
);
CREATE TABLE [dbo].[frontend_links] (
  [recid] bigint identity(1,1) NOT NULL,
  [element_sequence] INT NOT NULL DEFAULT ((0)),
  [element_title] nvarchar(max) NULL,
  [element_url] nvarchar(max) NULL,
  CONSTRAINT [PK_frontend_links] PRIMARY KEY ([recid])
);
CREATE TABLE [dbo].[frontend_routes] (
  [recid] bigint identity(1,1) NOT NULL,
  [element_enablement] NVARCHAR(1) NOT NULL DEFAULT ('0'),
  [element_roles] BIGINT NOT NULL DEFAULT ((0)),
  [element_sequence] INT NOT NULL DEFAULT ((0)),
  [element_path] NVARCHAR(512) NULL,
  [element_name] NVARCHAR(256) NULL,
  [element_icon] NVARCHAR(256) NULL,
  CONSTRAINT [PK_frontend_routes] PRIMARY KEY ([recid])
);
CREATE TABLE [dbo].[service_pages] (
  [recid] bigint identity(1,1) NOT NULL,
  [element_route_name] NVARCHAR(200) NOT NULL,
  [element_pageblob] nvarchar(max) NOT NULL,
  [element_version] INT NOT NULL DEFAULT ((1)),
  [element_created_on] datetimeoffset(7) NOT NULL DEFAULT (sysutcdatetime()),
  [element_modified_on] datetimeoffset(7) NOT NULL DEFAULT (sysutcdatetime()),
  [element_created_by] UNIQUEIDENTIFIER NOT NULL,
  [element_modified_by] UNIQUEIDENTIFIER NOT NULL,
  [element_is_active] BIT NOT NULL DEFAULT ((1)),
  CONSTRAINT [PK_service_pages] PRIMARY KEY ([recid])
);
CREATE TABLE [dbo].[users_sessions] (
  [element_guid] UNIQUEIDENTIFIER NOT NULL,
  [users_guid] UNIQUEIDENTIFIER NOT NULL,
  [element_created_at] datetimeoffset(7) NOT NULL DEFAULT (sysutcdatetime()),
  [element_token] nvarchar(max) NOT NULL DEFAULT (CONVERT([nvarchar](64),newid())),
  [element_token_iat] datetimeoffset(7) NOT NULL DEFAULT (sysutcdatetime()),
  [element_token_exp] datetimeoffset(7) NOT NULL DEFAULT (sysutcdatetime()),
  [element_created_on] datetimeoffset(7) NOT NULL DEFAULT (sysutcdatetime()),
  [element_modified_on] datetimeoffset(7) NOT NULL DEFAULT (sysutcdatetime()),
  CONSTRAINT [PK_users_sessions] PRIMARY KEY ([element_guid])
);
CREATE TABLE [dbo].[sessions_devices] (
  [element_guid] UNIQUEIDENTIFIER NOT NULL,
  [sessions_guid] UNIQUEIDENTIFIER NOT NULL,
  [element_token] nvarchar(max) NOT NULL,
  [element_token_iat] datetimeoffset(7) NOT NULL DEFAULT (sysutcdatetime()),
  [element_token_exp] datetimeoffset(7) NOT NULL DEFAULT (sysutcdatetime()),
  [element_device_fingerprint] NVARCHAR(512) NULL,
  [element_user_agent] NVARCHAR(1024) NULL,
  [element_ip_last_seen] NVARCHAR(64) NULL,
  [element_revoked_at] datetimeoffset(7) NULL,
  [providers_recid] BIGINT NOT NULL DEFAULT ((0)),
  [element_created_on] datetimeoffset(7) NOT NULL DEFAULT (sysutcdatetime()),
  [element_modified_on] datetimeoffset(7) NOT NULL DEFAULT (sysutcdatetime()),
  [element_rotkey] nvarchar(max) NOT NULL DEFAULT (''),
  [element_rotkey_iat] datetimeoffset(7) NOT NULL DEFAULT (sysutcdatetime()),
  [element_rotkey_exp] datetimeoffset(7) NOT NULL DEFAULT (sysutcdatetime()),
  CONSTRAINT [PK_sessions_devices] PRIMARY KEY ([element_guid])
);
CREATE TABLE [dbo].[storage_types] (
  [recid] bigint identity(1,1) NOT NULL,
  [element_mimetype] NVARCHAR(128) NOT NULL,
  [element_displaytype] NVARCHAR(64) NOT NULL,
  CONSTRAINT [PK_storage_types] PRIMARY KEY ([recid])
);
CREATE TABLE [dbo].[system_config] (
  [recid] bigint identity(1,1) NOT NULL,
  [element_key] NVARCHAR(1024) NULL,
  [element_value] nvarchar(max) NULL,
  CONSTRAINT [PK_system_config] PRIMARY KEY ([recid])
);
CREATE TABLE [dbo].[system_edt_mappings] (
  [recid] bigint identity(1,1) NOT NULL,
  [element_name] NVARCHAR(64) NOT NULL,
  [element_mssql_type] NVARCHAR(128) NOT NULL,
  [element_postgresql_type] NVARCHAR(128) NOT NULL,
  [element_mysql_type] NVARCHAR(128) NOT NULL,
  [element_python_type] NVARCHAR(64) NOT NULL,
  [element_odbc_type_code] INT NOT NULL,
  [element_max_length] INT NULL,
  [element_notes] NVARCHAR(2048) NULL,
  [element_created_on] datetimeoffset(7) NOT NULL DEFAULT (sysutcdatetime()),
  [element_modified_on] datetimeoffset(7) NOT NULL DEFAULT (sysutcdatetime()),
  CONSTRAINT [PK_system_edt_mappings] PRIMARY KEY ([recid])
);
CREATE TABLE [dbo].[system_roles] (
  [recid] bigint identity(1,1) NOT NULL,
  [element_mask] BIGINT NOT NULL DEFAULT ((0)),
  [element_enablement] NVARCHAR(1) NOT NULL DEFAULT ('0'),
  [element_name] NVARCHAR(1024) NOT NULL,
  [element_display] NVARCHAR(1024) NULL,
  CONSTRAINT [PK_system_roles] PRIMARY KEY ([recid])
);
CREATE TABLE [dbo].[system_schema_tables] (
  [recid] bigint identity(1,1) NOT NULL,
  [element_name] NVARCHAR(128) NOT NULL,
  [element_schema] NVARCHAR(64) NOT NULL DEFAULT ('dbo'),
  [element_description] NVARCHAR(1024) NULL,
  [element_created_on] datetimeoffset(7) NOT NULL DEFAULT (sysutcdatetime()),
  [element_modified_on] datetimeoffset(7) NOT NULL DEFAULT (sysutcdatetime()),
  CONSTRAINT [PK_system_schema_tables] PRIMARY KEY ([recid])
);
CREATE TABLE [dbo].[system_schema_columns] (
  [recid] bigint identity(1,1) NOT NULL,
  [tables_recid] BIGINT NOT NULL,
  [edt_recid] BIGINT NOT NULL,
  [element_name] NVARCHAR(128) NOT NULL,
  [element_ordinal] INT NOT NULL,
  [element_nullable] BIT NOT NULL DEFAULT ((0)),
  [element_default] NVARCHAR(512) NULL,
  [element_max_length] INT NULL,
  [element_is_primary_key] BIT NOT NULL DEFAULT ((0)),
  [element_is_identity] BIT NOT NULL DEFAULT ((0)),
  [element_description] NVARCHAR(1024) NULL,
  [element_created_on] datetimeoffset(7) NOT NULL DEFAULT (sysutcdatetime()),
  [element_modified_on] datetimeoffset(7) NOT NULL DEFAULT (sysutcdatetime()),
  CONSTRAINT [PK_system_schema_columns] PRIMARY KEY ([recid])
);
CREATE TABLE [dbo].[system_schema_foreign_keys] (
  [recid] bigint identity(1,1) NOT NULL,
  [tables_recid] BIGINT NOT NULL,
  [element_column_name] NVARCHAR(128) NOT NULL,
  [referenced_tables_recid] BIGINT NOT NULL,
  [element_referenced_column] NVARCHAR(128) NOT NULL,
  [element_created_on] datetimeoffset(7) NOT NULL DEFAULT (sysutcdatetime()),
  [element_modified_on] datetimeoffset(7) NOT NULL DEFAULT (sysutcdatetime()),
  CONSTRAINT [PK_system_schema_foreign_keys] PRIMARY KEY ([recid])
);
CREATE TABLE [dbo].[system_schema_indexes] (
  [recid] bigint identity(1,1) NOT NULL,
  [tables_recid] BIGINT NOT NULL,
  [element_name] NVARCHAR(256) NOT NULL,
  [element_columns] NVARCHAR(1024) NOT NULL,
  [element_is_unique] BIT NOT NULL DEFAULT ((0)),
  [element_created_on] datetimeoffset(7) NOT NULL DEFAULT (sysutcdatetime()),
  [element_modified_on] datetimeoffset(7) NOT NULL DEFAULT (sysutcdatetime()),
  CONSTRAINT [PK_system_schema_indexes] PRIMARY KEY ([recid])
);
CREATE TABLE [dbo].[system_schema_views] (
  [recid] BIGINT IDENTITY(1, 1) NOT NULL,
  [element_name] NVARCHAR(128) NOT NULL,
  [element_schema] NVARCHAR(64) NOT NULL DEFAULT ('dbo'),
  [element_definition] nvarchar(max) NOT NULL,
  [element_description] NVARCHAR(1024) NULL,
  [element_created_on] datetimeoffset(7) NOT NULL DEFAULT (sysutcdatetime()),
  [element_modified_on] datetimeoffset(7) NOT NULL DEFAULT (sysutcdatetime()),
  CONSTRAINT [PK_system_schema_views] PRIMARY KEY ([recid])
);
CREATE TABLE [dbo].[users_actions_log] (
  [recid] bigint identity(1,1) NOT NULL,
  [users_guid] UNIQUEIDENTIFIER NOT NULL,
  [action_recid] BIGINT NOT NULL,
  [element_url] NVARCHAR(1024) NULL,
  [element_logged_on] datetimeoffset(7) NOT NULL DEFAULT (sysutcdatetime()),
  [element_notes] NVARCHAR(1024) NULL,
  CONSTRAINT [PK_users_actions_log] PRIMARY KEY ([recid])
);
CREATE TABLE [dbo].[users_auth] (
  [recid] bigint identity(1,1) NOT NULL,
  [users_guid] UNIQUEIDENTIFIER NOT NULL,
  [providers_recid] BIGINT NOT NULL,
  [element_identifier] UNIQUEIDENTIFIER NOT NULL,
  [element_linked] BIT NOT NULL DEFAULT ((0)),
  [element_created_on] datetimeoffset(7) NOT NULL DEFAULT (sysutcdatetime()),
  [element_modified_on] datetimeoffset(7) NOT NULL DEFAULT (sysutcdatetime()),
  CONSTRAINT [PK_users_auth] PRIMARY KEY ([recid])
);
CREATE TABLE [dbo].[users_credits] (
  [users_guid] UNIQUEIDENTIFIER NOT NULL,
  [element_credits] INT NOT NULL,
  [element_reserve] INT NULL,
  [element_created_on] datetimeoffset(7) NOT NULL DEFAULT (sysutcdatetime()),
  [element_modified_on] datetimeoffset(7) NOT NULL DEFAULT (sysutcdatetime()),
  CONSTRAINT [PK_users_credits] PRIMARY KEY ([users_guid])
);
CREATE TABLE [dbo].[users_enablements] (
  [users_guid] UNIQUEIDENTIFIER NOT NULL,
  [element_enablements] nvarchar(max) NOT NULL DEFAULT ('0'),
  [element_created_on] datetimeoffset(7) NOT NULL DEFAULT (sysutcdatetime()),
  [element_modified_on] datetimeoffset(7) NOT NULL DEFAULT (sysutcdatetime()),
  CONSTRAINT [PK_users_enablements] PRIMARY KEY ([users_guid])
);
CREATE TABLE [dbo].[users_profileimg] (
  [users_guid] UNIQUEIDENTIFIER NOT NULL,
  [element_base64] nvarchar(max) NULL,
  [providers_recid] BIGINT NOT NULL,
  [element_created_on] datetimeoffset(7) NOT NULL DEFAULT (sysutcdatetime()),
  [element_modified_on] datetimeoffset(7) NOT NULL DEFAULT (sysutcdatetime()),
  CONSTRAINT [PK_users_profileimg] PRIMARY KEY ([users_guid])
);
CREATE TABLE [dbo].[users_roles] (
  [users_guid] UNIQUEIDENTIFIER NOT NULL,
  [element_roles] BIGINT NOT NULL DEFAULT ((0)),
  [element_created_on] datetimeoffset(7) NOT NULL DEFAULT (sysutcdatetime()),
  [element_modified_on] datetimeoffset(7) NOT NULL DEFAULT (sysutcdatetime()),
  CONSTRAINT [PK_users_roles] PRIMARY KEY ([users_guid])
);
CREATE TABLE [dbo].[users_storage_cache] (
  [recid] bigint identity(1,1) NOT NULL,
  [users_guid] UNIQUEIDENTIFIER NOT NULL,
  [types_recid] BIGINT NOT NULL,
  [element_path] NVARCHAR(512) NOT NULL,
  [element_filename] NVARCHAR(255) NOT NULL,
  [element_public] BIT NOT NULL DEFAULT ((0)),
  [element_created_on] datetimeoffset(7) NOT NULL DEFAULT (sysutcdatetime()),
  [element_modified_on] datetimeoffset(7) NOT NULL DEFAULT (sysutcdatetime()),
  [element_deleted] BIT NOT NULL DEFAULT ((0)),
  [element_url] NVARCHAR(1024) NULL,
  [element_reported] BIT NOT NULL DEFAULT ((0)),
  [moderation_recid] BIGINT NULL,
  CONSTRAINT [PK_users_storage_cache] PRIMARY KEY ([recid])
);

CREATE UNIQUE INDEX [UQ_account_actions_label] ON [dbo].[account_actions] ([action_label]);
CREATE UNIQUE INDEX [UQ_account_users_guid] ON [dbo].[account_users] ([element_guid]);
CREATE UNIQUE INDEX [UQ_discord_guilds_guild_id] ON [dbo].[discord_guilds] ([element_guild_id]);
CREATE UNIQUE INDEX [UQ_finance_numbers_account] ON [dbo].[finance_numbers] ([accounts_guid]);
CREATE UNIQUE INDEX [UQ_finance_periods_year_period] ON [dbo].[finance_periods] ([element_year], [element_period_number]);
CREATE UNIQUE INDEX [UQ_service_pages_route] ON [dbo].[service_pages] ([element_route_name]);
CREATE UNIQUE INDEX [UQ_storage_types_mimetype] ON [dbo].[storage_types] ([element_mimetype]);
CREATE UNIQUE INDEX [UQ_system_edt_mappings_name] ON [dbo].[system_edt_mappings] ([element_name]);
CREATE UNIQUE INDEX [UQ_system_schema_tables_schema_name] ON [dbo].[system_schema_tables] ([element_schema], [element_name]);
CREATE INDEX [IX_system_schema_columns_table_ordinal] ON [dbo].[system_schema_columns] ([tables_recid], [element_ordinal]);
CREATE UNIQUE INDEX [UQ_system_schema_columns_table_column] ON [dbo].[system_schema_columns] ([tables_recid], [element_name]);
CREATE UNIQUE INDEX [UQ_system_schema_foreign_keys_table_column] ON [dbo].[system_schema_foreign_keys] ([tables_recid], [element_column_name]);
CREATE UNIQUE INDEX [UQ_system_schema_indexes_table_name] ON [dbo].[system_schema_indexes] ([tables_recid], [element_name]);
CREATE UNIQUE INDEX [UQ_system_schema_views_schema_name] ON [dbo].[system_schema_views] ([element_schema], [element_name]);
CREATE UNIQUE INDEX [UQ_users_auth_element_identifier] ON [dbo].[users_auth] ([element_identifier]);
CREATE UNIQUE INDEX [UQ_users_storage_cache] ON [dbo].[users_storage_cache] ([users_guid], [element_path], [element_filename]);

ALTER TABLE [dbo].[account_users] ADD CONSTRAINT [FK_account_users_providers_recid_auth_providers] FOREIGN KEY ([providers_recid]) REFERENCES [dbo].[auth_providers] ([recid]);
ALTER TABLE [dbo].[assistant_personas] ADD CONSTRAINT [FK_assistant_personas_models_recid_assistant_models] FOREIGN KEY ([models_recid]) REFERENCES [dbo].[assistant_models] ([recid]);
ALTER TABLE [dbo].[assistant_conversations] ADD CONSTRAINT [FK_assistant_conversations_models_recid_assistant_models] FOREIGN KEY ([models_recid]) REFERENCES [dbo].[assistant_models] ([recid]);
ALTER TABLE [dbo].[assistant_conversations] ADD CONSTRAINT [FK_assistant_conversations_personas_recid_assistant_personas] FOREIGN KEY ([personas_recid]) REFERENCES [dbo].[assistant_personas] ([recid]);
ALTER TABLE [dbo].[finance_accounts] ADD CONSTRAINT [FK_finance_accounts_element_parent_finance_accounts] FOREIGN KEY ([element_parent]) REFERENCES [dbo].[finance_accounts] ([element_guid]);
ALTER TABLE [dbo].[finance_numbers] ADD CONSTRAINT [FK_finance_numbers_accounts_guid_finance_accounts] FOREIGN KEY ([accounts_guid]) REFERENCES [dbo].[finance_accounts] ([element_guid]);
ALTER TABLE [dbo].[service_pages] ADD CONSTRAINT [FK_service_pages_element_created_by_account_users] FOREIGN KEY ([element_created_by]) REFERENCES [dbo].[account_users] ([element_guid]);
ALTER TABLE [dbo].[service_pages] ADD CONSTRAINT [FK_service_pages_element_modified_by_account_users] FOREIGN KEY ([element_modified_by]) REFERENCES [dbo].[account_users] ([element_guid]);
ALTER TABLE [dbo].[users_sessions] ADD CONSTRAINT [FK_users_sessions_users_guid_account_users] FOREIGN KEY ([users_guid]) REFERENCES [dbo].[account_users] ([element_guid]);
ALTER TABLE [dbo].[sessions_devices] ADD CONSTRAINT [FK_sessions_devices_providers_recid_auth_providers] FOREIGN KEY ([providers_recid]) REFERENCES [dbo].[auth_providers] ([recid]);
ALTER TABLE [dbo].[sessions_devices] ADD CONSTRAINT [FK_sessions_devices_sessions_guid_users_sessions] FOREIGN KEY ([sessions_guid]) REFERENCES [dbo].[users_sessions] ([element_guid]);
ALTER TABLE [dbo].[system_schema_columns] ADD CONSTRAINT [FK_system_schema_columns_edt_recid_system_edt_mappings] FOREIGN KEY ([edt_recid]) REFERENCES [dbo].[system_edt_mappings] ([recid]);
ALTER TABLE [dbo].[system_schema_columns] ADD CONSTRAINT [FK_system_schema_columns_tables_recid_system_schema_tables] FOREIGN KEY ([tables_recid]) REFERENCES [dbo].[system_schema_tables] ([recid]);
ALTER TABLE [dbo].[system_schema_foreign_keys] ADD CONSTRAINT [FK_system_schema_foreign_keys_referenced_tables_recid_system_schema_tables] FOREIGN KEY ([referenced_tables_recid]) REFERENCES [dbo].[system_schema_tables] ([recid]);
ALTER TABLE [dbo].[system_schema_foreign_keys] ADD CONSTRAINT [FK_system_schema_foreign_keys_tables_recid_system_schema_tables] FOREIGN KEY ([tables_recid]) REFERENCES [dbo].[system_schema_tables] ([recid]);
ALTER TABLE [dbo].[system_schema_indexes] ADD CONSTRAINT [FK_system_schema_indexes_tables_recid_system_schema_tables] FOREIGN KEY ([tables_recid]) REFERENCES [dbo].[system_schema_tables] ([recid]);
ALTER TABLE [dbo].[users_actions_log] ADD CONSTRAINT [FK_users_actions_log_action_recid_account_actions] FOREIGN KEY ([action_recid]) REFERENCES [dbo].[account_actions] ([recid]);
ALTER TABLE [dbo].[users_actions_log] ADD CONSTRAINT [FK_users_actions_log_users_guid_account_users] FOREIGN KEY ([users_guid]) REFERENCES [dbo].[account_users] ([element_guid]);
ALTER TABLE [dbo].[users_auth] ADD CONSTRAINT [FK_users_auth_providers_recid_auth_providers] FOREIGN KEY ([providers_recid]) REFERENCES [dbo].[auth_providers] ([recid]);
ALTER TABLE [dbo].[users_auth] ADD CONSTRAINT [FK_users_auth_users_guid_account_users] FOREIGN KEY ([users_guid]) REFERENCES [dbo].[account_users] ([element_guid]);
ALTER TABLE [dbo].[users_credits] ADD CONSTRAINT [FK_users_credits_users_guid_account_users] FOREIGN KEY ([users_guid]) REFERENCES [dbo].[account_users] ([element_guid]);
ALTER TABLE [dbo].[users_enablements] ADD CONSTRAINT [FK_users_enablements_users_guid_account_users] FOREIGN KEY ([users_guid]) REFERENCES [dbo].[account_users] ([element_guid]);
ALTER TABLE [dbo].[users_profileimg] ADD CONSTRAINT [FK_users_profileimg_providers_recid_auth_providers] FOREIGN KEY ([providers_recid]) REFERENCES [dbo].[auth_providers] ([recid]);
ALTER TABLE [dbo].[users_profileimg] ADD CONSTRAINT [FK_users_profileimg_users_guid_account_users] FOREIGN KEY ([users_guid]) REFERENCES [dbo].[account_users] ([element_guid]);
ALTER TABLE [dbo].[users_roles] ADD CONSTRAINT [FK_users_roles_users_guid_account_users] FOREIGN KEY ([users_guid]) REFERENCES [dbo].[account_users] ([element_guid]);
ALTER TABLE [dbo].[users_storage_cache] ADD CONSTRAINT [FK_users_storage_cache_moderation_recid_account_actions] FOREIGN KEY ([moderation_recid]) REFERENCES [dbo].[account_actions] ([recid]);
ALTER TABLE [dbo].[users_storage_cache] ADD CONSTRAINT [FK_users_storage_cache_types_recid_storage_types] FOREIGN KEY ([types_recid]) REFERENCES [dbo].[storage_types] ([recid]);
ALTER TABLE [dbo].[users_storage_cache] ADD CONSTRAINT [FK_users_storage_cache_users_guid_account_users] FOREIGN KEY ([users_guid]) REFERENCES [dbo].[account_users] ([element_guid]);

CREATE VIEW dbo.vw_account_user_profile AS
SELECT
    au.element_guid         AS user_guid,
    au.element_email        AS email,
    au.element_display      AS display_name,
    ap.element_name         AS provider_name,
    ap.element_display      AS provider_display,
    up.element_base64       AS profile_image_base64,
    au.element_optin        AS opt_in,
    uc.element_credits      AS credits
FROM dbo.account_users       AS au
JOIN dbo.auth_providers      AS ap ON au.providers_recid = ap.recid
JOIN dbo.users_profileimg    AS up ON au.element_guid = up.users_guid
JOIN dbo.users_credits       AS uc ON au.element_guid = uc.users_guid;
CREATE VIEW dbo.vw_account_user_security AS
SELECT
    au.element_guid AS user_guid,
    au.element_rotkey,
    au.element_rotkey_iat,
    au.element_rotkey_exp,
    us.element_guid AS session_guid,
    sd.element_guid AS device_guid,
    sd.element_token,
    sd.element_token_iat,
    sd.element_token_exp,
    sd.element_revoked_at,
    sd.element_device_fingerprint,
    sd.element_user_agent,
    sd.element_ip_last_seen
FROM dbo.account_users AS au
JOIN dbo.users_sessions AS us ON au.element_guid = us.users_guid
JOIN dbo.sessions_devices AS sd ON us.element_guid = sd.sessions_guid;
CREATE VIEW dbo.vw_account_user_sessions AS
SELECT
    au.element_guid AS user_guid,
    ur.element_roles AS user_roles,
    au.element_created_on AS user_created_on,
    au.element_modified_on AS user_modified_on,
    au.element_rotkey,
    au.element_rotkey_iat,
    au.element_rotkey_exp,
    us.element_guid AS session_guid,
    us.element_created_on AS session_created_on,
    us.element_modified_on AS session_modified_on,
    sd.element_guid AS device_guid,
    sd.element_created_on AS device_created_on,
    sd.element_modified_on AS device_modified_on,
    sd.element_token,
    sd.element_token_iat,
    sd.element_token_exp,
    sd.element_revoked_at,
    sd.element_device_fingerprint,
    sd.element_user_agent,
    sd.element_ip_last_seen
FROM dbo.account_users AS au
JOIN dbo.users_sessions AS us ON au.element_guid = us.users_guid
JOIN dbo.users_roles AS ur ON au.element_guid = ur.users_guid
JOIN dbo.sessions_devices AS sd ON us.element_guid = sd.sessions_guid;
CREATE VIEW dbo.vw_content_conversations AS
SELECT
    ac.recid,
    ac.personas_recid,
    ap.element_name AS persona_name,
    ac.models_recid,
    am.element_name AS model_name,
    ac.element_guild_id,
    ac.element_channel_id,
    ac.element_user_id,
    ac.element_input,
    ac.element_output,
    ac.element_tokens,
    ac.element_created_on
FROM dbo.assistant_conversations AS ac
JOIN dbo.assistant_personas AS ap ON ap.recid = ac.personas_recid
JOIN dbo.assistant_models AS am ON am.recid = ac.models_recid;
CREATE VIEW dbo.vw_content_personas AS
SELECT
    ap.recid AS persona_recid,
    ap.element_name AS persona_name,
    ap.element_prompt AS persona_prompt,
    ap.element_tokens AS token_allowance,
    ap.models_recid,
    am.element_name AS model_name,
    ap.element_created_on,
    ap.element_modified_on
FROM dbo.assistant_personas AS ap
JOIN dbo.assistant_models AS am ON am.recid = ap.models_recid;
CREATE VIEW dbo.vw_content_public_user_files AS
SELECT
    usc.recid,
    usc.users_guid AS user_guid,
    usc.element_path,
    usc.element_filename,
    usc.element_url,
    usc.element_public,
    usc.element_deleted,
    usc.element_reported,
    usc.element_created_on,
    usc.element_modified_on,
    usc.moderation_recid,
    st.element_mimetype AS content_type,
    st.element_displaytype AS content_display_type
FROM dbo.users_storage_cache AS usc
JOIN dbo.storage_types AS st ON st.recid = usc.types_recid;
CREATE VIEW dbo.vw_content_public_user_profiles AS
SELECT
    au.element_guid AS user_guid,
    au.element_display AS display_name,
    au.element_email AS email,
    au.element_optin AS email_opt_in,
    up.element_base64 AS profile_image_base64
FROM dbo.account_users AS au
LEFT JOIN dbo.users_profileimg AS up ON up.users_guid = au.element_guid;
CREATE VIEW dbo.vw_content_user_roles AS
SELECT
    au.element_guid AS user_guid,
    au.element_display AS display_name,
    ISNULL(ur.element_roles, 0) AS role_mask
FROM dbo.account_users AS au
LEFT JOIN dbo.users_roles AS ur ON ur.users_guid = au.element_guid;
CREATE VIEW dbo.vw_conversation_history AS
SELECT
    ap.element_name AS persona_name,
    am.element_name AS model_name,
    ap.element_tokens AS element_token_allowance,
    ac.element_tokens AS element_tokens_returned,
    ac.element_input,
    ac.element_output,
    ac.element_user_id,
    ac.element_guild_id,
    ac.element_channel_id
FROM dbo.assistant_conversations ac
JOIN dbo.assistant_models am ON am.recid = ac.models_recid
JOIN dbo.assistant_personas ap ON ap.recid = ac.personas_recid;
CREATE VIEW dbo.vw_personas AS
SELECT
    ap.element_name AS persona_name,
    am.element_name AS model_name,
    ap.element_tokens AS token_allowance,
    ap.element_prompt AS system_role_prompt,
    ap.element_created_on,
    ap.element_modified_on
FROM dbo.assistant_personas AS ap
JOIN dbo.assistant_models AS am ON am.recid = ap.models_recid;
CREATE VIEW dbo.vw_user_session_security AS
SELECT
    au.element_guid AS user_guid,
    ur.element_roles AS user_roles,
    au.element_created_on AS user_created_on,
    au.element_modified_on AS user_modified_on,
    au.element_rotkey,
    au.element_rotkey_iat,
    au.element_rotkey_exp,
    us.element_guid AS session_guid,
    us.element_created_on AS session_created_on,
    us.element_modified_on AS session_modified_on,
    sd.element_guid AS device_guid,
    sd.element_created_on AS device_created_on,
    sd.element_modified_on AS device_modified_on,
    sd.element_token,
    sd.element_token_iat,
    sd.element_token_exp,
    sd.element_revoked_at,
    sd.element_device_fingerprint,
    sd.element_user_agent,
    sd.element_ip_last_seen,
    sd.element_rotkey AS element_device_rotkey,
    sd.element_rotkey_iat AS element_device_rotkey_iat,
    sd.element_rotkey_exp AS element_device_rotkey_exp
FROM dbo.account_users AS au
JOIN dbo.users_sessions AS us ON au.element_guid = us.users_guid
JOIN dbo.users_roles AS ur ON au.element_guid = ur.users_guid
JOIN dbo.sessions_devices AS sd ON us.element_guid = sd.sessions_guid;
CREATE VIEW dbo.vw_users_storage_cache AS
SELECT
    sc.recid,
    users_guid,
    types_recid,
    element_path,
    element_filename,
    element_public,
    sc.element_created_on,
    sc.element_modified_on,
    element_deleted,
    st.element_mimetype,
    st.element_displaytype
FROM dbo.users_storage_cache AS sc
JOIN dbo.storage_types AS st ON types_recid = st.recid;
