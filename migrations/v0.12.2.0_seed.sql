-- ============================================================================
-- TheOracleRPC v0.12.2.0 — Auth Roles & Entitlements
-- Date: 2026-04-10
-- Purpose:
--   Create authorization tables for roles and entitlements, following
--   the same mapping-table pattern as system_user_auth.
--
--   Tables created:
--     system_auth_roles           — role definitions
--     system_user_roles           — user ↔ role mapping
--     system_auth_entitlements    — entitlement definitions
--     system_user_entitlements    — user ↔ entitlement mapping
--
--   Also registers all 4 tables in the system_objects reflection tree
--   with self-describing column, index, and constraint seed data.
--
--   UUID5 namespace: DECAFBAD-CAFE-FADE-BABE-C0FFEE420B67
--   Roles:        uuid5(NS, 'role:{pub_name}')
--   Entitlements: uuid5(NS, 'entitlement:{pub_name}')
--   Tables:       uuid5(NS, 'table:{table_name}')
--   Columns:      uuid5(NS, 'column:{table_name}.{column_name}')
-- ============================================================================

-- ============================================================================
-- system_auth_roles
-- ============================================================================

CREATE TABLE [dbo].[system_auth_roles] (
  [key_guid]              UNIQUEIDENTIFIER  NOT NULL,
  [pub_name]              NVARCHAR(64)      NOT NULL,
  [pub_display]           NVARCHAR(128)     NOT NULL,
  [pub_rpc_domain]        NVARCHAR(64)      NULL,
  [priv_created_on]       DATETIMEOFFSET(7) NOT NULL CONSTRAINT [DF_sar_created_on]  DEFAULT SYSUTCDATETIME(),
  [priv_modified_on]      DATETIMEOFFSET(7) NOT NULL CONSTRAINT [DF_sar_modified_on] DEFAULT SYSUTCDATETIME(),
  CONSTRAINT [PK_system_auth_roles]      PRIMARY KEY CLUSTERED ([key_guid]),
  CONSTRAINT [UQ_system_auth_roles_name] UNIQUE ([pub_name])
);
GO

-- ============================================================================
-- system_user_roles
-- ============================================================================

CREATE TABLE [dbo].[system_user_roles] (
  [key_guid]              UNIQUEIDENTIFIER  NOT NULL CONSTRAINT [DF_sur_guid] DEFAULT NEWID(),
  [ref_user_guid]         UNIQUEIDENTIFIER  NOT NULL,
  [ref_role_guid]         UNIQUEIDENTIFIER  NOT NULL,
  [priv_created_on]       DATETIMEOFFSET(7) NOT NULL CONSTRAINT [DF_sur_created_on]  DEFAULT SYSUTCDATETIME(),
  [priv_modified_on]      DATETIMEOFFSET(7) NOT NULL CONSTRAINT [DF_sur_modified_on] DEFAULT SYSUTCDATETIME(),
  CONSTRAINT [PK_system_user_roles]         PRIMARY KEY CLUSTERED ([key_guid]),
  CONSTRAINT [FK_sur_user]                  FOREIGN KEY ([ref_user_guid]) REFERENCES [dbo].[system_users] ([key_guid]),
  CONSTRAINT [FK_sur_role]                  FOREIGN KEY ([ref_role_guid]) REFERENCES [dbo].[system_auth_roles] ([key_guid]),
  CONSTRAINT [UQ_system_user_roles_mapping] UNIQUE ([ref_user_guid], [ref_role_guid])
);
GO

CREATE INDEX [IX_sur_user_role] ON [dbo].[system_user_roles] ([ref_user_guid], [ref_role_guid]);
GO

-- ============================================================================
-- system_auth_entitlements
-- ============================================================================

