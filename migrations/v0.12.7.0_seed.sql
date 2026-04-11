-- ============================================================================
-- TheOracleRPC v0.12.7.0 — IoService Gateway & Session Foundation
-- Date: 2026-04-11
-- Purpose:
--   Create the unified enumeration system, session management layer,
--   agent/client registration, IoService gateway registry, and
--   Discord table replacements. 13 new tables total.
--
--   Design reference: IoServiceGatewayDesign_v3.md
--
-- Tables created (Phase order):
--   Phase 1 (standalone):
--     service_enum_categories, service_enum_values
--   Phase 2 (deps on Phase 1 + existing):
--     system_sessions, system_session_tokens, system_session_devices,
--     service_agent_clients, service_agent_client_users, service_agent_auth_codes,
--     service_discord_guilds, service_discord_channels
--   Phase 3 (deps on Phase 1 + existing object tree):
--     system_objects_io_gateways, system_objects_gateway_identity_providers,
--     system_objects_gateway_method_bindings
--
-- UUID5 namespace: DECAFBAD-CAFE-FADE-BABE-C0FFEE420B67
-- Column naming: key_ / pub_ / priv_ / ref_
-- PK strategy: UNIQUEIDENTIFIER (UUID5 deterministic for seed, NEWID() for instance)
-- ============================================================================


-- ============================================================================
-- PHASE 1: Unified Enumeration System
-- ============================================================================

CREATE TABLE [dbo].[service_enum_categories] (
  [key_guid]              UNIQUEIDENTIFIER  NOT NULL,
  [pub_name]              NVARCHAR(128)     NOT NULL,
  [pub_display]           NVARCHAR(256)     NOT NULL,
  [pub_description]       NVARCHAR(512)     NULL,
  [priv_created_on]       DATETIMEOFFSET(7) NOT NULL  CONSTRAINT [DF_sec_created_on]  DEFAULT SYSUTCDATETIME(),
  [priv_modified_on]      DATETIMEOFFSET(7) NOT NULL  CONSTRAINT [DF_sec_modified_on] DEFAULT SYSUTCDATETIME(),
  CONSTRAINT [PK_service_enum_categories]      PRIMARY KEY CLUSTERED ([key_guid]),
  CONSTRAINT [UQ_service_enum_categories_name] UNIQUE ([pub_name])
);
GO

CREATE TABLE [dbo].[service_enum_values] (
  [key_guid]              UNIQUEIDENTIFIER  NOT NULL,
  [ref_category_guid]     UNIQUEIDENTIFIER  NOT NULL,
  [pub_name]              NVARCHAR(64)      NOT NULL,
  [pub_display]           NVARCHAR(128)     NOT NULL,
  [pub_sequence]          INT               NOT NULL  CONSTRAINT [DF_sev_sequence]    DEFAULT 0,
  [priv_created_on]       DATETIMEOFFSET(7) NOT NULL  CONSTRAINT [DF_sev_created_on]  DEFAULT SYSUTCDATETIME(),
  [priv_modified_on]      DATETIMEOFFSET(7) NOT NULL  CONSTRAINT [DF_sev_modified_on] DEFAULT SYSUTCDATETIME(),
  CONSTRAINT [PK_service_enum_values]            PRIMARY KEY CLUSTERED ([key_guid]),
  CONSTRAINT [FK_sev_category]                   FOREIGN KEY ([ref_category_guid]) REFERENCES [dbo].[service_enum_categories] ([key_guid]),
  CONSTRAINT [UQ_service_enum_values_cat_name]   UNIQUE ([ref_category_guid], [pub_name])
);
GO

CREATE INDEX [IX_sev_category] ON [dbo].[service_enum_values] ([ref_category_guid]);
GO

-- Seed: Categories
INSERT INTO [dbo].[service_enum_categories] ([key_guid], [pub_name], [pub_display], [pub_description]) VALUES
(N'2DD8626E-4DC5-5A7E-9B4E-09AF096C9DBD', N'session_types',       N'Session Types',       N'Discriminator for system_sessions.ref_session_type_guid'),
(N'DECD6C94-3A94-5F24-9A27-F23A8AE0BD1C', N'token_types',         N'Token Types',         N'Discriminator for system_session_tokens.ref_token_type_guid'),
(N'C3FE4194-456B-5045-BE28-D54E7A3B0BA9', N'gateway_transports',  N'Gateway Transports',  N'Transport protocol for IoService gateways'),
(N'7B22DEA3-9F3B-5EB8-8FCC-F4F5D3941D29', N'identity_strategies', N'Identity Strategies', N'Authentication strategy for gateway identity providers');
GO

-- Seed: Values — session_types
INSERT INTO [dbo].[service_enum_values] ([key_guid], [ref_category_guid], [pub_name], [pub_display], [pub_sequence]) VALUES
(N'184AEAD3-D35D-5882-A3C2-75BA58E6FB33', N'2DD8626E-4DC5-5A7E-9B4E-09AF096C9DBD', N'browser', N'Web Browser Session',    10),
(N'503A571B-2FAB-5828-AA12-E05FF018D4B7', N'2DD8626E-4DC5-5A7E-9B4E-09AF096C9DBD', N'agent',   N'MCP/API Agent Session',  20),
(N'A53CD0A9-C055-583B-9F84-53E54D35C1A4', N'2DD8626E-4DC5-5A7E-9B4E-09AF096C9DBD', N'bot',     N'Bot Service Session',    30);

-- Seed: Values — token_types
INSERT INTO [dbo].[service_enum_values] ([key_guid], [ref_category_guid], [pub_name], [pub_display], [pub_sequence]) VALUES
(N'8AA0F073-7CA1-5375-9989-67DB2688BDF5', N'DECD6C94-3A94-5F24-9A27-F23A8AE0BD1C', N'access',   N'Access Token',   10),
(N'8E312303-3EA8-5D6F-9341-D201D5A9ABA6', N'DECD6C94-3A94-5F24-9A27-F23A8AE0BD1C', N'refresh',  N'Refresh Token',  20),
(N'C5551771-3FBD-5357-9302-821DE44D73B8', N'DECD6C94-3A94-5F24-9A27-F23A8AE0BD1C', N'rotation', N'Rotation Token', 30);

-- Seed: Values — gateway_transports
INSERT INTO [dbo].[service_enum_values] ([key_guid], [ref_category_guid], [pub_name], [pub_display], [pub_sequence]) VALUES
(N'FD52AF68-3CCF-5350-BC9C-960F993216C1', N'C3FE4194-456B-5045-BE28-D54E7A3B0BA9', N'http_rpc',     N'HTTP RPC (POST /rpc)',   10),
(N'C40B4903-4FF5-51FF-A85F-71544100BC82', N'C3FE4194-456B-5045-BE28-D54E7A3B0BA9', N'http_sse',     N'HTTP SSE (MCP Streamable)', 20),
(N'ED664F8B-9C0C-5831-A446-13A67637BCB8', N'C3FE4194-456B-5045-BE28-D54E7A3B0BA9', N'websocket',    N'WebSocket (Discord)',    30),
(N'8D35C3D0-5318-589C-A614-4F5D8545796A', N'C3FE4194-456B-5045-BE28-D54E7A3B0BA9', N'http_rest',    N'HTTP REST API',          40),
(N'30FE8D44-2882-506D-B54A-508F2725441B', N'C3FE4194-456B-5045-BE28-D54E7A3B0BA9', N'electron_ipc', N'Electron IPC',           50);

-- Seed: Values — identity_strategies
INSERT INTO [dbo].[service_enum_values] ([key_guid], [ref_category_guid], [pub_name], [pub_display], [pub_sequence]) VALUES
(N'751A514C-5DC2-542C-A357-E28081C3EC08', N'7B22DEA3-9F3B-5EB8-8FCC-F4F5D3941D29', N'bearer_jwt',          N'Bearer JWT Token',           10),
(N'8A31AC80-F304-55EB-B028-CA4D66B846BC', N'7B22DEA3-9F3B-5EB8-8FCC-F4F5D3941D29', N'static_token',        N'Static API Token',           20),
(N'6260E49B-72E7-51C3-8543-42988433D5F2', N'7B22DEA3-9F3B-5EB8-8FCC-F4F5D3941D29', N'discord_user_id',     N'Discord User ID',            30),
(N'E1BA20E2-BA8F-59E3-BA4F-5874B2287CE9', N'7B22DEA3-9F3B-5EB8-8FCC-F4F5D3941D29', N'api_key',             N'API Key',                    40),
(N'37B8000D-0953-57B7-9E5A-C58A44CD0E37', N'7B22DEA3-9F3B-5EB8-8FCC-F4F5D3941D29', N'client_credentials',  N'OAuth Client Credentials',   50);
GO


-- ============================================================================
-- PHASE 2: Session Layer + Agent Registration + Discord Replacements
-- ============================================================================

-- system_sessions
CREATE TABLE [dbo].[system_sessions] (
  [key_guid]                UNIQUEIDENTIFIER  NOT NULL  CONSTRAINT [DF_ss_guid]        DEFAULT NEWID(),
  [ref_user_guid]           UNIQUEIDENTIFIER  NOT NULL,
  [ref_session_type_guid]   UNIQUEIDENTIFIER  NOT NULL,
  [pub_is_active]           BIT               NOT NULL  CONSTRAINT [DF_ss_active]      DEFAULT 1,
  [pub_revoked_at]          DATETIMEOFFSET(7) NULL,
  [pub_expires_at]          DATETIMEOFFSET(7) NOT NULL,
  [priv_created_on]         DATETIMEOFFSET(7) NOT NULL  CONSTRAINT [DF_ss_created_on]  DEFAULT SYSUTCDATETIME(),
  [priv_modified_on]        DATETIMEOFFSET(7) NOT NULL  CONSTRAINT [DF_ss_modified_on] DEFAULT SYSUTCDATETIME(),
  CONSTRAINT [PK_system_sessions]          PRIMARY KEY CLUSTERED ([key_guid]),
  CONSTRAINT [FK_ss_user]                  FOREIGN KEY ([ref_user_guid])         REFERENCES [dbo].[system_users] ([key_guid]),
  CONSTRAINT [FK_ss_session_type]          FOREIGN KEY ([ref_session_type_guid]) REFERENCES [dbo].[service_enum_values] ([key_guid])
);
GO

