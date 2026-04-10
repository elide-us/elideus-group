-- ============================================================================
-- TheOracleRPC v0.12.0.0 — Security Core Foundation
-- Date: 2026-04-09
-- Purpose:
--   Create the anchor identity table (system_users), the provider
--   configuration table (service_auth_providers), and the provider
--   link mapping table (system_user_auth).
--
-- Column naming convention:
--   key_*  — primary key (UNIQUEIDENTIFIER or BIGINT IDENTITY(1,1) only)
--   pub_*  — functional/public columns (views, joins, API responses)
--   priv_* — bookkeeping columns (audit timestamps, internal tracking)
--   ext_*  — reserved for future extensions/add-ins
--
-- Table naming convention:
--   service_* — service-tier configuration managed by ROLE_SERVICE_ADMIN
--               (external integrations: auth providers, db providers,
--                storage providers, input providers)
--   system_*  — application-internal tables (users, config, roles,
--               sessions, reflection)
--
-- Join convention:
--   Always join on key_guid or key_id. Never on name strings.
--
-- PK strategy for service_auth_providers:
--   key_guid is a deterministic UUID5 derived from pub_name using an
--   application namespace stored in system_config as UuidNamespace.
--   Same provider name = same GUID in every database instance.
--
--   Generation:
--     import uuid
--     NS = uuid.UUID(system_config['UuidNamespace'])
--     key_guid = uuid.uuid5(NS, pub_name)
--
-- These are NEW tables with no references to existing tables.
-- Data migration from legacy tables is performed manually in SSMS.
-- ============================================================================

-- ============================================================================
-- service_auth_providers
--
-- Canonical definition of every OAuth/OIDC provider the system can
-- authenticate against. One of several service_*_providers tables
-- following the same pattern (service_db_providers,
-- service_storage_providers, service_input_providers, etc.).
--
-- Consolidates provider configuration previously spread across:
--   - auth_providers table (3 columns)
--   - frontend/src/config/*.ts (static TypeScript files)
--   - server/modules/providers/auth/*/ (hardcoded Python constants)
--   - system_config keys (MsApiId, GoogleClientId, DiscordClientId)
--
-- Client secrets stay in environment variables.
-- JWKS keys are runtime cache, not stored.
-- ============================================================================

CREATE TABLE [dbo].[service_auth_providers] (
  [key_guid]                      UNIQUEIDENTIFIER     NOT NULL,

  -- Identity
  [pub_name]                      NVARCHAR(64)         NOT NULL,
  [pub_display]                   NVARCHAR(128)        NOT NULL,

  -- OAuth endpoints
  [pub_authorize_url]             NVARCHAR(2048)       NULL,
  [pub_token_url]                 NVARCHAR(2048)       NULL,
  [pub_userinfo_url]              NVARCHAR(2048)       NULL,
  [pub_openid_config_url]         NVARCHAR(2048)       NULL,
  [pub_jwks_uri]                  NVARCHAR(2048)       NULL,
  [pub_issuer]                    NVARCHAR(512)        NULL,

  -- Client configuration
  [pub_client_id]                 NVARCHAR(512)        NOT NULL,
  [pub_scopes]                    NVARCHAR(1024)       NOT NULL,
  [pub_grant_types]               NVARCHAR(256)        NOT NULL   CONSTRAINT [DF_sap_grant_types]   DEFAULT N'authorization_code',
  [pub_response_type]             NVARCHAR(64)         NOT NULL   CONSTRAINT [DF_sap_response_type] DEFAULT N'code',

  -- Behavioral flags
  [pub_is_oidc]                   BIT                  NOT NULL   CONSTRAINT [DF_sap_is_oidc]       DEFAULT 0,
  [pub_requires_id_token]         BIT                  NOT NULL   CONSTRAINT [DF_sap_requires_id]   DEFAULT 0,
  [pub_is_active]                 BIT                  NOT NULL   CONSTRAINT [DF_sap_is_active]     DEFAULT 1,
  [pub_allow_registration]        BIT                  NOT NULL   CONSTRAINT [DF_sap_allow_reg]     DEFAULT 0,

  -- Profile claim mapping
  [pub_identifier_claim]          NVARCHAR(64)         NOT NULL,
  [pub_email_claim]               NVARCHAR(64)         NOT NULL   CONSTRAINT [DF_sap_email_claim]   DEFAULT N'email',
  [pub_display_claim]             NVARCHAR(64)         NOT NULL   CONSTRAINT [DF_sap_display_claim] DEFAULT N'name',
  [pub_avatar_claim]              NVARCHAR(64)         NULL,
  [pub_avatar_url_pattern]        NVARCHAR(512)        NULL,

  -- Display
  [pub_sequence]                  INT                  NOT NULL   CONSTRAINT [DF_sap_sequence]      DEFAULT 0,

  -- Bookkeeping
  [priv_created_on]               DATETIMEOFFSET(7)    NOT NULL   CONSTRAINT [DF_sap_created_on]    DEFAULT SYSUTCDATETIME(),
  [priv_modified_on]              DATETIMEOFFSET(7)    NOT NULL   CONSTRAINT [DF_sap_modified_on]   DEFAULT SYSUTCDATETIME(),

  CONSTRAINT [PK_service_auth_providers]      PRIMARY KEY CLUSTERED ([key_guid]),
  CONSTRAINT [UQ_service_auth_providers_name] UNIQUE ([pub_name])
);
GO