CREATE TABLE [dbo].[system_auth_entitlements] (
  [key_guid]              UNIQUEIDENTIFIER  NOT NULL,
  [pub_name]              NVARCHAR(64)      NOT NULL,
  [pub_display]           NVARCHAR(128)     NOT NULL,
  [priv_created_on]       DATETIMEOFFSET(7) NOT NULL CONSTRAINT [DF_sae_created_on]  DEFAULT SYSUTCDATETIME(),
  [priv_modified_on]      DATETIMEOFFSET(7) NOT NULL CONSTRAINT [DF_sae_modified_on] DEFAULT SYSUTCDATETIME(),
  CONSTRAINT [PK_system_auth_entitlements]      PRIMARY KEY CLUSTERED ([key_guid]),
  CONSTRAINT [UQ_system_auth_entitlements_name] UNIQUE ([pub_name])
);
GO

-- ============================================================================
-- system_user_entitlements
-- ============================================================================

CREATE TABLE [dbo].[system_user_entitlements] (
  [key_guid]              UNIQUEIDENTIFIER  NOT NULL CONSTRAINT [DF_sue_guid] DEFAULT NEWID(),
  [ref_user_guid]         UNIQUEIDENTIFIER  NOT NULL,
  [ref_entitlement_guid]  UNIQUEIDENTIFIER  NOT NULL,
  [priv_created_on]       DATETIMEOFFSET(7) NOT NULL CONSTRAINT [DF_sue_created_on]  DEFAULT SYSUTCDATETIME(),
  [priv_modified_on]      DATETIMEOFFSET(7) NOT NULL CONSTRAINT [DF_sue_modified_on] DEFAULT SYSUTCDATETIME(),
  CONSTRAINT [PK_system_user_entitlements]         PRIMARY KEY CLUSTERED ([key_guid]),
  CONSTRAINT [FK_sue_user]                         FOREIGN KEY ([ref_user_guid])        REFERENCES [dbo].[system_users] ([key_guid]),
  CONSTRAINT [FK_sue_entitlement]                  FOREIGN KEY ([ref_entitlement_guid]) REFERENCES [dbo].[system_auth_entitlements] ([key_guid]),
  CONSTRAINT [UQ_system_user_entitlements_mapping] UNIQUE ([ref_user_guid], [ref_entitlement_guid])
);
GO

CREATE INDEX [IX_sue_user_entitlement] ON [dbo].[system_user_entitlements] ([ref_user_guid], [ref_entitlement_guid]);
GO

-- ============================================================================
-- SEED: Roles — uuid5(NS, 'role:{pub_name}')
-- ============================================================================

INSERT INTO [dbo].[system_auth_roles] ([key_guid], [pub_name], [pub_display], [pub_rpc_domain]) VALUES
(N'B1E44954-D1A6-53B2-A4EB-815692659EFD', N'ROLE_REGISTERED',    N'Registered User',    N'users'),
(N'1F4A424E-3ADA-5D58-9426-C604CF6DD716', N'ROLE_STORAGE',       N'Storage Enabled',    N'storage'),
(N'4144D41A-7072-515B-BA88-239C1F79A53E', N'ROLE_SUPPORT',       N'Support',            N'support'),
(N'B98B539D-553B-5253-8E21-644328D136FE', N'ROLE_MODERATOR',     N'Moderator',          N'moderation'),
(N'7AABB9C3-015F-512A-9A1E-BB103498619D', N'ROLE_FINANCE_ACCT',  N'Accountant',         N'finacct'),
(N'F7627D20-F281-5924-BC5B-6369A4515C01', N'ROLE_FINANCE_APPR',  N'Accounting Manager', N'finappr'),
(N'88D3D657-7220-528B-9DEC-5BD7D326B37B', N'ROLE_DISCORD_ADMIN', N'Discord Admin',      N'discord'),
(N'F88DDA08-C10A-58D3-889F-67BA44C6B06B', N'ROLE_ACCOUNT_ADMIN', N'Account Admin',      N'account'),
(N'70363FE5-E7AE-5D7E-AD7F-72BC80287C66', N'ROLE_FINANCE_ADMIN', N'Finance Admin',      N'finadmin'),
(N'20F0C823-4742-51BE-938B-7AA5B9D36B81', N'ROLE_SYSTEM_ADMIN',  N'System Admin',       N'system'),
(N'E8E1A4CC-0898-59F4-8B03-B2C9804516C0', N'ROLE_SERVICE_ADMIN', N'Service Admin',      N'service');
GO