CREATE INDEX [IX_ss_user]         ON [dbo].[system_sessions] ([ref_user_guid]);
CREATE INDEX [IX_ss_session_type] ON [dbo].[system_sessions] ([ref_session_type_guid]);
CREATE INDEX [IX_ss_active]       ON [dbo].[system_sessions] ([pub_is_active]) WHERE [pub_is_active] = 1;
GO

-- system_session_tokens
-- Token cleanup requirements (DO NOT IMPLEMENT — scheduled task future):
--   - Expired tokens (pub_expires_at < SYSUTCDATETIME()): purge periodically
--   - Revoked tokens (pub_revoked_at IS NOT NULL): retain 90 days for audit, then purge
--   - Cleanup: daily scheduled task, idempotent DELETE with WHERE, log purge count
CREATE TABLE [dbo].[system_session_tokens] (
  [key_guid]                UNIQUEIDENTIFIER  NOT NULL  CONSTRAINT [DF_sst_guid]       DEFAULT NEWID(),
  [ref_session_guid]        UNIQUEIDENTIFIER  NOT NULL,
  [ref_token_type_guid]     UNIQUEIDENTIFIER  NOT NULL,
  [pub_token_hash]          NVARCHAR(512)     NOT NULL,
  [pub_scopes]              NVARCHAR(1024)    NULL,
  [pub_issued_at]           DATETIMEOFFSET(7) NOT NULL  CONSTRAINT [DF_sst_issued_at]  DEFAULT SYSUTCDATETIME(),
  [pub_expires_at]          DATETIMEOFFSET(7) NOT NULL,
  [pub_revoked_at]          DATETIMEOFFSET(7) NULL,
  [priv_created_on]         DATETIMEOFFSET(7) NOT NULL  CONSTRAINT [DF_sst_created_on] DEFAULT SYSUTCDATETIME(),
  CONSTRAINT [PK_system_session_tokens]    PRIMARY KEY CLUSTERED ([key_guid]),
  CONSTRAINT [FK_sst_session]              FOREIGN KEY ([ref_session_guid])    REFERENCES [dbo].[system_sessions] ([key_guid]),
  CONSTRAINT [FK_sst_token_type]           FOREIGN KEY ([ref_token_type_guid]) REFERENCES [dbo].[service_enum_values] ([key_guid])
);
GO

CREATE INDEX [IX_sst_session]    ON [dbo].[system_session_tokens] ([ref_session_guid]);
CREATE INDEX [IX_sst_token_type] ON [dbo].[system_session_tokens] ([ref_token_type_guid]);
CREATE INDEX [IX_sst_hash]       ON [dbo].[system_session_tokens] ([pub_token_hash]);
CREATE INDEX [IX_sst_expires]    ON [dbo].[system_session_tokens] ([pub_expires_at]) WHERE [pub_revoked_at] IS NULL;
GO

-- system_session_devices
CREATE TABLE [dbo].[system_session_devices] (
  [key_guid]                UNIQUEIDENTIFIER  NOT NULL  CONSTRAINT [DF_ssd_guid]       DEFAULT NEWID(),
  [ref_session_guid]        UNIQUEIDENTIFIER  NOT NULL,
  [pub_device_fingerprint]  NVARCHAR(512)     NULL,
  [pub_user_agent]          NVARCHAR(1024)    NULL,
  [pub_ip_address]          NVARCHAR(64)      NULL,
  [pub_last_seen_at]        DATETIMEOFFSET(7) NULL,
  [priv_created_on]         DATETIMEOFFSET(7) NOT NULL  CONSTRAINT [DF_ssd_created_on] DEFAULT SYSUTCDATETIME(),
  [priv_modified_on]        DATETIMEOFFSET(7) NOT NULL  CONSTRAINT [DF_ssd_modified_on] DEFAULT SYSUTCDATETIME(),
  CONSTRAINT [PK_system_session_devices]   PRIMARY KEY CLUSTERED ([key_guid]),
  CONSTRAINT [FK_ssd_session]              FOREIGN KEY ([ref_session_guid]) REFERENCES [dbo].[system_sessions] ([key_guid]),
  CONSTRAINT [UQ_ssd_session]              UNIQUE ([ref_session_guid])
);
GO

-- service_agent_clients
CREATE TABLE [dbo].[service_agent_clients] (
  [key_guid]                UNIQUEIDENTIFIER  NOT NULL  CONSTRAINT [DF_sac_guid]       DEFAULT NEWID(),
  [pub_client_id]           UNIQUEIDENTIFIER  NOT NULL  CONSTRAINT [DF_sac_client_id]  DEFAULT NEWID(),
  [pub_client_name]         NVARCHAR(256)     NOT NULL,
  [pub_redirect_uris]       NVARCHAR(MAX)     NULL,
  [pub_grant_types]         NVARCHAR(256)     NOT NULL  CONSTRAINT [DF_sac_grant]      DEFAULT N'authorization_code',
  [pub_response_types]      NVARCHAR(64)      NOT NULL  CONSTRAINT [DF_sac_resp]       DEFAULT N'code',
  [pub_scopes]              NVARCHAR(1024)    NOT NULL  CONSTRAINT [DF_sac_scopes]     DEFAULT N'mcp:schema:read',
  [pub_is_dcr]              BIT               NOT NULL  CONSTRAINT [DF_sac_dcr]        DEFAULT 0,
  [pub_is_active]           BIT               NOT NULL  CONSTRAINT [DF_sac_active]     DEFAULT 1,
  [pub_revoked_at]          DATETIMEOFFSET(7) NULL,
  [pub_ip_address]          NVARCHAR(64)      NULL,
  [pub_user_agent]          NVARCHAR(1024)    NULL,
  [priv_created_on]         DATETIMEOFFSET(7) NOT NULL  CONSTRAINT [DF_sac_created_on] DEFAULT SYSUTCDATETIME(),
  [priv_modified_on]        DATETIMEOFFSET(7) NOT NULL  CONSTRAINT [DF_sac_modified_on] DEFAULT SYSUTCDATETIME(),
  CONSTRAINT [PK_service_agent_clients]       PRIMARY KEY CLUSTERED ([key_guid]),
  CONSTRAINT [UQ_sac_client_id]               UNIQUE ([pub_client_id])
);
GO

-- service_agent_client_users
CREATE TABLE [dbo].[service_agent_client_users] (
  [key_guid]                UNIQUEIDENTIFIER  NOT NULL  CONSTRAINT [DF_sacu_guid]       DEFAULT NEWID(),
  [ref_client_guid]         UNIQUEIDENTIFIER  NOT NULL,
  [ref_user_guid]           UNIQUEIDENTIFIER  NOT NULL,
  [pub_is_active]           BIT               NOT NULL  CONSTRAINT [DF_sacu_active]     DEFAULT 1,
  [priv_created_on]         DATETIMEOFFSET(7) NOT NULL  CONSTRAINT [DF_sacu_created_on] DEFAULT SYSUTCDATETIME(),
  [priv_modified_on]        DATETIMEOFFSET(7) NOT NULL  CONSTRAINT [DF_sacu_modified_on] DEFAULT SYSUTCDATETIME(),
  CONSTRAINT [PK_service_agent_client_users]  PRIMARY KEY CLUSTERED ([key_guid]),
  CONSTRAINT [FK_sacu_client]                 FOREIGN KEY ([ref_client_guid]) REFERENCES [dbo].[service_agent_clients] ([key_guid]),
  CONSTRAINT [FK_sacu_user]                   FOREIGN KEY ([ref_user_guid])   REFERENCES [dbo].[system_users] ([key_guid]),
  CONSTRAINT [UQ_sacu_client_user]            UNIQUE ([ref_client_guid], [ref_user_guid])
);
GO

CREATE INDEX [IX_sacu_client] ON [dbo].[service_agent_client_users] ([ref_client_guid]);
CREATE INDEX [IX_sacu_user]   ON [dbo].[service_agent_client_users] ([ref_user_guid]);
GO

-- service_agent_auth_codes
-- Auth code cleanup requirements (DO NOT IMPLEMENT — scheduled task future):
--   - Expired + unconsumed (pub_expires_at < SYSUTCDATETIME() AND pub_consumed = 0): purge periodically
--   - Consumed (pub_consumed = 1): retain 30 days for audit, then purge
--   - Cleanup: daily, same scheduled task as token cleanup, idempotent
CREATE TABLE [dbo].[service_agent_auth_codes] (
  [key_guid]                UNIQUEIDENTIFIER  NOT NULL  CONSTRAINT [DF_saac_guid]       DEFAULT NEWID(),
  [ref_client_guid]         UNIQUEIDENTIFIER  NOT NULL,
  [ref_user_guid]           UNIQUEIDENTIFIER  NOT NULL,
  [pub_code]                NVARCHAR(256)     NOT NULL,
  [pub_code_challenge]      NVARCHAR(256)     NOT NULL,
  [pub_code_method]         NVARCHAR(16)      NOT NULL  CONSTRAINT [DF_saac_method]     DEFAULT N'S256',
  [pub_redirect_uri]        NVARCHAR(2048)    NOT NULL,
  [pub_scopes]              NVARCHAR(1024)    NOT NULL,
  [pub_consumed]            BIT               NOT NULL  CONSTRAINT [DF_saac_consumed]   DEFAULT 0,
  [pub_expires_at]          DATETIMEOFFSET(7) NOT NULL,
  [priv_created_on]         DATETIMEOFFSET(7) NOT NULL  CONSTRAINT [DF_saac_created_on] DEFAULT SYSUTCDATETIME(),
  CONSTRAINT [PK_service_agent_auth_codes]    PRIMARY KEY CLUSTERED ([key_guid]),
  CONSTRAINT [FK_saac_client]                 FOREIGN KEY ([ref_client_guid]) REFERENCES [dbo].[service_agent_clients] ([key_guid]),
  CONSTRAINT [FK_saac_user]                   FOREIGN KEY ([ref_user_guid])   REFERENCES [dbo].[system_users] ([key_guid])
);
GO

CREATE INDEX [IX_saac_client]  ON [dbo].[service_agent_auth_codes] ([ref_client_guid]);
CREATE INDEX [IX_saac_code]    ON [dbo].[service_agent_auth_codes] ([pub_code]) WHERE [pub_consumed] = 0;
CREATE INDEX [IX_saac_expires] ON [dbo].[service_agent_auth_codes] ([pub_expires_at]) WHERE [pub_consumed] = 0;
GO