-- ============================================================================
-- system_users
--
-- Anchor identity table. key_guid is the linchpin for the entire
-- application — all authorization, sessions, provider links, and
-- entitlements FK to this value.
--
-- Lean by design. Roles, entitlements, and provider links are
-- resolved via mapping tables joined on key_guid:
--   - system_user_auth        (provider links)
--   - system_user_roles       (future)
--   - system_user_entitlements (future)
-- ============================================================================

CREATE TABLE [dbo].[system_users] (
  [key_guid]                      UNIQUEIDENTIFIER     NOT NULL   CONSTRAINT [DF_system_users_guid]        DEFAULT NEWID(),

  [pub_display]                   NVARCHAR(256)        NOT NULL,
  [pub_email]                     NVARCHAR(320)        NOT NULL,

  -- Bookkeeping
  [priv_created_on]               DATETIMEOFFSET(7)    NOT NULL   CONSTRAINT [DF_system_users_created_on]  DEFAULT SYSUTCDATETIME(),
  [priv_modified_on]              DATETIMEOFFSET(7)    NOT NULL   CONSTRAINT [DF_system_users_modified_on] DEFAULT SYSUTCDATETIME(),

  CONSTRAINT [PK_system_users] PRIMARY KEY CLUSTERED ([key_guid])
);
GO

-- ============================================================================
-- system_user_auth
--
-- Maps a user to their identity at each linked provider.
-- One row per user-provider link. Query pattern:
--
--   SELECT u.*, p.pub_name, p.pub_display, a.pub_provider_identifier
--   FROM system_users u
--   LEFT JOIN system_user_auth a ON a.pub_user_guid = u.key_guid
--   LEFT JOIN service_auth_providers p ON p.key_guid = a.pub_provider_guid
--   WHERE u.key_guid = @guid
--
-- Returns N rows (one per linked provider). Consuming code
-- aggregates or flattens as needed.
-- ============================================================================