-- ============================================================================
-- SEED: Entitlements — uuid5(NS, 'entitlement:{pub_name}')
-- ============================================================================

INSERT INTO [dbo].[system_auth_entitlements] ([key_guid], [pub_name], [pub_display]) VALUES
(N'8923E213-68D2-50DA-B846-FB3A5C4DD71D', N'ENABLE_OPENAI_API',  N'OpenAI Generation'),
(N'B4210F5F-F056-5B98-8EBA-4EAE1BE4F8A5', N'ENABLE_LUMAAI_API',  N'LumaAI Generation'),
(N'C1B7B7E2-851D-5EFA-A837-D9E4DD2B179A', N'ENABLE_DISCORD_BOT', N'Discord Bot'),
(N'3D16F6CA-A4DE-59DC-A67C-EDA76B5D53FD', N'ENABLE_MCP_ACCESS',  N'MCP Agent Access');
GO

-- ============================================================================
-- SEED: Admin user — all roles and all entitlements
-- User: 60C28D8D-96D6-4463-8962-1214E915395B
-- ============================================================================

INSERT INTO [dbo].[system_user_roles] ([ref_user_guid], [ref_role_guid]) VALUES
(N'60C28D8D-96D6-4463-8962-1214E915395B', N'B1E44954-D1A6-53B2-A4EB-815692659EFD'),
(N'60C28D8D-96D6-4463-8962-1214E915395B', N'1F4A424E-3ADA-5D58-9426-C604CF6DD716'),
(N'60C28D8D-96D6-4463-8962-1214E915395B', N'4144D41A-7072-515B-BA88-239C1F79A53E'),
(N'60C28D8D-96D6-4463-8962-1214E915395B', N'B98B539D-553B-5253-8E21-644328D136FE'),
(N'60C28D8D-96D6-4463-8962-1214E915395B', N'7AABB9C3-015F-512A-9A1E-BB103498619D'),
(N'60C28D8D-96D6-4463-8962-1214E915395B', N'F7627D20-F281-5924-BC5B-6369A4515C01'),
(N'60C28D8D-96D6-4463-8962-1214E915395B', N'88D3D657-7220-528B-9DEC-5BD7D326B37B'),
(N'60C28D8D-96D6-4463-8962-1214E915395B', N'F88DDA08-C10A-58D3-889F-67BA44C6B06B'),
(N'60C28D8D-96D6-4463-8962-1214E915395B', N'70363FE5-E7AE-5D7E-AD7F-72BC80287C66'),
(N'60C28D8D-96D6-4463-8962-1214E915395B', N'20F0C823-4742-51BE-938B-7AA5B9D36B81'),
(N'60C28D8D-96D6-4463-8962-1214E915395B', N'E8E1A4CC-0898-59F4-8B03-B2C9804516C0');
GO

INSERT INTO [dbo].[system_user_entitlements] ([ref_user_guid], [ref_entitlement_guid]) VALUES
(N'60C28D8D-96D6-4463-8962-1214E915395B', N'8923E213-68D2-50DA-B846-FB3A5C4DD71D'),
(N'60C28D8D-96D6-4463-8962-1214E915395B', N'B4210F5F-F056-5B98-8EBA-4EAE1BE4F8A5'),
(N'60C28D8D-96D6-4463-8962-1214E915395B', N'C1B7B7E2-851D-5EFA-A837-D9E4DD2B179A'),
(N'60C28D8D-96D6-4463-8962-1214E915395B', N'3D16F6CA-A4DE-59DC-A67C-EDA76B5D53FD');
GO

-- ============================================================================
-- SEED: Object tree — register tables
-- ============================================================================