-- service_discord_guilds (replaces discord_guilds)
CREATE TABLE [dbo].[service_discord_guilds] (
  [key_guid]                UNIQUEIDENTIFIER  NOT NULL,
  [pub_guild_id]            NVARCHAR(64)      NOT NULL,
  [pub_name]                NVARCHAR(256)     NOT NULL,
  [pub_member_count]        INT               NULL,
  [pub_owner_id]            NVARCHAR(64)      NULL,
  [pub_region]              NVARCHAR(128)     NULL,
  [pub_credits]             INT               NOT NULL  CONSTRAINT [DF_sdg_credits]     DEFAULT 0,
  [pub_joined_at]           DATETIMEOFFSET(7) NOT NULL  CONSTRAINT [DF_sdg_joined_at]   DEFAULT SYSUTCDATETIME(),
  [pub_left_at]             DATETIMEOFFSET(7) NULL,
  [pub_notes]               NVARCHAR(MAX)     NULL,
  [priv_created_on]         DATETIMEOFFSET(7) NOT NULL  CONSTRAINT [DF_sdg_created_on]  DEFAULT SYSUTCDATETIME(),
  [priv_modified_on]        DATETIMEOFFSET(7) NOT NULL  CONSTRAINT [DF_sdg_modified_on] DEFAULT SYSUTCDATETIME(),
  CONSTRAINT [PK_service_discord_guilds]      PRIMARY KEY CLUSTERED ([key_guid]),
  CONSTRAINT [UQ_sdg_guild_id]                UNIQUE ([pub_guild_id])
);
GO

-- service_discord_channels (replaces discord_channels)
CREATE TABLE [dbo].[service_discord_channels] (
  [key_guid]                UNIQUEIDENTIFIER  NOT NULL,
  [ref_guild_guid]          UNIQUEIDENTIFIER  NOT NULL,
  [pub_channel_id]          NVARCHAR(64)      NOT NULL,
  [pub_name]                NVARCHAR(256)     NULL,
  [pub_type]                NVARCHAR(32)      NULL,
  [pub_message_count]       BIGINT            NOT NULL  CONSTRAINT [DF_sdc_msg_count]   DEFAULT 0,
  [pub_last_activity_at]    DATETIMEOFFSET(7) NULL,
  [pub_notes]               NVARCHAR(MAX)     NULL,
  [priv_created_on]         DATETIMEOFFSET(7) NOT NULL  CONSTRAINT [DF_sdc_created_on]  DEFAULT SYSUTCDATETIME(),
  [priv_modified_on]        DATETIMEOFFSET(7) NOT NULL  CONSTRAINT [DF_sdc_modified_on] DEFAULT SYSUTCDATETIME(),
  CONSTRAINT [PK_service_discord_channels]    PRIMARY KEY CLUSTERED ([key_guid]),
  CONSTRAINT [FK_sdc_guild]                   FOREIGN KEY ([ref_guild_guid]) REFERENCES [dbo].[service_discord_guilds] ([key_guid]),
  CONSTRAINT [UQ_sdc_channel_id]              UNIQUE ([pub_channel_id])
);
GO

CREATE INDEX [IX_sdc_guild] ON [dbo].[service_discord_channels] ([ref_guild_guid]);
GO


-- ============================================================================
-- PHASE 3: IoService Gateway Registry (deps on existing object tree)
-- ============================================================================

-- Register new IoService modules first
INSERT INTO [dbo].[system_objects_modules] ([key_guid], [pub_name], [pub_state_attr], [pub_module_path]) VALUES
(N'372A3D8D-D4E8-5495-895A-1D8E2130ACF1', N'RpcIoServiceModule',     N'rpc_io',     N'server.modules.rpc_io_service_module'),
(N'3898D988-258E-5529-8218-8F053886D48E', N'McpIoServiceModule',     N'mcp_io',     N'server.modules.mcp_io_service_module'),
(N'21858AC7-0DAE-5356-BD16-817F329E85C9', N'DiscordIoServiceModule', N'discord_io', N'server.modules.discord_io_service_module');
GO

-- system_objects_io_gateways
CREATE TABLE [dbo].[system_objects_io_gateways] (
  [key_guid]                UNIQUEIDENTIFIER  NOT NULL,
  [pub_name]                NVARCHAR(128)     NOT NULL,
  [ref_transport_guid]      UNIQUEIDENTIFIER  NOT NULL,
  [pub_description]         NVARCHAR(512)     NULL,
  [ref_module_guid]         UNIQUEIDENTIFIER  NOT NULL,
  [pub_is_active]           BIT               NOT NULL  CONSTRAINT [DF_soig_active]     DEFAULT 1,
  [priv_created_on]         DATETIMEOFFSET(7) NOT NULL  CONSTRAINT [DF_soig_created_on] DEFAULT SYSUTCDATETIME(),
  [priv_modified_on]        DATETIMEOFFSET(7) NOT NULL  CONSTRAINT [DF_soig_modified_on] DEFAULT SYSUTCDATETIME(),
  CONSTRAINT [PK_system_objects_io_gateways]  PRIMARY KEY CLUSTERED ([key_guid]),
  CONSTRAINT [UQ_soig_name]                   UNIQUE ([pub_name]),
  CONSTRAINT [FK_soig_transport]              FOREIGN KEY ([ref_transport_guid]) REFERENCES [dbo].[service_enum_values] ([key_guid]),
  CONSTRAINT [FK_soig_module]                 FOREIGN KEY ([ref_module_guid])    REFERENCES [dbo].[system_objects_modules] ([key_guid])
);
GO

-- Seed: Gateways
INSERT INTO [dbo].[system_objects_io_gateways] ([key_guid], [pub_name], [ref_transport_guid], [pub_description], [ref_module_guid]) VALUES
(N'606C04E3-44F1-593D-9C8B-8006E0A377D3', N'rpc',     N'FD52AF68-3CCF-5350-BC9C-960F993216C1', N'HTTP RPC gateway — canonical baseline for browser and API clients.',            N'372A3D8D-D4E8-5495-895A-1D8E2130ACF1'),
(N'1287363D-8093-564A-A8CA-D0AE6985BDBD', N'mcp',     N'C40B4903-4FF5-51FF-A85F-71544100BC82', N'MCP Streamable HTTP gateway for Claude, Codex, and Copilot Studio.',            N'3898D988-258E-5529-8218-8F053886D48E'),
(N'16825F1A-EF4B-55DB-8D5A-898A5DFB69B1', N'discord',  N'ED664F8B-9C0C-5831-A446-13A67637BCB8', N'Discord WebSocket gateway bot.',                                                N'21858AC7-0DAE-5356-BD16-817F329E85C9'),
(N'37C5B8BD-698F-5182-82B9-33BC3FE4CD4D', N'api',     N'8D35C3D0-5318-589C-A614-4F5D8545796A', N'Future REST API gateway for external integrations.',                            N'372A3D8D-D4E8-5495-895A-1D8E2130ACF1');
GO

-- system_objects_gateway_identity_providers
CREATE TABLE [dbo].[system_objects_gateway_identity_providers] (
  [key_guid]                UNIQUEIDENTIFIER  NOT NULL,
  [ref_gateway_guid]        UNIQUEIDENTIFIER  NOT NULL,
  [ref_strategy_guid]       UNIQUEIDENTIFIER  NOT NULL,
  [pub_priority]            INT               NOT NULL  CONSTRAINT [DF_sogip_priority]    DEFAULT 0,
  [pub_description]         NVARCHAR(512)     NULL,
  [pub_is_active]           BIT               NOT NULL  CONSTRAINT [DF_sogip_active]      DEFAULT 1,
  [priv_created_on]         DATETIMEOFFSET(7) NOT NULL  CONSTRAINT [DF_sogip_created_on]  DEFAULT SYSUTCDATETIME(),
  [priv_modified_on]        DATETIMEOFFSET(7) NOT NULL  CONSTRAINT [DF_sogip_modified_on] DEFAULT SYSUTCDATETIME(),
  CONSTRAINT [PK_system_objects_gateway_identity_providers] PRIMARY KEY CLUSTERED ([key_guid]),
  CONSTRAINT [FK_sogip_gateway]   FOREIGN KEY ([ref_gateway_guid])  REFERENCES [dbo].[system_objects_io_gateways] ([key_guid]),
  CONSTRAINT [FK_sogip_strategy]  FOREIGN KEY ([ref_strategy_guid]) REFERENCES [dbo].[service_enum_values] ([key_guid]),
  CONSTRAINT [UQ_sogip_gw_strat]  UNIQUE ([ref_gateway_guid], [ref_strategy_guid])
);
GO

CREATE INDEX [IX_sogip_gateway] ON [dbo].[system_objects_gateway_identity_providers] ([ref_gateway_guid]);
GO

-- Seed: Gateway identity providers
INSERT INTO [dbo].[system_objects_gateway_identity_providers] ([key_guid], [ref_gateway_guid], [ref_strategy_guid], [pub_priority], [pub_description]) VALUES
-- RPC
(N'E942D883-C352-5C40-B0BF-9B1C14BB2FD5', N'606C04E3-44F1-593D-9C8B-8006E0A377D3', N'751A514C-5DC2-542C-A357-E28081C3EC08', 10, N'Session JWT from browser login'),
(N'E04AEFFC-A816-5496-94CD-74DF5F537B69', N'606C04E3-44F1-593D-9C8B-8006E0A377D3', N'6260E49B-72E7-51C3-8543-42988433D5F2', 20, N'Discord domain requests with x-discord-id header'),
-- MCP
(N'6C2ABC1A-A6A9-5A39-A845-C370F45C02F8', N'1287363D-8093-564A-A8CA-D0AE6985BDBD', N'8A31AC80-F304-55EB-B028-CA4D66B846BC', 10, N'MCP_AGENT_TOKEN env var for dev/admin'),
(N'AD1E353C-F9E8-5F05-8FB9-410966B8D764', N'1287363D-8093-564A-A8CA-D0AE6985BDBD', N'751A514C-5DC2-542C-A357-E28081C3EC08', 20, N'OAuth PKCE JWT for Claude.ai'),
(N'A3895791-D9C0-5313-A282-27B8583E1F99', N'1287363D-8093-564A-A8CA-D0AE6985BDBD', N'37B8000D-0953-57B7-9E5A-C58A44CD0E37', 30, N'Machine-to-machine for Codex Cloud'),
-- Discord
(N'AFFC1B4F-F7A4-5DEA-859F-662346B75D7B', N'16825F1A-EF4B-55DB-8D5A-898A5DFB69B1', N'6260E49B-72E7-51C3-8543-42988433D5F2', 10, N'Discord message author to provider link'),
-- API (future)
(N'3D38C155-EA80-5E5F-A89D-91285456D209', N'37C5B8BD-698F-5182-82B9-33BC3FE4CD4D', N'E1BA20E2-BA8F-59E3-BA4F-5874B2287CE9', 10, N'Static API key'),
(N'37A54031-54EF-5B17-BD15-DF426C731736', N'37C5B8BD-698F-5182-82B9-33BC3FE4CD4D', N'751A514C-5DC2-542C-A357-E28081C3EC08', 20, N'OAuth JWT for API clients');
GO

