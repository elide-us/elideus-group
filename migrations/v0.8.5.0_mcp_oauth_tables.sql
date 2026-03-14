SET ANSI_NULLS ON;
SET QUOTED_IDENTIFIER ON;
GO

-- ============================================================================
-- v0.8.5.0 MCP OAuth 2.1 Tables
-- ============================================================================

-- A1. account_mcp_agents — registered MCP clients (DCR or manual)
CREATE TABLE [dbo].[account_mcp_agents] (
  [recid]                   bigint IDENTITY(1,1) NOT NULL,
  [element_client_id]       UNIQUEIDENTIFIER NOT NULL DEFAULT NEWID(),
  [element_client_secret]   NVARCHAR(512) NULL,
  [element_client_name]     NVARCHAR(256) NOT NULL,
  [element_redirect_uris]   NVARCHAR(MAX) NULL,
  [element_grant_types]     NVARCHAR(1024) NOT NULL DEFAULT 'authorization_code',
  [element_response_types]  NVARCHAR(256) NOT NULL DEFAULT 'code',
  [element_scopes]          NVARCHAR(1024) NOT NULL DEFAULT 'mcp:schema:read',
  [element_roles]           BIGINT NOT NULL DEFAULT ((0)),
  [users_recid]             BIGINT NULL,
  [element_ip_address]      NVARCHAR(64) NULL,
  [element_user_agent]      NVARCHAR(1024) NULL,
  [element_is_active]       BIT NOT NULL DEFAULT ((1)),
  [element_revoked_at]      datetimeoffset(7) NULL,
  [element_created_on]      datetimeoffset(7) NOT NULL DEFAULT (sysutcdatetime()),
  [element_modified_on]     datetimeoffset(7) NOT NULL DEFAULT (sysutcdatetime()),
  CONSTRAINT [PK_account_mcp_agents] PRIMARY KEY ([recid]),
  CONSTRAINT [FK_account_mcp_agents_users] FOREIGN KEY ([users_recid])
    REFERENCES [dbo].[account_users] ([recid])
);
GO

CREATE UNIQUE INDEX [UQ_account_mcp_agents_client_id]
  ON [dbo].[account_mcp_agents] ([element_client_id]);
GO

CREATE INDEX [IX_account_mcp_agents_users]
  ON [dbo].[account_mcp_agents] ([users_recid]);
GO

-- A2. account_mcp_agent_tokens — access/refresh tokens for MCP agents
CREATE TABLE [dbo].[account_mcp_agent_tokens] (
  [recid]                   bigint IDENTITY(1,1) NOT NULL,
  [agents_recid]            BIGINT NOT NULL,
  [element_access_token]    NVARCHAR(MAX) NOT NULL,
  [element_refresh_token]   NVARCHAR(MAX) NULL,
  [element_access_exp]      datetimeoffset(7) NOT NULL,
  [element_refresh_exp]     datetimeoffset(7) NULL,
  [element_scopes]          NVARCHAR(1024) NOT NULL,
  [element_revoked_at]      datetimeoffset(7) NULL,
  [element_created_on]      datetimeoffset(7) NOT NULL DEFAULT (sysutcdatetime()),
  CONSTRAINT [PK_account_mcp_agent_tokens] PRIMARY KEY ([recid]),
  CONSTRAINT [FK_account_mcp_agent_tokens_agents] FOREIGN KEY ([agents_recid])
    REFERENCES [dbo].[account_mcp_agents] ([recid])
);
GO

CREATE INDEX [IX_account_mcp_agent_tokens_agents]
  ON [dbo].[account_mcp_agent_tokens] ([agents_recid]);
GO

-- A3. account_mcp_auth_codes — single-use authorization codes (60s TTL)
CREATE TABLE [dbo].[account_mcp_auth_codes] (
  [recid]                   bigint IDENTITY(1,1) NOT NULL,
  [agents_recid]            BIGINT NOT NULL,
  [users_recid]             BIGINT NOT NULL,
  [element_code]            NVARCHAR(256) NOT NULL,
  [element_code_challenge]  NVARCHAR(256) NOT NULL,
  [element_code_method]     NVARCHAR(16) NOT NULL DEFAULT 'S256',
  [element_redirect_uri]    NVARCHAR(2048) NOT NULL,
  [element_scopes]          NVARCHAR(1024) NOT NULL,
  [element_consumed]        BIT NOT NULL DEFAULT ((0)),
  [element_expires_on]      datetimeoffset(7) NOT NULL,
  [element_created_on]      datetimeoffset(7) NOT NULL DEFAULT (sysutcdatetime()),
  CONSTRAINT [PK_account_mcp_auth_codes] PRIMARY KEY ([recid]),
  CONSTRAINT [FK_account_mcp_auth_codes_agents] FOREIGN KEY ([agents_recid])
    REFERENCES [dbo].[account_mcp_agents] ([recid]),
  CONSTRAINT [FK_account_mcp_auth_codes_users] FOREIGN KEY ([users_recid])
    REFERENCES [dbo].[account_users] ([recid])
);
GO

CREATE UNIQUE INDEX [UQ_account_mcp_auth_codes_code]
  ON [dbo].[account_mcp_auth_codes] ([element_code]);
GO

-- B1. Add ROLE_MCP_ACCESS (bit 5, mask 32)
IF NOT EXISTS (SELECT 1 FROM system_roles WHERE element_name = 'ROLE_MCP_ACCESS')
  INSERT INTO system_roles (element_mask, element_enablement, element_name, element_display)
    VALUES (32, '0', 'ROLE_MCP_ACCESS', 'MCP Agent Access');
GO

-- B2. Add auth provider for MCP
IF NOT EXISTS (SELECT 1 FROM auth_providers WHERE element_name = 'mcp')
  INSERT INTO auth_providers (element_name, element_display)
    VALUES ('mcp', 'MCP Agent');
GO

-- B3. System config entries (kill switch + rate limits)
IF NOT EXISTS (SELECT 1 FROM system_config WHERE element_key = 'MCP_DCR_ENABLED')
  INSERT INTO system_config (element_key, element_value) VALUES ('MCP_DCR_ENABLED', 'false');
GO
IF NOT EXISTS (SELECT 1 FROM system_config WHERE element_key = 'MCP_RATE_LIMIT_REGISTER_IP')
  INSERT INTO system_config (element_key, element_value) VALUES ('MCP_RATE_LIMIT_REGISTER_IP', '5');
GO
IF NOT EXISTS (SELECT 1 FROM system_config WHERE element_key = 'MCP_RATE_LIMIT_REGISTER_GLOBAL')
  INSERT INTO system_config (element_key, element_value) VALUES ('MCP_RATE_LIMIT_REGISTER_GLOBAL', '50');
GO
IF NOT EXISTS (SELECT 1 FROM system_config WHERE element_key = 'MCP_RATE_LIMIT_TOKEN_IP')
  INSERT INTO system_config (element_key, element_value) VALUES ('MCP_RATE_LIMIT_TOKEN_IP', '60');
GO
IF NOT EXISTS (SELECT 1 FROM system_config WHERE element_key = 'MCP_RATE_LIMIT_TOKEN_GLOBAL')
  INSERT INTO system_config (element_key, element_value) VALUES ('MCP_RATE_LIMIT_TOKEN_GLOBAL', '500');
GO