INSERT INTO [dbo].[system_objects_database_tables] ([key_guid], [pub_name], [pub_schema]) VALUES
(N'A578EAB7-B6C4-5BF0-A14D-10BDDC22EA5B', N'system_auth_roles',         N'dbo'),
(N'F809FAD0-0D76-5B67-B986-0CB3B838EF24', N'system_user_roles',         N'dbo'),
(N'F975A8E7-62CA-5922-811E-97B5FE7C5998', N'system_auth_entitlements',  N'dbo'),
(N'B993A463-FA66-5721-A2BA-85515D1C05DB', N'system_user_entitlements',  N'dbo');
GO

-- ============================================================================
-- SEED: Object tree — register columns
-- ============================================================================

DECLARE @T_UUID  UNIQUEIDENTIFIER = N'4D2EB10B-363E-5AF4-826A-9294146244E4';
DECLARE @T_STR   UNIQUEIDENTIFIER = N'0093B404-1EEE-563D-9135-4B9E7EECA7A2';
DECLARE @T_DTZ   UNIQUEIDENTIFIER = N'70F890D3-5AB5-5250-860E-4F7F9624190C';

DECLARE @TBL_ROLES    UNIQUEIDENTIFIER = N'A578EAB7-B6C4-5BF0-A14D-10BDDC22EA5B';
DECLARE @TBL_UROLES   UNIQUEIDENTIFIER = N'F809FAD0-0D76-5B67-B986-0CB3B838EF24';
DECLARE @TBL_ENTITLE  UNIQUEIDENTIFIER = N'F975A8E7-62CA-5922-811E-97B5FE7C5998';
DECLARE @TBL_UENTITLE UNIQUEIDENTIFIER = N'B993A463-FA66-5721-A2BA-85515D1C05DB';

-- system_auth_roles
INSERT INTO [dbo].[system_objects_database_columns] ([key_guid],[ref_table_guid],[ref_type_guid],[pub_name],[pub_ordinal],[pub_is_nullable],[pub_is_primary_key],[pub_is_identity],[pub_default],[pub_max_length]) VALUES
(N'AA276608-C963-592B-87BF-0B2C99A44148',@TBL_ROLES,@T_UUID,N'key_guid',       1,0,1,0,NULL,              NULL),
(N'04267D58-57F1-5263-9D4E-5B0DEF0F6C71',@TBL_ROLES,@T_STR, N'pub_name',       2,0,0,0,NULL,              64),
(N'8D864AF4-1135-5A22-B404-DC65518CFDC4',@TBL_ROLES,@T_STR, N'pub_display',    3,0,0,0,NULL,              128),
(N'6547AB30-EAB8-516C-99F9-392F553336EF',@TBL_ROLES,@T_STR, N'pub_rpc_domain', 4,1,0,0,NULL,              64),
(N'C85234AC-8447-560E-B16A-E810D59BB0BC',@TBL_ROLES,@T_DTZ, N'priv_created_on',5,0,0,0,N'SYSUTCDATETIME()',NULL),
(N'8782513E-852A-55E0-9052-DFF7E1DB63E4',@TBL_ROLES,@T_DTZ, N'priv_modified_on',6,0,0,0,N'SYSUTCDATETIME()',NULL);

-- system_user_roles
INSERT INTO [dbo].[system_objects_database_columns] ([key_guid],[ref_table_guid],[ref_type_guid],[pub_name],[pub_ordinal],[pub_is_nullable],[pub_is_primary_key],[pub_is_identity],[pub_default],[pub_max_length]) VALUES
(N'35FF4CA7-F636-5952-BB73-771E012C70B6',@TBL_UROLES,@T_UUID,N'key_guid',        1,0,1,0,N'NEWID()',          NULL),
(N'647B9F7D-DB91-5764-AD18-EED31E4F73E6',@TBL_UROLES,@T_UUID,N'ref_user_guid',   2,0,0,0,NULL,               NULL),
(N'D5AA5306-BCB9-5E39-99B1-F2FB5023957A',@TBL_UROLES,@T_UUID,N'ref_role_guid',   3,0,0,0,NULL,               NULL),
(N'D5A4195D-45F9-5A69-8316-D8268B922592',@TBL_UROLES,@T_DTZ, N'priv_created_on', 4,0,0,0,N'SYSUTCDATETIME()',NULL),
(N'B9910AF0-C417-5090-9AAB-16C5112AF15E',@TBL_UROLES,@T_DTZ, N'priv_modified_on',5,0,0,0,N'SYSUTCDATETIME()',NULL);