-- system_objects_gateway_method_bindings
CREATE TABLE [dbo].[system_objects_gateway_method_bindings] (
  [key_guid]                        UNIQUEIDENTIFIER  NOT NULL,
  [ref_gateway_guid]                UNIQUEIDENTIFIER  NOT NULL,
  [ref_method_guid]                 UNIQUEIDENTIFIER  NOT NULL,
  [pub_operation_name]              NVARCHAR(128)     NOT NULL,
  [pub_description]                 NVARCHAR(512)     NULL,
  [pub_required_scope]              NVARCHAR(128)     NULL,
  [ref_required_role_guid]          UNIQUEIDENTIFIER  NULL,
  [ref_required_entitlement_guid]   UNIQUEIDENTIFIER  NULL,
  [pub_is_read_only]                BIT               NOT NULL  CONSTRAINT [DF_sogmb_readonly]    DEFAULT 1,
  [pub_is_active]                   BIT               NOT NULL  CONSTRAINT [DF_sogmb_active]      DEFAULT 1,
  [priv_created_on]                 DATETIMEOFFSET(7) NOT NULL  CONSTRAINT [DF_sogmb_created_on]  DEFAULT SYSUTCDATETIME(),
  [priv_modified_on]                DATETIMEOFFSET(7) NOT NULL  CONSTRAINT [DF_sogmb_modified_on] DEFAULT SYSUTCDATETIME(),
  CONSTRAINT [PK_system_objects_gateway_method_bindings] PRIMARY KEY CLUSTERED ([key_guid]),
  CONSTRAINT [FK_sogmb_gateway]       FOREIGN KEY ([ref_gateway_guid])              REFERENCES [dbo].[system_objects_io_gateways] ([key_guid]),
  CONSTRAINT [FK_sogmb_method]        FOREIGN KEY ([ref_method_guid])               REFERENCES [dbo].[system_objects_module_methods] ([key_guid]),
  CONSTRAINT [FK_sogmb_role]          FOREIGN KEY ([ref_required_role_guid])         REFERENCES [dbo].[system_auth_roles] ([key_guid]),
  CONSTRAINT [FK_sogmb_entitlement]   FOREIGN KEY ([ref_required_entitlement_guid]) REFERENCES [dbo].[system_auth_entitlements] ([key_guid]),
  CONSTRAINT [UQ_sogmb_gw_op]         UNIQUE ([ref_gateway_guid], [pub_operation_name])
);
GO

CREATE INDEX [IX_sogmb_gateway] ON [dbo].[system_objects_gateway_method_bindings] ([ref_gateway_guid]);
CREATE INDEX [IX_sogmb_method]  ON [dbo].[system_objects_gateway_method_bindings] ([ref_method_guid]);
GO

-- NOTE: Method bindings will be seeded incrementally as each IoService module
-- is implemented. The table is ready; bindings are populated per-phase.


-- ============================================================================
-- PHASE 4: Seed Claude agent client (FA6CE2FC)
-- ============================================================================

INSERT INTO [dbo].[service_agent_clients]
  ([key_guid], [pub_client_id], [pub_client_name], [pub_redirect_uris],
   [pub_grant_types], [pub_response_types], [pub_scopes], [pub_is_dcr])
VALUES
  (NEWID(),
   N'FA6CE2FC-784A-419A-BC43-B5F778161C9C',
   N'Claude',
   N'https://claude.ai/api/mcp/auth_callback',
   N'authorization_code',
   N'code',
   N'mcp:schema:read mcp:data:read mcp:rpc:list',
   0);
GO

-- Link Claude agent to user
INSERT INTO [dbo].[service_agent_client_users]
  ([key_guid], [ref_client_guid], [ref_user_guid], [pub_is_active])
SELECT
  NEWID(),
  sac.[key_guid],
  N'60C28D8D-96D6-4463-8962-1214E915395B',
  1
FROM [dbo].[service_agent_clients] sac
WHERE sac.[pub_client_id] = N'FA6CE2FC-784A-419A-BC43-B5F778161C9C';
GO


-- ============================================================================
-- PHASE 5: Object Tree Self-Registration
-- ============================================================================

-- 5a: Register all 13 new tables
INSERT INTO [dbo].[system_objects_database_tables] ([key_guid], [pub_name], [pub_schema]) VALUES
(N'F3F35E03-D6A8-5BCC-9E0F-9E92F2D3A5A4', N'service_enum_categories',                      N'dbo'),
(N'F4F4783A-4E31-5F42-AD6D-E8BB0E5D8BCF', N'service_enum_values',                           N'dbo'),
(N'B8BD1C09-93FB-54E0-9924-F29F94E7F1AC', N'system_sessions',                               N'dbo'),
(N'C2254205-56A8-5F2D-B97A-F3EBC2C1BAF3', N'system_session_tokens',                         N'dbo'),
(N'43361C00-491A-508F-A418-208D3DFB35E3', N'system_session_devices',                        N'dbo'),
(N'CA0AF361-7F1B-5126-B1CC-D68F5452E37E', N'service_agent_clients',                         N'dbo'),
(N'0F9A194A-8B18-5201-B403-AD611C35E5D5', N'service_agent_client_users',                    N'dbo'),
(N'F9AF918E-B310-5415-B964-9138475125B7', N'service_agent_auth_codes',                      N'dbo'),
(N'79891A32-2D78-5706-9A2D-5F5FFC3F83D7', N'system_objects_io_gateways',                    N'dbo'),
(N'9341CA8A-1759-5664-AAF6-6351305B9730', N'system_objects_gateway_identity_providers',      N'dbo'),
(N'013CB8EE-96A1-5BDB-BE53-8CE9CA22049B', N'system_objects_gateway_method_bindings',         N'dbo'),
(N'A57AE808-EF52-53F9-856C-54B4C3410A9B', N'service_discord_guilds',                        N'dbo'),
(N'F856B061-45A7-5F05-874A-6A8D69132013', N'service_discord_channels',                      N'dbo');
GO

-- 5b: Register columns for all tables
-- Type GUIDs
DECLARE @T_UUID  UNIQUEIDENTIFIER = N'4D2EB10B-363E-5AF4-826A-9294146244E4';
DECLARE @T_STR   UNIQUEIDENTIFIER = N'0093B404-1EEE-563D-9135-4B9E7EECA7A2';
DECLARE @T_TEXT  UNIQUEIDENTIFIER = N'DCA18974-D648-5DFF-AEFB-122C081145AA';
DECLARE @T_INT32 UNIQUEIDENTIFIER = N'E3EDE0CE-2A03-501E-A796-3487BEA03B7B';
DECLARE @T_INT64 UNIQUEIDENTIFIER = N'362EB7D6-8ECF-58FA-9416-D4822410DF9F';
DECLARE @T_BOOL  UNIQUEIDENTIFIER = N'12B2F03B-E315-50A5-B631-E6B1EB961A17';
DECLARE @T_DTZ   UNIQUEIDENTIFIER = N'70F890D3-5AB5-5250-860E-4F7F9624190C';

-- Table GUIDs
DECLARE @TBL_SEC   UNIQUEIDENTIFIER = N'F3F35E03-D6A8-5BCC-9E0F-9E92F2D3A5A4'; -- service_enum_categories
DECLARE @TBL_SEV   UNIQUEIDENTIFIER = N'F4F4783A-4E31-5F42-AD6D-E8BB0E5D8BCF'; -- service_enum_values
DECLARE @TBL_SS    UNIQUEIDENTIFIER = N'B8BD1C09-93FB-54E0-9924-F29F94E7F1AC'; -- system_sessions
DECLARE @TBL_SST   UNIQUEIDENTIFIER = N'C2254205-56A8-5F2D-B97A-F3EBC2C1BAF3'; -- system_session_tokens
DECLARE @TBL_SSD   UNIQUEIDENTIFIER = N'43361C00-491A-508F-A418-208D3DFB35E3'; -- system_session_devices
DECLARE @TBL_SAC   UNIQUEIDENTIFIER = N'CA0AF361-7F1B-5126-B1CC-D68F5452E37E'; -- service_agent_clients
DECLARE @TBL_SACU  UNIQUEIDENTIFIER = N'0F9A194A-8B18-5201-B403-AD611C35E5D5'; -- service_agent_client_users
DECLARE @TBL_SAAC  UNIQUEIDENTIFIER = N'F9AF918E-B310-5415-B964-9138475125B7'; -- service_agent_auth_codes
DECLARE @TBL_SOIG  UNIQUEIDENTIFIER = N'79891A32-2D78-5706-9A2D-5F5FFC3F83D7'; -- system_objects_io_gateways
DECLARE @TBL_SOGIP UNIQUEIDENTIFIER = N'9341CA8A-1759-5664-AAF6-6351305B9730'; -- system_objects_gateway_identity_providers
DECLARE @TBL_SOGMB UNIQUEIDENTIFIER = N'013CB8EE-96A1-5BDB-BE53-8CE9CA22049B'; -- system_objects_gateway_method_bindings
DECLARE @TBL_SDG   UNIQUEIDENTIFIER = N'A57AE808-EF52-53F9-856C-54B4C3410A9B'; -- service_discord_guilds
DECLARE @TBL_SDC   UNIQUEIDENTIFIER = N'F856B061-45A7-5F05-874A-6A8D69132013'; -- service_discord_channels