CREATE TABLE [dbo].[system_user_auth] (
  [key_id]                        BIGINT IDENTITY(1,1) NOT NULL,

  [ref_user_guid]                 UNIQUEIDENTIFIER     NOT NULL,
  [ref_provider_guid]             UNIQUEIDENTIFIER     NOT NULL,
  [pub_provider_identifier]       NVARCHAR(512)        NOT NULL,
  [pub_is_linked]                 BIT                  NOT NULL   CONSTRAINT [DF_sua_linked]      DEFAULT 1,

  -- Bookkeeping
  [priv_created_on]               DATETIMEOFFSET(7)    NOT NULL   CONSTRAINT [DF_sua_created_on]  DEFAULT SYSUTCDATETIME(),
  [priv_modified_on]              DATETIMEOFFSET(7)    NOT NULL   CONSTRAINT [DF_sua_modified_on] DEFAULT SYSUTCDATETIME(),

  CONSTRAINT [PK_system_user_auth]                     PRIMARY KEY CLUSTERED ([key_id]),
  CONSTRAINT [FK_system_user_auth_user]                FOREIGN KEY ([ref_user_guid])     REFERENCES [dbo].[system_users] ([key_guid]),
  CONSTRAINT [FK_system_user_auth_provider]            FOREIGN KEY ([ref_provider_guid]) REFERENCES [dbo].[service_auth_providers] ([key_guid]),
  CONSTRAINT [UQ_system_user_auth_provider_identifier] UNIQUE ([ref_provider_guid], [pub_provider_identifier])
);
GO
CREATE INDEX [IX_system_user_auth_user_guid] ON [dbo].[system_user_auth] ([ref_user_guid]);
CREATE INDEX [IX_system_user_auth_user_provider] ON [dbo].[system_user_auth] ([ref_user_guid], [ref_provider_guid]);
GO

-- ============================================================================
-- Seed: Auth Providers
--
-- key_guid values are deterministic UUID5:
--   Namespace: DECAFBAD-CAFE-FADE-BABE-C0FFEE420B67
--   Formula:   uuid5(namespace, pub_name)
--
--   import uuid
--   NS = uuid.UUID('DECAFBAD-CAFE-FADE-BABE-C0FFEE420B67')
--   uuid.uuid5(NS, 'microsoft')  -> 17183915-860F-5FA0-8932-6CA4FF5C3707
--   uuid.uuid5(NS, 'google')     -> 1887B330-D5B8-5B0B-A578-861A37372021
--   uuid.uuid5(NS, 'discord')    -> 435B381F-9A8B-5ECB-9471-A4668C817A72
--   uuid.uuid5(NS, 'apple')      -> 59006D5D-F7C7-5E94-9A13-B6F683D899C4 (reserved)
-- ============================================================================

INSERT INTO [dbo].[service_auth_providers] (
  [key_guid],
  [pub_name], [pub_display],
  [pub_authorize_url], [pub_token_url], [pub_userinfo_url],
  [pub_openid_config_url], [pub_jwks_uri], [pub_issuer],
  [pub_client_id], [pub_scopes], [pub_grant_types], [pub_response_type],
  [pub_is_oidc], [pub_requires_id_token], [pub_is_active], [pub_allow_registration],
  [pub_identifier_claim], [pub_email_claim], [pub_display_claim],
  [pub_avatar_claim], [pub_avatar_url_pattern],
  [pub_sequence]
) VALUES
-- Microsoft (OIDC, consumers tenant)
(
  N'17183915-860F-5FA0-8932-6CA4FF5C3707',
  N'microsoft', N'Microsoft',
  N'https://login.microsoftonline.com/consumers/oauth2/v2.0/authorize',
  N'https://login.microsoftonline.com/consumers/oauth2/v2.0/token',
  N'https://graph.microsoft.com/v1.0/me',
  N'https://login.microsoftonline.com/consumers/v2.0/.well-known/openid-configuration',
  NULL,
  N'https://login.microsoftonline.com/9188040d-6c67-4c5b-b112-36a304b66dad/v2.0',
  N'6c725f5b-6a44-4bf0-a0d6-c2cfc15230be',
  N'openid profile email User.Read',
  N'authorization_code', N'code',
  1, 1, 1, 1,
  N'oid', N'mail', N'displayName',
  NULL, N'https://graph.microsoft.com/v1.0/me/photo/$value',
  10
),
-- Google (OIDC)
(
  N'1887B330-D5B8-5B0B-A578-861A37372021',
  N'google', N'Google',
  N'https://accounts.google.com/o/oauth2/v2/auth',
  N'https://oauth2.googleapis.com/token',
  NULL,
  N'https://accounts.google.com/.well-known/openid-configuration',
  NULL,
  N'https://accounts.google.com',
  N'295304659309-vkbjt5572fg3vjlqbj3qkkfgal83pcrj.apps.googleusercontent.com',
  N'openid profile email',
  N'authorization_code', N'code',
  1, 1, 1, 1,
  N'sub', N'email', N'name',
  N'picture', NULL,
  20
),
-- Discord (non-OIDC)
(
  N'435B381F-9A8B-5ECB-9471-A4668C817A72',
  N'discord', N'Discord',
  N'https://discord.com/oauth2/authorize',
  N'https://discord.com/api/oauth2/token',
  N'https://discord.com/api/users/@me',
  NULL, NULL, NULL,
  N'1339726954986999878',
  N'identify email',
  N'authorization_code', N'code',
  0, 0, 1, 1,
  N'id', N'email', N'username',
  N'avatar', N'https://cdn.discordapp.com/avatars/{id}/{avatar}.png',
  30
);
GO