-- system_auth_entitlements
INSERT INTO [dbo].[system_objects_database_columns] ([key_guid],[ref_table_guid],[ref_type_guid],[pub_name],[pub_ordinal],[pub_is_nullable],[pub_is_primary_key],[pub_is_identity],[pub_default],[pub_max_length]) VALUES
(N'52B0C21A-6284-5173-9044-3A61804C6167',@TBL_ENTITLE,@T_UUID,N'key_guid',        1,0,1,0,NULL,              NULL),
(N'559C6739-18BD-5609-A031-359434711A90',@TBL_ENTITLE,@T_STR, N'pub_name',        2,0,0,0,NULL,              64),
(N'31754605-3C54-50A8-858D-CE93BC2EB45D',@TBL_ENTITLE,@T_STR, N'pub_display',     3,0,0,0,NULL,              128),
(N'F7CE1A50-81F2-59B5-97B2-EA47E8F3ECA1',@TBL_ENTITLE,@T_DTZ, N'priv_created_on', 4,0,0,0,N'SYSUTCDATETIME()',NULL),
(N'D07450BF-F215-53EA-8571-97DCB0313269',@TBL_ENTITLE,@T_DTZ, N'priv_modified_on',5,0,0,0,N'SYSUTCDATETIME()',NULL);

-- system_user_entitlements
INSERT INTO [dbo].[system_objects_database_columns] ([key_guid],[ref_table_guid],[ref_type_guid],[pub_name],[pub_ordinal],[pub_is_nullable],[pub_is_primary_key],[pub_is_identity],[pub_default],[pub_max_length]) VALUES
(N'E4CB9A17-9AF8-5CB7-9A1D-019A14E84CC7',@TBL_UENTITLE,@T_UUID,N'key_guid',             1,0,1,0,N'NEWID()',          NULL),
(N'AD9A1519-312B-5406-9E0B-E58B224641A1',@TBL_UENTITLE,@T_UUID,N'ref_user_guid',        2,0,0,0,NULL,               NULL),
(N'187129D0-12BE-5280-A0B9-2B5E75024A43',@TBL_UENTITLE,@T_UUID,N'ref_entitlement_guid', 3,0,0,0,NULL,               NULL),
(N'0EFB8E90-E267-564C-8A2C-8B910989339F',@TBL_UENTITLE,@T_DTZ, N'priv_created_on',      4,0,0,0,N'SYSUTCDATETIME()',NULL),
(N'B51F10ED-C722-585B-B634-DC814607E4A2',@TBL_UENTITLE,@T_DTZ, N'priv_modified_on',     5,0,0,0,N'SYSUTCDATETIME()',NULL);
GO

-- ============================================================================
-- SEED: Object tree — register indexes
-- ============================================================================

INSERT INTO [dbo].[system_objects_database_indexes] ([ref_table_guid],[pub_name],[pub_columns],[pub_is_unique]) VALUES
(N'A578EAB7-B6C4-5BF0-A14D-10BDDC22EA5B', N'UQ_system_auth_roles_name',             N'pub_name',                        1),
(N'F809FAD0-0D76-5B67-B986-0CB3B838EF24', N'UQ_system_user_roles_mapping',          N'ref_user_guid,ref_role_guid',     1),
(N'F809FAD0-0D76-5B67-B986-0CB3B838EF24', N'IX_sur_user_role',                      N'ref_user_guid,ref_role_guid',     0),
(N'F975A8E7-62CA-5922-811E-97B5FE7C5998', N'UQ_system_auth_entitlements_name',      N'pub_name',                        1),
(N'B993A463-FA66-5721-A2BA-85515D1C05DB', N'UQ_system_user_entitlements_mapping',   N'ref_user_guid,ref_entitlement_guid', 1),
(N'B993A463-FA66-5721-A2BA-85515D1C05DB', N'IX_sue_user_entitlement',               N'ref_user_guid,ref_entitlement_guid', 0);
GO