-- service_enum_categories columns
INSERT INTO [dbo].[system_objects_database_columns] ([key_guid],[ref_table_guid],[ref_type_guid],[pub_name],[pub_ordinal],[pub_is_nullable],[pub_is_primary_key],[pub_is_identity],[pub_default],[pub_max_length]) VALUES
(N'09ADB7F8-D4C2-5885-9385-797F06787209',@TBL_SEC,@T_UUID,N'key_guid',        1,0,1,0,NULL,               NULL),
(N'C1F6CF31-D0F8-57B3-A80E-BD0ACF38CBBB',@TBL_SEC,@T_STR, N'pub_name',        2,0,0,0,NULL,               128),
(N'295D1BC5-D586-5B8D-ABB6-FAA0E42FED2A',@TBL_SEC,@T_STR, N'pub_display',      3,0,0,0,NULL,               256),
(N'A24C51DD-3EEA-551F-9A70-15FF74F6DCD0',@TBL_SEC,@T_STR, N'pub_description',  4,1,0,0,NULL,               512),
(N'C12A7031-FDBF-50C5-AC7E-F758409956F0',@TBL_SEC,@T_DTZ, N'priv_created_on',  5,0,0,0,N'SYSUTCDATETIME()',NULL),
(N'F2AC47C1-8793-5CE4-ACF4-F2BA135A06D5',@TBL_SEC,@T_DTZ, N'priv_modified_on', 6,0,0,0,N'SYSUTCDATETIME()',NULL);

-- service_enum_values columns
INSERT INTO [dbo].[system_objects_database_columns] ([key_guid],[ref_table_guid],[ref_type_guid],[pub_name],[pub_ordinal],[pub_is_nullable],[pub_is_primary_key],[pub_is_identity],[pub_default],[pub_max_length]) VALUES
(N'3CF8E90D-C44F-538F-A092-4D596A4CDFB2',@TBL_SEV,@T_UUID, N'key_guid',          1,0,1,0,NULL,               NULL),
(N'3C7EEA25-F502-5C63-A1AD-774EB8F2C9A5',@TBL_SEV,@T_UUID, N'ref_category_guid', 2,0,0,0,NULL,               NULL),
(N'1747A217-BCA4-50B8-B138-67659C2C013E',@TBL_SEV,@T_STR,  N'pub_name',          3,0,0,0,NULL,               64),
(N'85C090F5-E586-5763-A335-4B52B115B610',@TBL_SEV,@T_STR,  N'pub_display',       4,0,0,0,NULL,               128),
(N'67C809BB-EFBC-5926-99AC-F91FF0E6E374',@TBL_SEV,@T_INT32,N'pub_sequence',      5,0,0,0,N'0',              NULL),
(N'7FA231EE-2384-525E-BAB5-D16E3B8E9AB2',@TBL_SEV,@T_DTZ,  N'priv_created_on',   6,0,0,0,N'SYSUTCDATETIME()',NULL),
(N'E3D8A229-FE7A-5334-BF04-66C543EF44F9',@TBL_SEV,@T_DTZ,  N'priv_modified_on',  7,0,0,0,N'SYSUTCDATETIME()',NULL);

-- system_sessions columns
INSERT INTO [dbo].[system_objects_database_columns] ([key_guid],[ref_table_guid],[ref_type_guid],[pub_name],[pub_ordinal],[pub_is_nullable],[pub_is_primary_key],[pub_is_identity],[pub_default],[pub_max_length]) VALUES
(N'BA2D7FBB-E2B3-5AFF-B0BD-007EC188701A',@TBL_SS,@T_UUID,N'key_guid',              1,0,1,0,N'NEWID()',          NULL),
(N'D9D80FFE-6848-5E12-9C96-505C5FFD3417',@TBL_SS,@T_UUID,N'ref_user_guid',         2,0,0,0,NULL,               NULL),
(N'8382B476-05D5-58A2-80CF-526D61F6BD5B',@TBL_SS,@T_UUID,N'ref_session_type_guid', 3,0,0,0,NULL,               NULL),
(N'0EC6F80D-479B-56C2-9111-F9F8C19D30FD',@TBL_SS,@T_BOOL,N'pub_is_active',         4,0,0,0,N'1',              NULL),
(N'95D563F8-8635-55C9-9D45-954EAF3C976D',@TBL_SS,@T_DTZ, N'pub_revoked_at',        5,1,0,0,NULL,               NULL),
(N'1CDE6513-F86E-577D-A27A-1158064E1EF4',@TBL_SS,@T_DTZ, N'pub_expires_at',        6,0,0,0,NULL,               NULL),
(N'0899C99F-1DE2-5008-9AFD-DF080D84AE26',@TBL_SS,@T_DTZ, N'priv_created_on',       7,0,0,0,N'SYSUTCDATETIME()',NULL),
(N'0591C0AB-1039-52CD-9228-2A9AFEC31A85',@TBL_SS,@T_DTZ, N'priv_modified_on',      8,0,0,0,N'SYSUTCDATETIME()',NULL);

-- system_session_tokens columns
INSERT INTO [dbo].[system_objects_database_columns] ([key_guid],[ref_table_guid],[ref_type_guid],[pub_name],[pub_ordinal],[pub_is_nullable],[pub_is_primary_key],[pub_is_identity],[pub_default],[pub_max_length]) VALUES
(N'0735E1AC-2D49-5E5A-B7CB-6D1620E8AD24',@TBL_SST,@T_UUID,N'key_guid',            1,0,1,0,N'NEWID()',          NULL),
(N'A0601D6F-2335-5138-A798-62EE23CC675F',@TBL_SST,@T_UUID,N'ref_session_guid',     2,0,0,0,NULL,               NULL),
(N'9A50E7C4-9109-588C-90AF-FB04B8AC9DF2',@TBL_SST,@T_UUID,N'ref_token_type_guid',  3,0,0,0,NULL,               NULL),
(N'F73B7E0B-3E73-5DC8-BBD5-73A6DC586047',@TBL_SST,@T_STR, N'pub_token_hash',       4,0,0,0,NULL,               512),
(N'243E1A68-4171-5508-9AB0-97AC912C6CD4',@TBL_SST,@T_STR, N'pub_scopes',           5,1,0,0,NULL,               1024),
(N'25855ED7-E388-5CE6-A7FF-5284D4059524',@TBL_SST,@T_DTZ, N'pub_issued_at',        6,0,0,0,N'SYSUTCDATETIME()',NULL),
(N'049B6DDE-9476-54B4-AF58-D9FCDBF86A23',@TBL_SST,@T_DTZ, N'pub_expires_at',       7,0,0,0,NULL,               NULL),
(N'1E0E6D2B-70B0-589F-BD44-CD02D7B3E9F6',@TBL_SST,@T_DTZ, N'pub_revoked_at',       8,1,0,0,NULL,               NULL),
(N'FA7C7AA8-AE2D-5533-AF7E-D1C29F2F1441',@TBL_SST,@T_DTZ, N'priv_created_on',      9,0,0,0,N'SYSUTCDATETIME()',NULL);

-- system_session_devices columns
INSERT INTO [dbo].[system_objects_database_columns] ([key_guid],[ref_table_guid],[ref_type_guid],[pub_name],[pub_ordinal],[pub_is_nullable],[pub_is_primary_key],[pub_is_identity],[pub_default],[pub_max_length]) VALUES
(N'C125B1A9-205D-53CD-9B26-6F307A9960FB',@TBL_SSD,@T_UUID,N'key_guid',                1,0,1,0,N'NEWID()',          NULL),
(N'F2AC596A-9A20-58BA-B888-2B907E70B0B8',@TBL_SSD,@T_UUID,N'ref_session_guid',        2,0,0,0,NULL,               NULL),
(N'3597F5D6-AF2B-55DF-A33D-91ADDDF1C9F2',@TBL_SSD,@T_STR, N'pub_device_fingerprint',  3,1,0,0,NULL,               512),
(N'04035876-89C2-5746-90F2-F27F9CE1DA23',@TBL_SSD,@T_STR, N'pub_user_agent',          4,1,0,0,NULL,               1024),
(N'87875AC9-4658-5F6C-A6D9-2324925F5BD7',@TBL_SSD,@T_STR, N'pub_ip_address',          5,1,0,0,NULL,               64),
(N'74F098A7-615A-5816-A1CE-98FCE52116D9',@TBL_SSD,@T_DTZ, N'pub_last_seen_at',        6,1,0,0,NULL,               NULL),
(N'AA29EE18-AD0B-5A3B-A809-C5A8DD5EEAF3',@TBL_SSD,@T_DTZ, N'priv_created_on',         7,0,0,0,N'SYSUTCDATETIME()',NULL),
(N'35182F6B-D31F-538E-86A8-9B84056CDDBC',@TBL_SSD,@T_DTZ, N'priv_modified_on',        8,0,0,0,N'SYSUTCDATETIME()',NULL);

-- service_agent_clients columns
INSERT INTO [dbo].[system_objects_database_columns] ([key_guid],[ref_table_guid],[ref_type_guid],[pub_name],[pub_ordinal],[pub_is_nullable],[pub_is_primary_key],[pub_is_identity],[pub_default],[pub_max_length]) VALUES
(N'1948DBB8-2D10-5396-994B-CB7FFEF502E4',@TBL_SAC,@T_UUID,N'key_guid',           1, 0,1,0,N'NEWID()',          NULL),
(N'A6A6D0D2-6DDE-5F48-8BCF-19922382019F',@TBL_SAC,@T_UUID,N'pub_client_id',      2, 0,0,0,N'NEWID()',          NULL),
(N'BEFB61B2-EE0F-5A82-BF92-0E5934F4F961',@TBL_SAC,@T_STR, N'pub_client_name',    3, 0,0,0,NULL,               256),
(N'9A47A20B-7196-5E91-A587-77FE4D337E63',@TBL_SAC,@T_TEXT,N'pub_redirect_uris',  4, 1,0,0,NULL,               NULL),
(N'30EFAEB3-9439-527D-8B81-8015427DE8AE',@TBL_SAC,@T_STR, N'pub_grant_types',    5, 0,0,0,N'authorization_code', 256),
(N'3CA688E0-3E70-529F-A83D-FF2EDA860E36',@TBL_SAC,@T_STR, N'pub_response_types', 6, 0,0,0,N'code',            64),
(N'769EEAD4-F5DA-5786-8339-9B8D031D6F4F',@TBL_SAC,@T_STR, N'pub_scopes',         7, 0,0,0,N'mcp:schema:read', 1024),
(N'67D440A0-437A-5101-B8E4-85927F010091',@TBL_SAC,@T_BOOL,N'pub_is_dcr',         8, 0,0,0,N'0',              NULL),
(N'0AE6FF8E-6145-57D8-A983-F1B74301AF79',@TBL_SAC,@T_BOOL,N'pub_is_active',      9, 0,0,0,N'1',              NULL),
(N'5702D638-06C4-59C6-BD97-F6B8214925A1',@TBL_SAC,@T_DTZ, N'pub_revoked_at',     10,1,0,0,NULL,               NULL),
(N'C0D29269-EADD-59AD-B4E1-2855E2A3B238',@TBL_SAC,@T_STR, N'pub_ip_address',     11,1,0,0,NULL,               64),
(N'4D783211-7486-5AA6-A289-1D686FF47519',@TBL_SAC,@T_STR, N'pub_user_agent',     12,1,0,0,NULL,               1024),
(N'95867C74-BA92-52AA-B43E-B00105EF3579',@TBL_SAC,@T_DTZ, N'priv_created_on',    13,0,0,0,N'SYSUTCDATETIME()',NULL),
(N'D746E6C3-D37D-52FA-A35D-F6ADE7896E14',@TBL_SAC,@T_DTZ, N'priv_modified_on',   14,0,0,0,N'SYSUTCDATETIME()',NULL);