-- ============================================================================
-- Verification
-- ============================================================================

SELECT 'service_auth_providers' AS [table], COUNT(*) AS [rows] FROM [dbo].[service_auth_providers];
SELECT 'system_users' AS [table], COUNT(*) AS [rows] FROM [dbo].[system_users];
SELECT 'system_user_auth' AS [table], COUNT(*) AS [rows] FROM [dbo].[system_user_auth];

SELECT
  [key_guid], [pub_name], [pub_display],
  [pub_is_oidc] AS [oidc],
  [pub_requires_id_token] AS [id_token],
  [pub_is_active] AS [active],
  [pub_identifier_claim] AS [id_claim]
FROM [dbo].[service_auth_providers]
ORDER BY [pub_sequence];


----------------


-- ============================================================================
-- Backfill: seed column definitions for v0.12.0.0 tables
-- These were registered as tables but their columns were not seeded
-- ============================================================================

DECLARE @T_UUID  UNIQUEIDENTIFIER = N'4D2EB10B-363E-5AF4-826A-9294146244E4';
DECLARE @T_INT64_ID UNIQUEIDENTIFIER = N'E0556F4C-ECA5-5475-B6C1-F60706632F06';
DECLARE @T_BOOL  UNIQUEIDENTIFIER = N'12B2F03B-E315-50A5-B631-E6B1EB961A17';
DECLARE @T_STR   UNIQUEIDENTIFIER = N'0093B404-1EEE-563D-9135-4B9E7EECA7A2';
DECLARE @T_DTZ   UNIQUEIDENTIFIER = N'70F890D3-5AB5-5250-860E-4F7F9624190C';
DECLARE @T_INT32 UNIQUEIDENTIFIER = N'E3EDE0CE-2A03-501E-A796-3487BEA03B7B';

DECLARE @TBL_SAP   UNIQUEIDENTIFIER = N'6E74766A-38EA-583C-9E08-4060FB5FDC4B'; -- service_auth_providers
DECLARE @TBL_USERS UNIQUEIDENTIFIER = N'DCC79235-8429-5731-AF60-092AF3A2E4B0'; -- system_users
DECLARE @TBL_SUA   UNIQUEIDENTIFIER = N'D847D5C3-0D47-5668-9745-E394E6712B39'; -- system_user_auth

-- system_users
INSERT INTO [dbo].[system_objects_database_columns] ([key_guid],[ref_table_guid],[ref_type_guid],[pub_name],[pub_ordinal],[pub_is_nullable],[pub_is_primary_key],[pub_is_identity],[pub_default],[pub_max_length]) VALUES
(N'1280BB1F-6504-5268-A49D-0C8F2FA52D3C',@TBL_USERS,@T_UUID,N'key_guid',        1,0,1,0,N'NEWID()',          NULL),
(N'783A200B-F0E7-5197-9952-81A008B2A16A',@TBL_USERS,@T_STR, N'pub_display',     2,0,0,0,NULL,               256),
(N'A5884C27-0DF8-50B5-94E7-21FE28F52AA9',@TBL_USERS,@T_STR, N'pub_email',       3,0,0,0,NULL,               320),
(N'77961531-A18E-52C0-BFE6-9E1140C3B435',@TBL_USERS,@T_DTZ, N'priv_created_on', 4,0,0,0,N'SYSUTCDATETIME()',NULL),
(N'FC954A0D-B3FC-5EEA-BD1C-21CA6EB5AB80',@TBL_USERS,@T_DTZ, N'priv_modified_on',5,0,0,0,N'SYSUTCDATETIME()',NULL);