-- ============================================================================
-- SEED: Object tree — register FK constraints
-- ============================================================================

DECLARE @TBL_USERS2    UNIQUEIDENTIFIER = N'DCC79235-8429-5731-AF60-092AF3A2E4B0';
DECLARE @TBL_ROLES2    UNIQUEIDENTIFIER = N'A578EAB7-B6C4-5BF0-A14D-10BDDC22EA5B';
DECLARE @TBL_UROLES2   UNIQUEIDENTIFIER = N'F809FAD0-0D76-5B67-B986-0CB3B838EF24';
DECLARE @TBL_ENTITLE2  UNIQUEIDENTIFIER = N'F975A8E7-62CA-5922-811E-97B5FE7C5998';
DECLARE @TBL_UENTITLE2 UNIQUEIDENTIFIER = N'B993A463-FA66-5721-A2BA-85515D1C05DB';

-- system_users.key_guid column GUID (from v0.12.0.0 — need to look up)
DECLARE @COL_USERS_KEYGUID UNIQUEIDENTIFIER;
SELECT @COL_USERS_KEYGUID = [key_guid]
FROM [dbo].[system_objects_database_columns]
WHERE [ref_table_guid] = @TBL_USERS2 AND [pub_name] = N'key_guid';

-- system_auth_roles.key_guid column GUID
DECLARE @COL_ROLES_KEYGUID UNIQUEIDENTIFIER = N'AA276608-C963-592B-87BF-0B2C99A44148';

-- system_auth_entitlements.key_guid column GUID
DECLARE @COL_ENTITLE_KEYGUID UNIQUEIDENTIFIER = N'52B0C21A-6284-5173-9044-3A61804C6167';

-- system_user_roles FK columns
DECLARE @COL_UROLES_USER UNIQUEIDENTIFIER = N'647B9F7D-DB91-5764-AD18-EED31E4F73E6';
DECLARE @COL_UROLES_ROLE UNIQUEIDENTIFIER = N'D5AA5306-BCB9-5E39-99B1-F2FB5023957A';

-- system_user_entitlements FK columns
DECLARE @COL_UENTITLE_USER UNIQUEIDENTIFIER = N'AD9A1519-312B-5406-9E0B-E58B224641A1';
DECLARE @COL_UENTITLE_ENT  UNIQUEIDENTIFIER = N'187129D0-12BE-5280-A0B9-2B5E75024A43';

INSERT INTO [dbo].[system_objects_database_constraints] ([ref_table_guid],[ref_column_guid],[ref_referenced_table_guid],[ref_referenced_column_guid]) VALUES
-- system_user_roles.ref_user_guid → system_users.key_guid
(@TBL_UROLES2,   @COL_UROLES_USER,   @TBL_USERS2,   @COL_USERS_KEYGUID),
-- system_user_roles.ref_role_guid → system_auth_roles.key_guid
(@TBL_UROLES2,   @COL_UROLES_ROLE,   @TBL_ROLES2,   @COL_ROLES_KEYGUID),
-- system_user_entitlements.ref_user_guid → system_users.key_guid
(@TBL_UENTITLE2, @COL_UENTITLE_USER, @TBL_USERS2,   @COL_USERS_KEYGUID),
-- system_user_entitlements.ref_entitlement_guid → system_auth_entitlements.key_guid
(@TBL_UENTITLE2, @COL_UENTITLE_ENT,  @TBL_ENTITLE2, @COL_ENTITLE_KEYGUID);
GO

-- ============================================================================
-- Verification
-- ============================================================================

SELECT 'system_auth_roles' AS [table],         COUNT(*) AS [rows] FROM [dbo].[system_auth_roles];
SELECT 'system_user_roles' AS [table],         COUNT(*) AS [rows] FROM [dbo].[system_user_roles];
SELECT 'system_auth_entitlements' AS [table],  COUNT(*) AS [rows] FROM [dbo].[system_auth_entitlements];
SELECT 'system_user_entitlements' AS [table],  COUNT(*) AS [rows] FROM [dbo].[system_user_entitlements];