-- service_agent_client_users columns
INSERT INTO [dbo].[system_objects_database_columns] ([key_guid],[ref_table_guid],[ref_type_guid],[pub_name],[pub_ordinal],[pub_is_nullable],[pub_is_primary_key],[pub_is_identity],[pub_default],[pub_max_length]) VALUES
(N'58BE0763-33A1-5D31-A4F8-61D92404DD50',@TBL_SACU,@T_UUID,N'key_guid',        1,0,1,0,N'NEWID()',          NULL),
(N'815F9399-8DD9-5B2F-8BB7-D187DBA92E21',@TBL_SACU,@T_UUID,N'ref_client_guid', 2,0,0,0,NULL,               NULL),
(N'B96E544B-80E1-5913-8823-6B59E55BA6AD',@TBL_SACU,@T_UUID,N'ref_user_guid',   3,0,0,0,NULL,               NULL),
(N'9C1D64A1-7623-50D9-8A94-18D4EB38363F',@TBL_SACU,@T_BOOL,N'pub_is_active',   4,0,0,0,N'1',              NULL),
(N'522688AA-4686-5AD7-AAF9-4597F12C8D9A',@TBL_SACU,@T_DTZ, N'priv_created_on', 5,0,0,0,N'SYSUTCDATETIME()',NULL),
(N'A9E31166-B3E9-5B7B-B9D8-E1BCC7E10F9C',@TBL_SACU,@T_DTZ, N'priv_modified_on',6,0,0,0,N'SYSUTCDATETIME()',NULL);

-- service_agent_auth_codes columns
INSERT INTO [dbo].[system_objects_database_columns] ([key_guid],[ref_table_guid],[ref_type_guid],[pub_name],[pub_ordinal],[pub_is_nullable],[pub_is_primary_key],[pub_is_identity],[pub_default],[pub_max_length]) VALUES
(N'6BF9DEB9-3E9E-56FA-B440-82F23AD6F9AA',@TBL_SAAC,@T_UUID,N'key_guid',            1, 0,1,0,N'NEWID()',          NULL),
(N'577FFCE4-CC6B-5003-870F-31AB1FB45244',@TBL_SAAC,@T_UUID,N'ref_client_guid',     2, 0,0,0,NULL,               NULL),
(N'206766E3-9C33-5F35-9653-955EAC08E516',@TBL_SAAC,@T_UUID,N'ref_user_guid',       3, 0,0,0,NULL,               NULL),
(N'031BF7A1-F09E-506D-86F5-AC75A975BEA4',@TBL_SAAC,@T_STR, N'pub_code',            4, 0,0,0,NULL,               256),
(N'5B2CAFD6-8606-5E8F-BC16-B62F7E2A622C',@TBL_SAAC,@T_STR, N'pub_code_challenge',  5, 0,0,0,NULL,               256),
(N'A3AE226C-FA8F-58D8-8509-BA2ABCA77DD0',@TBL_SAAC,@T_STR, N'pub_code_method',     6, 0,0,0,N'S256',           16),
(N'CB99567C-817D-5FFC-8930-EC37FEBA5C96',@TBL_SAAC,@T_STR, N'pub_redirect_uri',    7, 0,0,0,NULL,               2048),
(N'EEE537A4-2CD7-5326-9A92-8B1D2DCB45D1',@TBL_SAAC,@T_STR, N'pub_scopes',          8, 0,0,0,NULL,               1024),
(N'44B8175F-F7C1-5F4D-B9F3-F9401B9104AA',@TBL_SAAC,@T_BOOL,N'pub_consumed',        9, 0,0,0,N'0',              NULL),
(N'30E6829D-C86B-5832-B87A-9E2C778D51C2',@TBL_SAAC,@T_DTZ, N'pub_expires_at',      10,0,0,0,NULL,               NULL),
(N'1EDBBDC9-E6EF-548A-B9A9-93710BDB9C52',@TBL_SAAC,@T_DTZ, N'priv_created_on',     11,0,0,0,N'SYSUTCDATETIME()',NULL);

-- system_objects_io_gateways columns
INSERT INTO [dbo].[system_objects_database_columns] ([key_guid],[ref_table_guid],[ref_type_guid],[pub_name],[pub_ordinal],[pub_is_nullable],[pub_is_primary_key],[pub_is_identity],[pub_default],[pub_max_length]) VALUES
(N'BAC56509-0B20-56A0-A68F-E0506959CE13',@TBL_SOIG,@T_UUID,N'key_guid',           1,0,1,0,NULL,               NULL),
(N'2D2FEDAF-ACFF-5945-8CCF-4DDAF82FA81E',@TBL_SOIG,@T_STR, N'pub_name',           2,0,0,0,NULL,               128),
(N'264B5090-3FFF-5E75-B5E8-A8D75FE1F5CC',@TBL_SOIG,@T_UUID,N'ref_transport_guid', 3,0,0,0,NULL,               NULL),
(N'6973249A-0008-5445-8D9E-B414E1CAFDB4',@TBL_SOIG,@T_STR, N'pub_description',    4,1,0,0,NULL,               512),
(N'688DB827-BD0B-5712-8EED-FB6AFD2A07FC',@TBL_SOIG,@T_UUID,N'ref_module_guid',    5,0,0,0,NULL,               NULL),
(N'E07B23CF-2CD8-52BD-A5E4-6D47BCF8DADA',@TBL_SOIG,@T_BOOL,N'pub_is_active',      6,0,0,0,N'1',              NULL),
(N'335AAFF4-2D83-57EE-8910-DBBECEE116A0',@TBL_SOIG,@T_DTZ, N'priv_created_on',    7,0,0,0,N'SYSUTCDATETIME()',NULL),
(N'5635A634-62C3-5984-9618-C4635499F017',@TBL_SOIG,@T_DTZ, N'priv_modified_on',   8,0,0,0,N'SYSUTCDATETIME()',NULL);

-- system_objects_gateway_identity_providers columns
INSERT INTO [dbo].[system_objects_database_columns] ([key_guid],[ref_table_guid],[ref_type_guid],[pub_name],[pub_ordinal],[pub_is_nullable],[pub_is_primary_key],[pub_is_identity],[pub_default],[pub_max_length]) VALUES
(N'5BCC7149-F2D8-53CA-8E4A-1414F28B0288',@TBL_SOGIP,@T_UUID,N'key_guid',           1,0,1,0,NULL,               NULL),
(N'06D0BBC7-CFFE-510F-ABDE-98760A908693',@TBL_SOGIP,@T_UUID,N'ref_gateway_guid',   2,0,0,0,NULL,               NULL),
(N'516B9623-A278-5590-AC70-A92593E22654',@TBL_SOGIP,@T_UUID,N'ref_strategy_guid',  3,0,0,0,NULL,               NULL),
(N'0ED9B068-0B79-5304-8ED0-952E037775BA',@TBL_SOGIP,@T_INT32,N'pub_priority',       4,0,0,0,N'0',              NULL),
(N'98FD01FD-DD77-5F31-A67B-C10AB7BF69A8',@TBL_SOGIP,@T_STR, N'pub_description',    5,1,0,0,NULL,               512),
(N'CFF37DF4-8144-50F8-BD6D-CF27E50EA78A',@TBL_SOGIP,@T_BOOL,N'pub_is_active',      6,0,0,0,N'1',              NULL),
(N'AEE250E7-6560-5F42-9BA3-AE5F1A208BE4',@TBL_SOGIP,@T_DTZ, N'priv_created_on',    7,0,0,0,N'SYSUTCDATETIME()',NULL),
(N'F50CCFC7-7349-5305-AA9B-00B2EA2A5FAD',@TBL_SOGIP,@T_DTZ, N'priv_modified_on',   8,0,0,0,N'SYSUTCDATETIME()',NULL);

-- system_objects_gateway_method_bindings columns
INSERT INTO [dbo].[system_objects_database_columns] ([key_guid],[ref_table_guid],[ref_type_guid],[pub_name],[pub_ordinal],[pub_is_nullable],[pub_is_primary_key],[pub_is_identity],[pub_default],[pub_max_length]) VALUES
(N'15391578-B683-5F3B-A0A0-47C4BAAC14CF',@TBL_SOGMB,@T_UUID,N'key_guid',                        1, 0,1,0,NULL,               NULL),
(N'ECA5AD93-7AC0-5EE0-8487-322FDBC54C69',@TBL_SOGMB,@T_UUID,N'ref_gateway_guid',                2, 0,0,0,NULL,               NULL),
(N'572B2D8A-5B21-5E6E-9FE9-8C3DE31AD0C0',@TBL_SOGMB,@T_UUID,N'ref_method_guid',                 3, 0,0,0,NULL,               NULL),
(N'2A9DCAC7-BE5E-55FE-859C-B52DF2A6FBC7',@TBL_SOGMB,@T_STR, N'pub_operation_name',              4, 0,0,0,NULL,               128),
(N'817D4D7E-FCC3-5AAF-A268-E4BB2FC6377E',@TBL_SOGMB,@T_STR, N'pub_description',                 5, 1,0,0,NULL,               512),
(N'F175A6B4-27A0-5DE8-B48E-D8CF3FBDBAFD',@TBL_SOGMB,@T_STR, N'pub_required_scope',              6, 1,0,0,NULL,               128),
(N'58B99E68-8685-577E-ACC5-05D306A4B2E0',@TBL_SOGMB,@T_UUID,N'ref_required_role_guid',          7, 1,0,0,NULL,               NULL),
(N'E1CC4DB0-2AF3-5A7D-832B-80F4D81B84C0',@TBL_SOGMB,@T_UUID,N'ref_required_entitlement_guid',   8, 1,0,0,NULL,               NULL),
(N'24DBBB03-17BD-5AB3-BDCD-DF664BBE9E9F',@TBL_SOGMB,@T_BOOL,N'pub_is_read_only',                9, 0,0,0,N'1',              NULL),
(N'FBFFA4D2-0C4A-5707-AD12-9AB54A7A545B',@TBL_SOGMB,@T_BOOL,N'pub_is_active',                   10,0,0,0,N'1',              NULL),
(N'36D152FF-5E06-550D-B694-1FC10C831A25',@TBL_SOGMB,@T_DTZ, N'priv_created_on',                 11,0,0,0,N'SYSUTCDATETIME()',NULL),
(N'D306870E-2934-53E8-B655-EEF1500FED3E',@TBL_SOGMB,@T_DTZ, N'priv_modified_on',                12,0,0,0,N'SYSUTCDATETIME()',NULL);