-- service_auth_providers (just key_guid for now — full column set can be added later)
INSERT INTO [dbo].[system_objects_database_columns] ([key_guid],[ref_table_guid],[ref_type_guid],[pub_name],[pub_ordinal],[pub_is_nullable],[pub_is_primary_key],[pub_is_identity],[pub_default],[pub_max_length]) VALUES
(N'94A894B1-763C-5B7F-803D-1F8E6605A2E2',@TBL_SAP,@T_UUID,N'key_guid',1,0,1,0,NULL,NULL);

-- system_user_auth
INSERT INTO [dbo].[system_objects_database_columns] ([key_guid],[ref_table_guid],[ref_type_guid],[pub_name],[pub_ordinal],[pub_is_nullable],[pub_is_primary_key],[pub_is_identity],[pub_default],[pub_max_length]) VALUES
(N'A3E4C34C-CDC4-51A3-8578-44B83B57D1B4',@TBL_SUA,@T_INT64_ID,N'key_id',                 1,0,1,1,NULL,               NULL),
(N'76FE6021-0CDE-5460-A937-CF966F79603E',@TBL_SUA,@T_UUID,    N'ref_user_guid',          2,0,0,0,NULL,               NULL),
(N'707BB3AA-BB86-51FF-9D9D-23614F284C77',@TBL_SUA,@T_UUID,    N'ref_provider_guid',      3,0,0,0,NULL,               NULL),
(N'6530EDD6-1906-5494-98CC-4FE2586A458A',@TBL_SUA,@T_STR,     N'pub_provider_identifier',4,0,0,0,NULL,               512),
(N'0E98761C-30AE-5487-9421-BF15434D6EBA',@TBL_SUA,@T_BOOL,    N'pub_is_linked',          5,0,0,0,N'1',              NULL),
(N'8CEC589C-7BBF-58B4-B335-014DFA180B88',@TBL_SUA,@T_DTZ,     N'priv_created_on',        6,0,0,0,N'SYSUTCDATETIME()',NULL),
(N'373C9881-3093-561E-9848-A940597F926E',@TBL_SUA,@T_DTZ,     N'priv_modified_on',       7,0,0,0,N'SYSUTCDATETIME()',NULL);
GO

-- ============================================================================
-- Now insert the FK constraints for roles/entitlements
-- (these were failing because system_users.key_guid column didn't exist)
-- ============================================================================

INSERT INTO [dbo].[system_objects_database_constraints] ([ref_table_guid],[ref_column_guid],[ref_referenced_table_guid],[ref_referenced_column_guid]) VALUES
-- system_user_roles.ref_user_guid → system_users.key_guid
(N'F809FAD0-0D76-5B67-B986-0CB3B838EF24', N'647B9F7D-DB91-5764-AD18-EED31E4F73E6', N'DCC79235-8429-5731-AF60-092AF3A2E4B0', N'1280BB1F-6504-5268-A49D-0C8F2FA52D3C'),
-- system_user_roles.ref_role_guid → system_auth_roles.key_guid
(N'F809FAD0-0D76-5B67-B986-0CB3B838EF24', N'D5AA5306-BCB9-5E39-99B1-F2FB5023957A', N'A578EAB7-B6C4-5BF0-A14D-10BDDC22EA5B', N'AA276608-C963-592B-87BF-0B2C99A44148'),
-- system_user_entitlements.ref_user_guid → system_users.key_guid
(N'B993A463-FA66-5721-A2BA-85515D1C05DB', N'AD9A1519-312B-5406-9E0B-E58B224641A1', N'DCC79235-8429-5731-AF60-092AF3A2E4B0', N'1280BB1F-6504-5268-A49D-0C8F2FA52D3C'),
-- system_user_entitlements.ref_entitlement_guid → system_auth_entitlements.key_guid
(N'B993A463-FA66-5721-A2BA-85515D1C05DB', N'187129D0-12BE-5280-A0B9-2B5E75024A43', N'F975A8E7-62CA-5922-811E-97B5FE7C5998', N'52B0C21A-6284-5173-9044-3A61804C6167');
GO