-- Show admin user's roles
SELECT r.[pub_name], r.[pub_display], r.[pub_rpc_domain]
FROM [dbo].[system_user_roles] ur
JOIN [dbo].[system_auth_roles] r ON r.[key_guid] = ur.[ref_role_guid]
WHERE ur.[ref_user_guid] = N'60C28D8D-96D6-4463-8962-1214E915395B'
ORDER BY r.[pub_name];

-- Show admin user's entitlements
SELECT e.[pub_name], e.[pub_display]
FROM [dbo].[system_user_entitlements] ue
JOIN [dbo].[system_auth_entitlements] e ON e.[key_guid] = ue.[ref_entitlement_guid]
WHERE ue.[ref_user_guid] = N'60C28D8D-96D6-4463-8962-1214E915395B'
ORDER BY e.[pub_name];

-- Object tree check: tables registered
SELECT [pub_name] FROM [dbo].[system_objects_database_tables] ORDER BY [pub_name];







----------------------------

-- Add unique constraint to prevent duplicate index registrations
ALTER TABLE [dbo].[system_objects_database_indexes]
ADD CONSTRAINT [UQ_sodi_table_name] UNIQUE ([ref_table_guid], [pub_name]);
GO

-- Register it in the object tree
INSERT INTO [dbo].[system_objects_database_indexes] ([ref_table_guid],[pub_name],[pub_columns],[pub_is_unique]) VALUES
(N'F9CEA0AB-2528-563C-BCE0-0CE60A60882F', N'UQ_sodi_table_name', N'ref_table_guid,pub_name', 1);
GO



-- ============================================================================
-- Backfill: service_auth_providers column registrations
-- The v0.12.0.0 seed only registered key_guid. This completes the set.
-- ============================================================================

DECLARE @TBL_SAP      UNIQUEIDENTIFIER = N'6E74766A-38EA-583C-9E08-4060FB5FDC4B';
DECLARE @T_UUID       UNIQUEIDENTIFIER = N'4D2EB10B-363E-5AF4-826A-9294146244E4';
DECLARE @T_STRING     UNIQUEIDENTIFIER = N'0093B404-1EEE-563D-9135-4B9E7EECA7A2';
DECLARE @T_BOOL       UNIQUEIDENTIFIER = N'12B2F03B-E315-50A5-B631-E6B1EB961A17';
DECLARE @T_INT32      UNIQUEIDENTIFIER = N'E3EDE0CE-2A03-501E-A796-3487BEA03B7B';
DECLARE @T_DATETIME_TZ UNIQUEIDENTIFIER = N'70F890D3-5AB5-5250-860E-4F7F9624190C';

INSERT INTO [dbo].[system_objects_database_columns]
  ([key_guid],[ref_table_guid],[ref_type_guid],[pub_name],[pub_ordinal],[pub_is_nullable],[pub_is_primary_key],[pub_is_identity],[pub_default],[pub_max_length])