-- service_discord_guilds columns
INSERT INTO [dbo].[system_objects_database_columns] ([key_guid],[ref_table_guid],[ref_type_guid],[pub_name],[pub_ordinal],[pub_is_nullable],[pub_is_primary_key],[pub_is_identity],[pub_default],[pub_max_length]) VALUES
(N'81556366-4AD1-5DAF-9F2E-D857385399D6',@TBL_SDG,@T_UUID,N'key_guid',        1, 0,1,0,NULL,               NULL),
(N'B12B0508-99C0-566B-B664-668E5B511766',@TBL_SDG,@T_STR, N'pub_guild_id',    2, 0,0,0,NULL,               64),
(N'74BFFCB0-25B4-5A44-B8BC-F8BC30319857',@TBL_SDG,@T_STR, N'pub_name',        3, 0,0,0,NULL,               256),
(N'F84D426E-CBBF-5755-8349-0BB26978C530',@TBL_SDG,@T_INT32,N'pub_member_count',4, 1,0,0,NULL,               NULL),
(N'6EABE930-2CAD-59D4-9562-758BDD8C2743',@TBL_SDG,@T_STR, N'pub_owner_id',    5, 1,0,0,NULL,               64),
(N'6E602D37-F182-51C5-9710-DA104AFF4C4D',@TBL_SDG,@T_STR, N'pub_region',      6, 1,0,0,NULL,               128),
(N'D296CAA7-FDE6-5F61-A6B4-7DF8E051EA81',@TBL_SDG,@T_INT32,N'pub_credits',     7, 0,0,0,N'0',              NULL),
(N'A0EC47E2-E561-55FA-88B4-E7CD15341B58',@TBL_SDG,@T_DTZ, N'pub_joined_at',   8, 0,0,0,N'SYSUTCDATETIME()',NULL),
(N'E56F1844-2DFD-5B63-9002-FE4E25D36939',@TBL_SDG,@T_DTZ, N'pub_left_at',     9, 1,0,0,NULL,               NULL),
(N'A5B684D0-2B01-5FEA-9272-4F68739D4520',@TBL_SDG,@T_TEXT,N'pub_notes',       10,1,0,0,NULL,               NULL),
(N'53D2AC42-6812-5A78-801E-6858372D1113',@TBL_SDG,@T_DTZ, N'priv_created_on', 11,0,0,0,N'SYSUTCDATETIME()',NULL),
(N'C596D6CA-A008-5F92-8911-681825C02A21',@TBL_SDG,@T_DTZ, N'priv_modified_on',12,0,0,0,N'SYSUTCDATETIME()',NULL);

-- service_discord_channels columns
INSERT INTO [dbo].[system_objects_database_columns] ([key_guid],[ref_table_guid],[ref_type_guid],[pub_name],[pub_ordinal],[pub_is_nullable],[pub_is_primary_key],[pub_is_identity],[pub_default],[pub_max_length]) VALUES
(N'6316E425-98D0-5932-AEE5-B34BF77EE062',@TBL_SDC,@T_UUID, N'key_guid',            1, 0,1,0,NULL,               NULL),
(N'850597EC-5196-556B-BBC3-43C1D9621705',@TBL_SDC,@T_UUID, N'ref_guild_guid',      2, 0,0,0,NULL,               NULL),
(N'6973FF94-76AF-54FE-9667-0C225F8F6F61',@TBL_SDC,@T_STR,  N'pub_channel_id',      3, 0,0,0,NULL,               64),
(N'75B380DB-B412-5705-80FB-B14CA6E10107',@TBL_SDC,@T_STR,  N'pub_name',            4, 1,0,0,NULL,               256),
(N'6E5C91AE-647B-5A2D-8722-69B634460744',@TBL_SDC,@T_STR,  N'pub_type',            5, 1,0,0,NULL,               32),
(N'73D56D81-EE71-5C3A-9DEE-A999D92E6B9F',@TBL_SDC,@T_INT64,N'pub_message_count',   6, 0,0,0,N'0',              NULL),
(N'0622CBD4-BBFA-52BC-8862-5C5FC9493CD0',@TBL_SDC,@T_DTZ,  N'pub_last_activity_at', 7, 1,0,0,NULL,               NULL),
(N'5E5E4CB6-04F0-52B5-BC10-165B6F8D0A56',@TBL_SDC,@T_TEXT, N'pub_notes',            8, 1,0,0,NULL,               NULL),
(N'D09158CE-9E89-52C8-9E57-2662D3CEE2D7',@TBL_SDC,@T_DTZ,  N'priv_created_on',      9, 0,0,0,N'SYSUTCDATETIME()',NULL),
(N'344A6BBD-35DB-550E-986E-E056D806EA3C',@TBL_SDC,@T_DTZ,  N'priv_modified_on',     10,0,0,0,N'SYSUTCDATETIME()',NULL);
GO




-- 5c: Register FK constraints

-- Referenced PK column GUIDs (from existing tables)
DECLARE @COL_USERS_PK   UNIQUEIDENTIFIER = N'1280BB1F-6504-5268-A49D-0C8F2FA52D3C'; -- system_users.key_guid
DECLARE @COL_MODULES_PK UNIQUEIDENTIFIER = N'ACC8E8B1-F5E5-5D93-B814-B8FF571DE287'; -- Note: reusing types PK guid pattern — need actual modules PK
DECLARE @COL_ROLES_PK   UNIQUEIDENTIFIER = N'AA276608-C963-592B-87BF-0B2C99A44148'; -- system_auth_roles.key_guid
DECLARE @COL_ENTITLE_PK UNIQUEIDENTIFIER = N'52B0C21A-6284-5173-9044-3A61804C6167'; -- system_auth_entitlements.key_guid

-- New table PK columns (from Phase 5b above)
DECLARE @COL_SEC_PK   UNIQUEIDENTIFIER = N'09ADB7F8-D4C2-5885-9385-797F06787209'; -- service_enum_categories.key_guid
DECLARE @COL_SEV_PK   UNIQUEIDENTIFIER = N'3CF8E90D-C44F-538F-A092-4D596A4CDFB2'; -- service_enum_values.key_guid
DECLARE @COL_SS_PK    UNIQUEIDENTIFIER = N'BA2D7FBB-E2B3-5AFF-B0BD-007EC188701A'; -- system_sessions.key_guid
DECLARE @COL_SAC_PK   UNIQUEIDENTIFIER = N'1948DBB8-2D10-5396-994B-CB7FFEF502E4'; -- service_agent_clients.key_guid
DECLARE @COL_SOIG_PK  UNIQUEIDENTIFIER = N'BAC56509-0B20-56A0-A68F-E0506959CE13'; -- system_objects_io_gateways.key_guid
DECLARE @COL_SDG_PK   UNIQUEIDENTIFIER = N'81556366-4AD1-5DAF-9F2E-D857385399D6'; -- service_discord_guilds.key_guid

-- FK table GUIDs (reuse from Phase 5a)
DECLARE @TBL2_SEC   UNIQUEIDENTIFIER = N'F3F35E03-D6A8-5BCC-9E0F-9E92F2D3A5A4';
DECLARE @TBL2_SEV   UNIQUEIDENTIFIER = N'F4F4783A-4E31-5F42-AD6D-E8BB0E5D8BCF';
DECLARE @TBL2_SS    UNIQUEIDENTIFIER = N'B8BD1C09-93FB-54E0-9924-F29F94E7F1AC';
DECLARE @TBL2_SST   UNIQUEIDENTIFIER = N'C2254205-56A8-5F2D-B97A-F3EBC2C1BAF3';
DECLARE @TBL2_SSD   UNIQUEIDENTIFIER = N'43361C00-491A-508F-A418-208D3DFB35E3';
DECLARE @TBL2_SAC   UNIQUEIDENTIFIER = N'CA0AF361-7F1B-5126-B1CC-D68F5452E37E';
DECLARE @TBL2_SACU  UNIQUEIDENTIFIER = N'0F9A194A-8B18-5201-B403-AD611C35E5D5';
DECLARE @TBL2_SAAC  UNIQUEIDENTIFIER = N'F9AF918E-B310-5415-B964-9138475125B7';
DECLARE @TBL2_SOIG  UNIQUEIDENTIFIER = N'79891A32-2D78-5706-9A2D-5F5FFC3F83D7';
DECLARE @TBL2_SOGIP UNIQUEIDENTIFIER = N'9341CA8A-1759-5664-AAF6-6351305B9730';
DECLARE @TBL2_SOGMB UNIQUEIDENTIFIER = N'013CB8EE-96A1-5BDB-BE53-8CE9CA22049B';
DECLARE @TBL2_SDC   UNIQUEIDENTIFIER = N'F856B061-45A7-5F05-874A-6A8D69132013';

DECLARE @TBL2_USERS    UNIQUEIDENTIFIER = N'DCC79235-8429-5731-AF60-092AF3A2E4B0'; -- system_users
DECLARE @TBL2_MODULES  UNIQUEIDENTIFIER = N'D039D8FB-3F95-5A66-B7FB-AB4BA1301FEA'; -- system_objects_modules
DECLARE @TBL2_METHODS  UNIQUEIDENTIFIER = N'65E5E8F3-7EFF-57F7-B4F9-087C191B7B5E'; -- system_objects_module_methods
DECLARE @TBL2_ROLES    UNIQUEIDENTIFIER = N'A578EAB7-B6C4-5BF0-A14D-10BDDC22EA5B'; -- system_auth_roles
DECLARE @TBL2_ENTITLE  UNIQUEIDENTIFIER = N'F975A8E7-62CA-5922-811E-97B5FE7C5998'; -- system_auth_entitlements
DECLARE @TBL2_SDG2     UNIQUEIDENTIFIER = N'A57AE808-EF52-53F9-856C-54B4C3410A9B'; -- service_discord_guilds

-- Need modules PK column GUID and methods PK column GUID
-- system_objects_modules was registered in v0.12.5.0, its key_guid column:
DECLARE @COL_MODULES_PK2 UNIQUEIDENTIFIER;
SELECT @COL_MODULES_PK2 = [key_guid] FROM [dbo].[system_objects_database_columns]
WHERE [ref_table_guid] = @TBL2_MODULES AND [pub_name] = N'key_guid';

DECLARE @COL_METHODS_PK2 UNIQUEIDENTIFIER;
SELECT @COL_METHODS_PK2 = [key_guid] FROM [dbo].[system_objects_database_columns]
WHERE [ref_table_guid] = @TBL2_METHODS AND [pub_name] = N'key_guid';

INSERT INTO [dbo].[system_objects_database_constraints] ([ref_table_guid],[ref_column_guid],[ref_referenced_table_guid],[ref_referenced_column_guid]) VALUES
-- service_enum_values.ref_category_guid → service_enum_categories.key_guid
(@TBL2_SEV,  N'3C7EEA25-F502-5C63-A1AD-774EB8F2C9A5', @TBL2_SEC, @COL_SEC_PK),
-- system_sessions.ref_user_guid → system_users.key_guid
(@TBL2_SS,   N'D9D80FFE-6848-5E12-9C96-505C5FFD3417', @TBL2_USERS, @COL_USERS_PK),
-- system_sessions.ref_session_type_guid → service_enum_values.key_guid
(@TBL2_SS,   N'8382B476-05D5-58A2-80CF-526D61F6BD5B', @TBL2_SEV, @COL_SEV_PK),
-- system_session_tokens.ref_session_guid → system_sessions.key_guid
(@TBL2_SST,  N'A0601D6F-2335-5138-A798-62EE23CC675F', @TBL2_SS, @COL_SS_PK),
-- system_session_tokens.ref_token_type_guid → service_enum_values.key_guid
(@TBL2_SST,  N'9A50E7C4-9109-588C-90AF-FB04B8AC9DF2', @TBL2_SEV, @COL_SEV_PK),
-- system_session_devices.ref_session_guid → system_sessions.key_guid
(@TBL2_SSD,  N'F2AC596A-9A20-58BA-B888-2B907E70B0B8', @TBL2_SS, @COL_SS_PK),
-- service_agent_client_users.ref_client_guid → service_agent_clients.key_guid
(@TBL2_SACU, N'815F9399-8DD9-5B2F-8BB7-D187DBA92E21', @TBL2_SAC, @COL_SAC_PK),
-- service_agent_client_users.ref_user_guid → system_users.key_guid
(@TBL2_SACU, N'B96E544B-80E1-5913-8823-6B59E55BA6AD', @TBL2_USERS, @COL_USERS_PK),
-- service_agent_auth_codes.ref_client_guid → service_agent_clients.key_guid
(@TBL2_SAAC, N'577FFCE4-CC6B-5003-870F-31AB1FB45244', @TBL2_SAC, @COL_SAC_PK),
-- service_agent_auth_codes.ref_user_guid → system_users.key_guid
(@TBL2_SAAC, N'206766E3-9C33-5F35-9653-955EAC08E516', @TBL2_USERS, @COL_USERS_PK),
-- system_objects_io_gateways.ref_transport_guid → service_enum_values.key_guid
(@TBL2_SOIG, N'264B5090-3FFF-5E75-B5E8-A8D75FE1F5CC', @TBL2_SEV, @COL_SEV_PK),
-- system_objects_io_gateways.ref_module_guid → system_objects_modules.key_guid
(@TBL2_SOIG, N'688DB827-BD0B-5712-8EED-FB6AFD2A07FC', @TBL2_MODULES, @COL_MODULES_PK2),
-- system_objects_gateway_identity_providers.ref_gateway_guid → system_objects_io_gateways.key_guid
(@TBL2_SOGIP, N'06D0BBC7-CFFE-510F-ABDE-98760A908693', @TBL2_SOIG, @COL_SOIG_PK),
-- system_objects_gateway_identity_providers.ref_strategy_guid → service_enum_values.key_guid
(@TBL2_SOGIP, N'516B9623-A278-5590-AC70-A92593E22654', @TBL2_SEV, @COL_SEV_PK),
-- system_objects_gateway_method_bindings.ref_gateway_guid → system_objects_io_gateways.key_guid
(@TBL2_SOGMB, N'ECA5AD93-7AC0-5EE0-8487-322FDBC54C69', @TBL2_SOIG, @COL_SOIG_PK),
-- system_objects_gateway_method_bindings.ref_method_guid → system_objects_module_methods.key_guid
(@TBL2_SOGMB, N'572B2D8A-5B21-5E6E-9FE9-8C3DE31AD0C0', @TBL2_METHODS, @COL_METHODS_PK2),
-- system_objects_gateway_method_bindings.ref_required_role_guid → system_auth_roles.key_guid
(@TBL2_SOGMB, N'58B99E68-8685-577E-ACC5-05D306A4B2E0', @TBL2_ROLES, @COL_ROLES_PK),
-- system_objects_gateway_method_bindings.ref_required_entitlement_guid → system_auth_entitlements.key_guid
(@TBL2_SOGMB, N'E1CC4DB0-2AF3-5A7D-832B-80F4D81B84C0', @TBL2_ENTITLE, @COL_ENTITLE_PK),
-- service_discord_channels.ref_guild_guid → service_discord_guilds.key_guid
(@TBL2_SDC,  N'850597EC-5196-556B-BBC3-43C1D9621705', @TBL2_SDG2, @COL_SDG_PK);
GO


-- ============================================================================
-- PHASE 6: Verification
-- ============================================================================

-- Table counts
SELECT 'service_enum_categories'    AS [table], COUNT(*) AS [rows] FROM [dbo].[service_enum_categories];
SELECT 'service_enum_values'        AS [table], COUNT(*) AS [rows] FROM [dbo].[service_enum_values];
SELECT 'system_sessions'            AS [table], COUNT(*) AS [rows] FROM [dbo].[system_sessions];
SELECT 'system_session_tokens'      AS [table], COUNT(*) AS [rows] FROM [dbo].[system_session_tokens];
SELECT 'system_session_devices'     AS [table], COUNT(*) AS [rows] FROM [dbo].[system_session_devices];
SELECT 'service_agent_clients'      AS [table], COUNT(*) AS [rows] FROM [dbo].[service_agent_clients];
SELECT 'service_agent_client_users' AS [table], COUNT(*) AS [rows] FROM [dbo].[service_agent_client_users];
SELECT 'service_agent_auth_codes'   AS [table], COUNT(*) AS [rows] FROM [dbo].[service_agent_auth_codes];
SELECT 'system_objects_io_gateways' AS [table], COUNT(*) AS [rows] FROM [dbo].[system_objects_io_gateways];
SELECT 'system_objects_gateway_identity_providers' AS [table], COUNT(*) AS [rows] FROM [dbo].[system_objects_gateway_identity_providers];
SELECT 'system_objects_gateway_method_bindings'    AS [table], COUNT(*) AS [rows] FROM [dbo].[system_objects_gateway_method_bindings];
SELECT 'service_discord_guilds'     AS [table], COUNT(*) AS [rows] FROM [dbo].[service_discord_guilds];
SELECT 'service_discord_channels'   AS [table], COUNT(*) AS [rows] FROM [dbo].[service_discord_channels];

-- Enum values with categories
SELECT c.pub_name AS category, v.pub_name AS value, v.pub_display, v.pub_sequence
FROM service_enum_values v
JOIN service_enum_categories c ON c.key_guid = v.ref_category_guid
ORDER BY c.pub_name, v.pub_sequence;

-- Gateway registry
SELECT g.pub_name AS gateway, v.pub_name AS transport, m.pub_name AS module
FROM system_objects_io_gateways g
JOIN service_enum_values v ON v.key_guid = g.ref_transport_guid
JOIN system_objects_modules m ON m.key_guid = g.ref_module_guid
ORDER BY g.pub_name;

-- Gateway identity strategies
SELECT g.pub_name AS gateway, v.pub_name AS strategy, ip.pub_priority
FROM system_objects_gateway_identity_providers ip
JOIN system_objects_io_gateways g ON g.key_guid = ip.ref_gateway_guid
JOIN service_enum_values v ON v.key_guid = ip.ref_strategy_guid
ORDER BY g.pub_name, ip.pub_priority;

-- Claude agent client
SELECT pub_client_id, pub_client_name, pub_scopes, pub_is_dcr
FROM service_agent_clients
WHERE pub_client_name = 'Claude';

-- Object tree: new table count
SELECT COUNT(*) AS new_tables_registered
FROM system_objects_database_tables
WHERE pub_name IN (
  'service_enum_categories', 'service_enum_values',
  'system_sessions', 'system_session_tokens', 'system_session_devices',
  'service_agent_clients', 'service_agent_client_users', 'service_agent_auth_codes',
  'system_objects_io_gateways', 'system_objects_gateway_identity_providers', 'system_objects_gateway_method_bindings',
  'service_discord_guilds', 'service_discord_channels'
);

-- Object tree: column count for new tables
SELECT t.pub_name AS [table], COUNT(c.key_guid) AS [columns]
FROM system_objects_database_tables t
JOIN system_objects_database_columns c ON c.ref_table_guid = t.key_guid
WHERE t.pub_name IN (
  'service_enum_categories', 'service_enum_values',
  'system_sessions', 'system_session_tokens', 'system_session_devices',
  'service_agent_clients', 'service_agent_client_users', 'service_agent_auth_codes',
  'system_objects_io_gateways', 'system_objects_gateway_identity_providers', 'system_objects_gateway_method_bindings',
  'service_discord_guilds', 'service_discord_channels'
)
GROUP BY t.pub_name
ORDER BY t.pub_name;

-- FK constraint count for new tables
SELECT COUNT(*) AS new_fk_constraints
FROM system_objects_database_constraints fk
JOIN system_objects_database_tables t ON t.key_guid = fk.ref_table_guid
WHERE t.pub_name IN (
  'service_enum_values',
  'system_sessions', 'system_session_tokens', 'system_session_devices',
  'service_agent_client_users', 'service_agent_auth_codes',
  'system_objects_io_gateways', 'system_objects_gateway_identity_providers', 'system_objects_gateway_method_bindings',
  'service_discord_channels'
);