VALUES
(N'4603FC18-8252-52D9-8BBE-15ADCA334438',@TBL_SAP,@T_STRING,     N'pub_name',               2,0,0,0,NULL,                  64),
(N'D1A1CBCF-E1B2-5792-8023-D4274E86F1B5',@TBL_SAP,@T_STRING,     N'pub_display',             3,0,0,0,NULL,                  128),
(N'04168F83-4D62-58AC-B13D-BC9D1D1F05B0',@TBL_SAP,@T_STRING,     N'pub_authorize_url',       4,1,0,0,NULL,                  2048),
(N'BF77EFAF-AA38-5885-BD1C-1C8ACBB221B4',@TBL_SAP,@T_STRING,     N'pub_token_url',           5,1,0,0,NULL,                  2048),
(N'F57D0F0A-BB81-5192-A368-9499042EE359',@TBL_SAP,@T_STRING,     N'pub_userinfo_url',        6,1,0,0,NULL,                  2048),
(N'C456555F-15C3-5467-9809-7D734CA10271',@TBL_SAP,@T_STRING,     N'pub_openid_config_url',   7,1,0,0,NULL,                  2048),
(N'BD1C0635-2669-5EFB-9314-460D510A2032',@TBL_SAP,@T_STRING,     N'pub_jwks_uri',            8,1,0,0,NULL,                  2048),
(N'E276E3D4-2CAC-5A9A-A818-C5AC08668AB2',@TBL_SAP,@T_STRING,     N'pub_issuer',              9,1,0,0,NULL,                  512),
(N'F99B5372-A4D8-5948-85BF-BA98BE73DC5B',@TBL_SAP,@T_STRING,     N'pub_client_id',          10,0,0,0,NULL,                  512),
(N'12167E37-4484-548C-9BC0-CF7E6CAF42BF',@TBL_SAP,@T_STRING,     N'pub_scopes',             11,0,0,0,NULL,                  1024),
(N'D6E04F41-8C52-5BBB-8F24-D9DCA95C126D',@TBL_SAP,@T_STRING,     N'pub_grant_types',        12,0,0,0,N'authorization_code', 256),
(N'2D21E429-4DDB-54D3-AA3D-2FADDDD7453C',@TBL_SAP,@T_STRING,     N'pub_response_type',      13,0,0,0,N'code',              64),
(N'600BD180-559D-5AA1-9EE5-3F2F24414BE1',@TBL_SAP,@T_BOOL,       N'pub_is_oidc',            14,0,0,0,N'0',                 NULL),
(N'7C15E1E5-9C19-5D4F-B543-7D41ED6CDF5D',@TBL_SAP,@T_BOOL,       N'pub_requires_id_token',  15,0,0,0,N'0',                 NULL),
(N'ABAA248C-E765-53B2-B4CF-8CE3A0D9128D',@TBL_SAP,@T_BOOL,       N'pub_is_active',          16,0,0,0,N'1',                 NULL),
(N'10AB86C9-7CA4-5291-A755-FDD00AF2947F',@TBL_SAP,@T_BOOL,       N'pub_allow_registration', 17,0,0,0,N'0',                 NULL),
(N'F18108D9-76E5-5BB2-87E8-732EA8307A32',@TBL_SAP,@T_STRING,     N'pub_identifier_claim',   18,0,0,0,NULL,                  64),
(N'E6E43FD5-E06E-59E0-BE6F-8F5B6B22243E',@TBL_SAP,@T_STRING,     N'pub_email_claim',        19,0,0,0,N'email',             64),
(N'C260A4B7-FB9B-5F40-ACCD-5CB2BB625972',@TBL_SAP,@T_STRING,     N'pub_display_claim',      20,0,0,0,N'name',              64),
(N'75BC0522-C397-56F6-9CB1-ABB150CCC56C',@TBL_SAP,@T_STRING,     N'pub_avatar_claim',       21,1,0,0,NULL,                  64),
(N'1657DFFC-0C5F-51D8-8EE3-AC0DEBC62649',@TBL_SAP,@T_STRING,     N'pub_avatar_url_pattern', 22,1,0,0,NULL,                  512),
(N'859444C5-F426-5E91-A1B4-BE64A887CB68',@TBL_SAP,@T_INT32,      N'pub_sequence',           23,0,0,0,N'0',                 NULL),
(N'5263B81B-B725-5663-8761-A2C3C72AAC0A',@TBL_SAP,@T_DATETIME_TZ,N'priv_created_on',        24,0,0,0,N'SYSUTCDATETIME()',  NULL),
(N'180D1942-FDD0-5866-8BEF-115A04B345F1',@TBL_SAP,@T_DATETIME_TZ,N'priv_modified_on',       25,0,0,0,N'SYSUTCDATETIME()',  NULL);
GO

-- Verification: should now show 25 columns for service_auth_providers
SELECT COUNT(*) AS [service_auth_providers_columns]
FROM [dbo].[system_objects_database_columns]
WHERE [ref_table_guid] = N'6E74766A-38EA-583C-9E08-4060FB5FDC4B';