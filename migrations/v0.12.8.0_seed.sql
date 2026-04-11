-- ============================================================================
-- TheOracleRPC v0.12.8.0 — Query Storage & Session Query Seeds
-- Date: 2026-04-11
-- Purpose:
--   Create system_objects_queries table for data-driven query storage.
--   Seed all session and agent management queries as database rows.
--   Register UserContext1 RPC model and get_user_context module method.
--
--   This replaces the legacy pattern of hardcoded SQL in
--   queryregistry/*/mssql.py files. Modules load queries from this table
--   at startup and execute them through DbModule with parameters.
--
-- UUID5 namespace: DECAFBAD-CAFE-FADE-BABE-C0FFEE420B67
-- Query GUIDs: uuid5(NS, 'query:{domain}.{subdomain}.{operation}')
-- ============================================================================


-- ============================================================================
-- PHASE 1: Create system_objects_queries table
-- ============================================================================

CREATE TABLE [dbo].[system_objects_queries] (
  [key_guid]              UNIQUEIDENTIFIER  NOT NULL,
  [pub_name]              NVARCHAR(256)     NOT NULL,
  [pub_query_text]        NVARCHAR(MAX)     NOT NULL,
  [pub_description]       NVARCHAR(512)     NULL,
  [ref_module_guid]       UNIQUEIDENTIFIER  NULL,
  [pub_is_parameterized]  BIT               NOT NULL  CONSTRAINT [DF_soq_param]       DEFAULT 0,
  [pub_parameter_names]   NVARCHAR(1024)    NULL,
  [pub_is_active]         BIT               NOT NULL  CONSTRAINT [DF_soq_active]      DEFAULT 1,
  [priv_created_on]       DATETIMEOFFSET(7) NOT NULL  CONSTRAINT [DF_soq_created_on]  DEFAULT SYSUTCDATETIME(),
  [priv_modified_on]      DATETIMEOFFSET(7) NOT NULL  CONSTRAINT [DF_soq_modified_on] DEFAULT SYSUTCDATETIME(),
  CONSTRAINT [PK_system_objects_queries]      PRIMARY KEY CLUSTERED ([key_guid]),
  CONSTRAINT [UQ_soq_name]                   UNIQUE ([pub_name]),
  CONSTRAINT [FK_soq_module]                 FOREIGN KEY ([ref_module_guid]) REFERENCES [dbo].[system_objects_modules] ([key_guid])
);
GO

CREATE INDEX [IX_soq_module] ON [dbo].[system_objects_queries] ([ref_module_guid]);
GO


-- ============================================================================
-- PHASE 2: Seed session management queries
-- ============================================================================

-- Module GUID for SessionModule (from v0.12.5.0)
DECLARE @MOD_SESSION UNIQUEIDENTIFIER = N'6D818DCB-5B60-5B80-91F1-A1D19DC03110';

-- --- security.sessions queries ---

INSERT INTO [dbo].[system_objects_queries]
  ([key_guid], [pub_name], [pub_description], [ref_module_guid], [pub_is_parameterized], [pub_parameter_names], [pub_query_text])
VALUES
(N'A0EF3C0E-1104-5DED-9E57-06AA36A1E6DB',
 N'security.sessions.create_session',
 N'Create a session, three tokens (access/refresh/rotation), and a device record. Returns session_guid, device_guid.',
 @MOD_SESSION, 1,
 N'user_guid,session_type_guid,expires_at,access_hash,access_scopes,access_expires,refresh_hash,refresh_scopes,refresh_expires,rotation_hash,rotation_expires,device_fingerprint,user_agent,ip_address',
 N'SET NOCOUNT ON;
DECLARE @session_guid UNIQUEIDENTIFIER = NEWID();
DECLARE @device_guid  UNIQUEIDENTIFIER = NEWID();

INSERT INTO [dbo].[system_sessions]
  ([key_guid], [ref_user_guid], [ref_session_type_guid], [pub_expires_at])
VALUES
  (@session_guid, TRY_CAST(? AS UNIQUEIDENTIFIER), TRY_CAST(? AS UNIQUEIDENTIFIER), TRY_CAST(? AS DATETIMEOFFSET(7)));

INSERT INTO [dbo].[system_session_tokens]
  ([ref_session_guid], [ref_token_type_guid], [pub_token_hash], [pub_scopes], [pub_expires_at])
VALUES
  (@session_guid, N''8AA0F073-7CA1-5375-9989-67DB2688BDF5'', ?, ?, TRY_CAST(? AS DATETIMEOFFSET(7))),
  (@session_guid, N''8E312303-3EA8-5D6F-9341-D201D5A9ABA6'', ?, ?, TRY_CAST(? AS DATETIMEOFFSET(7))),
  (@session_guid, N''C5551771-3FBD-5357-9302-821DE44D73B8'', ?, NULL, TRY_CAST(? AS DATETIMEOFFSET(7)));

INSERT INTO [dbo].[system_session_devices]
  ([key_guid], [ref_session_guid], [pub_device_fingerprint], [pub_user_agent], [pub_ip_address], [pub_last_seen_at])
VALUES
  (@device_guid, @session_guid, ?, ?, ?, SYSUTCDATETIME());

SELECT @session_guid AS session_guid, @device_guid AS device_guid
FOR JSON PATH, WITHOUT_ARRAY_WRAPPER;');

INSERT INTO [dbo].[system_objects_queries]
  ([key_guid], [pub_name], [pub_description], [ref_module_guid], [pub_is_parameterized], [pub_parameter_names], [pub_query_text])
VALUES
(N'C659C7B8-4CFE-5C9E-9802-C6CACB82B483',
 N'security.sessions.create_token',
 N'Create a single token for an existing session. Used for token rotation.',
 @MOD_SESSION, 1,
 N'session_guid,token_type_guid,token_hash,scopes,expires_at',
 N'INSERT INTO [dbo].[system_session_tokens]
  ([ref_session_guid], [ref_token_type_guid], [pub_token_hash], [pub_scopes], [pub_expires_at])
VALUES
  (TRY_CAST(? AS UNIQUEIDENTIFIER), TRY_CAST(? AS UNIQUEIDENTIFIER), ?, ?, TRY_CAST(? AS DATETIMEOFFSET(7)));');

INSERT INTO [dbo].[system_objects_queries]
  ([key_guid], [pub_name], [pub_description], [ref_module_guid], [pub_is_parameterized], [pub_parameter_names], [pub_query_text])
VALUES
(N'3EAB8271-325E-5388-93B8-DA4F0B3BB0C7',
 N'security.sessions.validate_token',
 N'Validate a token by hash. Returns session and user info if token is valid, active, and not expired.',
 @MOD_SESSION, 1,
 N'token_hash',
 N'SELECT
  t.[key_guid]           AS token_guid,
  t.[ref_session_guid]   AS session_guid,
  t.[pub_scopes]         AS scopes,
  t.[pub_expires_at]     AS token_expires_at,
  s.[ref_user_guid]      AS user_guid,
  s.[pub_is_active]      AS session_active,
  s.[pub_expires_at]     AS session_expires_at,
  st.[pub_name]          AS session_type,
  tt.[pub_name]          AS token_type
FROM [dbo].[system_session_tokens] t
JOIN [dbo].[system_sessions] s ON s.[key_guid] = t.[ref_session_guid]
JOIN [dbo].[service_enum_values] st ON st.[key_guid] = s.[ref_session_type_guid]
JOIN [dbo].[service_enum_values] tt ON tt.[key_guid] = t.[ref_token_type_guid]
WHERE t.[pub_token_hash] = ?
  AND t.[pub_revoked_at] IS NULL
  AND t.[pub_expires_at] > SYSUTCDATETIME()
  AND s.[pub_is_active] = 1
  AND s.[pub_revoked_at] IS NULL
FOR JSON PATH, WITHOUT_ARRAY_WRAPPER, INCLUDE_NULL_VALUES;');

INSERT INTO [dbo].[system_objects_queries]
  ([key_guid], [pub_name], [pub_description], [ref_module_guid], [pub_is_parameterized], [pub_parameter_names], [pub_query_text])
VALUES
(N'BDD85106-1FD0-5DD9-9654-3F2684DEC48A',
 N'security.sessions.revoke_session',
 N'Revoke an entire session. All child tokens become invalid.',
 @MOD_SESSION, 1,
 N'session_guid',
 N'UPDATE [dbo].[system_sessions]
SET [pub_is_active] = 0,
    [pub_revoked_at] = SYSUTCDATETIME(),
    [priv_modified_on] = SYSUTCDATETIME()
WHERE [key_guid] = TRY_CAST(? AS UNIQUEIDENTIFIER);');

INSERT INTO [dbo].[system_objects_queries]
  ([key_guid], [pub_name], [pub_description], [ref_module_guid], [pub_is_parameterized], [pub_parameter_names], [pub_query_text])
VALUES
(N'3F203528-0F06-52B1-9464-E04027F6E828',
 N'security.sessions.revoke_token',
 N'Revoke a single token by hash.',
 @MOD_SESSION, 1,
 N'token_hash',
 N'UPDATE [dbo].[system_session_tokens]
SET [pub_revoked_at] = SYSUTCDATETIME()
WHERE [pub_token_hash] = ?;');

INSERT INTO [dbo].[system_objects_queries]
  ([key_guid], [pub_name], [pub_description], [ref_module_guid], [pub_is_parameterized], [pub_parameter_names], [pub_query_text])
VALUES
(N'C25B1991-4B62-57A6-BC5E-231CBCF1C990',
 N'security.sessions.update_device',
 N'Update device metadata (last seen, IP, user agent).',
 @MOD_SESSION, 1,
 N'session_guid,ip_address,user_agent',
 N'UPDATE [dbo].[system_session_devices]
SET [pub_last_seen_at] = SYSUTCDATETIME(),
    [pub_ip_address] = ?,
    [pub_user_agent] = ?,
    [priv_modified_on] = SYSUTCDATETIME()
WHERE [ref_session_guid] = TRY_CAST(? AS UNIQUEIDENTIFIER);');

INSERT INTO [dbo].[system_objects_queries]
  ([key_guid], [pub_name], [pub_description], [ref_module_guid], [pub_is_parameterized], [pub_parameter_names], [pub_query_text])
VALUES
(N'32CDABAC-ED9C-59FE-A947-7A590B9B8BCB',
 N'security.sessions.get_session',
 N'Get session with device metadata by session GUID.',
 @MOD_SESSION, 1,
 N'session_guid',
 N'SELECT
  s.[key_guid]              AS session_guid,
  s.[ref_user_guid]         AS user_guid,
  s.[pub_is_active]         AS is_active,
  s.[pub_expires_at]        AS expires_at,
  s.[pub_revoked_at]        AS revoked_at,
  st.[pub_name]             AS session_type,
  d.[pub_device_fingerprint] AS device_fingerprint,
  d.[pub_user_agent]        AS user_agent,
  d.[pub_ip_address]        AS ip_address,
  d.[pub_last_seen_at]      AS last_seen_at
FROM [dbo].[system_sessions] s
JOIN [dbo].[service_enum_values] st ON st.[key_guid] = s.[ref_session_type_guid]
LEFT JOIN [dbo].[system_session_devices] d ON d.[ref_session_guid] = s.[key_guid]
WHERE s.[key_guid] = TRY_CAST(? AS UNIQUEIDENTIFIER)
FOR JSON PATH, WITHOUT_ARRAY_WRAPPER, INCLUDE_NULL_VALUES;');

INSERT INTO [dbo].[system_objects_queries]
  ([key_guid], [pub_name], [pub_description], [ref_module_guid], [pub_is_parameterized], [pub_parameter_names], [pub_query_text])
VALUES
(N'35E791CC-89FD-52E1-B253-FC549EFDBADA',
 N'security.sessions.get_user_context',
 N'Assemble UserContext for a user: display, email, role names, entitlement names, linked provider names. No GUIDs in output.',
 @MOD_SESSION, 1,
 N'user_guid',
 N'SELECT
  u.[pub_display]     AS display,
  u.[pub_email]       AS email,
  (SELECT r.[pub_name] AS name
   FROM [dbo].[system_user_roles] ur
   JOIN [dbo].[system_auth_roles] r ON r.[key_guid] = ur.[ref_role_guid]
   WHERE ur.[ref_user_guid] = u.[key_guid]
   FOR JSON PATH) AS roles,
  (SELECT e.[pub_name] AS name
   FROM [dbo].[system_user_entitlements] ue
   JOIN [dbo].[system_auth_entitlements] e ON e.[key_guid] = ue.[ref_entitlement_guid]
   WHERE ue.[ref_user_guid] = u.[key_guid]
   FOR JSON PATH) AS entitlements,
  (SELECT p.[pub_name] AS name
   FROM [dbo].[system_user_auth] ua
   JOIN [dbo].[service_auth_providers] p ON p.[key_guid] = ua.[ref_provider_guid]
   WHERE ua.[ref_user_guid] = u.[key_guid] AND ua.[pub_is_linked] = 1
   FOR JSON PATH) AS providers
FROM [dbo].[system_users] u
WHERE u.[key_guid] = TRY_CAST(? AS UNIQUEIDENTIFIER)
FOR JSON PATH, WITHOUT_ARRAY_WRAPPER, INCLUDE_NULL_VALUES;');
GO


-- ============================================================================
-- PHASE 3: Seed agent management queries
-- ============================================================================

DECLARE @MOD_SESSION2 UNIQUEIDENTIFIER = N'6D818DCB-5B60-5B80-91F1-A1D19DC03110';

INSERT INTO [dbo].[system_objects_queries]
  ([key_guid], [pub_name], [pub_description], [ref_module_guid], [pub_is_parameterized], [pub_parameter_names], [pub_query_text])
VALUES
(N'6D169F7B-7C55-5409-ABBF-55B99EA14242',
 N'security.agents.get_client_by_id',
 N'Look up agent client by external pub_client_id.',
 @MOD_SESSION2, 1,
 N'client_id',
 N'SELECT
  [key_guid]          AS client_guid,
  [pub_client_id]     AS client_id,
  [pub_client_name]   AS client_name,
  [pub_redirect_uris] AS redirect_uris,
  [pub_grant_types]   AS grant_types,
  [pub_response_types] AS response_types,
  [pub_scopes]        AS scopes,
  [pub_is_dcr]        AS is_dcr,
  [pub_is_active]     AS is_active,
  [pub_revoked_at]    AS revoked_at
FROM [dbo].[service_agent_clients]
WHERE [pub_client_id] = TRY_CAST(? AS UNIQUEIDENTIFIER)
FOR JSON PATH, WITHOUT_ARRAY_WRAPPER, INCLUDE_NULL_VALUES;');

INSERT INTO [dbo].[system_objects_queries]
  ([key_guid], [pub_name], [pub_description], [ref_module_guid], [pub_is_parameterized], [pub_parameter_names], [pub_query_text])
VALUES
(N'F31C0C51-4852-54F4-BE4C-0A68E2770B67',
 N'security.agents.link_client_user',
 N'Link an agent client to a user.',
 @MOD_SESSION2, 1,
 N'client_guid,user_guid',
 N'INSERT INTO [dbo].[service_agent_client_users]
  ([ref_client_guid], [ref_user_guid])
VALUES
  (TRY_CAST(? AS UNIQUEIDENTIFIER), TRY_CAST(? AS UNIQUEIDENTIFIER));');

INSERT INTO [dbo].[system_objects_queries]
  ([key_guid], [pub_name], [pub_description], [ref_module_guid], [pub_is_parameterized], [pub_parameter_names], [pub_query_text])
VALUES
(N'C4C8ECE4-1B09-5F58-AF35-02AC881BEAFA',
 N'security.agents.create_auth_code',
 N'Create an OAuth authorization code for PKCE flow.',
 @MOD_SESSION2, 1,
 N'client_guid,user_guid,code,code_challenge,code_method,redirect_uri,scopes,expires_at',
 N'INSERT INTO [dbo].[service_agent_auth_codes]
  ([ref_client_guid], [ref_user_guid], [pub_code], [pub_code_challenge],
   [pub_code_method], [pub_redirect_uri], [pub_scopes], [pub_expires_at])
VALUES
  (TRY_CAST(? AS UNIQUEIDENTIFIER), TRY_CAST(? AS UNIQUEIDENTIFIER),
   ?, ?, ?, ?, ?, TRY_CAST(? AS DATETIMEOFFSET(7)));');

INSERT INTO [dbo].[system_objects_queries]
  ([key_guid], [pub_name], [pub_description], [ref_module_guid], [pub_is_parameterized], [pub_parameter_names], [pub_query_text])
VALUES
(N'91C45A54-E578-5C24-A169-50D8F572F7BE',
 N'security.agents.consume_auth_code',
 N'Consume an auth code (mark used). Returns the code row for PKCE verification. Only consumes if not expired and not already consumed.',
 @MOD_SESSION2, 1,
 N'code',
 N'SET NOCOUNT ON;
UPDATE [dbo].[service_agent_auth_codes]
SET [pub_consumed] = 1
WHERE [pub_code] = ?
  AND [pub_consumed] = 0
  AND [pub_expires_at] > SYSUTCDATETIME();

SELECT
  ac.[key_guid]             AS code_guid,
  ac.[ref_client_guid]      AS client_guid,
  ac.[ref_user_guid]        AS user_guid,
  ac.[pub_code_challenge]   AS code_challenge,
  ac.[pub_code_method]      AS code_method,
  ac.[pub_redirect_uri]     AS redirect_uri,
  ac.[pub_scopes]           AS scopes,
  c.[pub_client_id]         AS client_id,
  c.[pub_is_active]         AS client_active
FROM [dbo].[service_agent_auth_codes] ac
JOIN [dbo].[service_agent_clients] c ON c.[key_guid] = ac.[ref_client_guid]
WHERE ac.[pub_code] = ?
  AND ac.[pub_consumed] = 1
FOR JSON PATH, WITHOUT_ARRAY_WRAPPER, INCLUDE_NULL_VALUES;');

INSERT INTO [dbo].[system_objects_queries]
  ([key_guid], [pub_name], [pub_description], [ref_module_guid], [pub_is_parameterized], [pub_parameter_names], [pub_query_text])
VALUES
(N'2FB0CA06-C333-59A9-A0AD-375CEBFFDEE0',
 N'security.agents.list_user_clients',
 N'List all agent clients linked to a user.',
 @MOD_SESSION2, 1,
 N'user_guid',
 N'SELECT
  c.[pub_client_id]     AS client_id,
  c.[pub_client_name]   AS client_name,
  c.[pub_scopes]        AS scopes,
  c.[pub_is_active]     AS is_active,
  c.[pub_is_dcr]        AS is_dcr,
  cu.[priv_created_on]  AS linked_on
FROM [dbo].[service_agent_clients] c
JOIN [dbo].[service_agent_client_users] cu ON cu.[ref_client_guid] = c.[key_guid]
WHERE cu.[ref_user_guid] = TRY_CAST(? AS UNIQUEIDENTIFIER)
ORDER BY c.[pub_client_name]
FOR JSON PATH, INCLUDE_NULL_VALUES;');

INSERT INTO [dbo].[system_objects_queries]
  ([key_guid], [pub_name], [pub_description], [ref_module_guid], [pub_is_parameterized], [pub_parameter_names], [pub_query_text])
VALUES
(N'289DE571-DF67-568F-9E6B-69DED3E7FEA5',
 N'security.agents.revoke_client',
 N'Revoke an agent client by pub_client_id.',
 @MOD_SESSION2, 1,
 N'client_id',
 N'UPDATE [dbo].[service_agent_clients]
SET [pub_is_active] = 0,
    [pub_revoked_at] = SYSUTCDATETIME(),
    [priv_modified_on] = SYSUTCDATETIME()
WHERE [pub_client_id] = TRY_CAST(? AS UNIQUEIDENTIFIER);');
GO


-- ============================================================================
-- PHASE 4: Register UserContext1 model and get_user_context method
-- ============================================================================

-- RPC Model: UserContext1
INSERT INTO [dbo].[system_objects_rpc_models] ([key_guid], [pub_name], [pub_version], [pub_description])
VALUES (N'5D3EA455-969B-58CA-A6F2-78B31238F443', N'UserContext1', 1, N'Server-assembled identity snapshot returned to clients. Contains no internal GUIDs.');

-- Model fields
DECLARE @T_STR_GUID  UNIQUEIDENTIFIER = N'0093B404-1EEE-563D-9135-4B9E7EECA7A2';
DECLARE @T_BOOL_GUID UNIQUEIDENTIFIER = N'12B2F03B-E315-50A5-B631-E6B1EB961A17';
DECLARE @MODEL_UC    UNIQUEIDENTIFIER = N'5D3EA455-969B-58CA-A6F2-78B31238F443';

INSERT INTO [dbo].[system_objects_rpc_model_fields]
  ([key_guid], [ref_model_guid], [pub_name], [pub_ordinal], [ref_type_guid], [pub_is_nullable], [pub_is_list])
VALUES
(N'38680BAA-7E18-52F4-95DB-08DCCBAA7F63', @MODEL_UC, N'display',         1, @T_STR_GUID,  0, 0),
(N'0B023128-16B0-546E-9A83-94507610C529', @MODEL_UC, N'email',           2, @T_STR_GUID,  0, 0),
(N'A072C69D-B38D-593E-B6A7-3B01A9D36662', @MODEL_UC, N'roles',           3, @T_STR_GUID,  0, 1),
(N'42353559-638A-54CA-B5FB-E3D7053DC0A5', @MODEL_UC, N'entitlements',    4, @T_STR_GUID,  0, 1),
(N'8C576931-B149-579B-9868-8EC00534C50F', @MODEL_UC, N'providers',       5, @T_STR_GUID,  0, 1),
(N'7092257F-7A0B-5E3F-BF8E-1B7FE602379E', @MODEL_UC, N'sessionType',    6, @T_STR_GUID,  0, 0),
(N'B1E42A19-5119-5B33-90DC-305872C6BACC', @MODEL_UC, N'isAuthenticated',7, @T_BOOL_GUID, 0, 0);
GO

-- Module method: SessionModule.get_user_context
INSERT INTO [dbo].[system_objects_module_methods]
  ([key_guid], [ref_module_guid], [pub_name], [ref_request_model_guid], [ref_response_model_guid])
VALUES
  (N'C57DE8A4-674B-5D1D-AE99-A2D8CC529E11',
   N'6D818DCB-5B60-5B80-91F1-A1D19DC03110',
   N'get_user_context', NULL,
   N'5D3EA455-969B-58CA-A6F2-78B31238F443');
GO


-- ============================================================================
-- PHASE 5: Object Tree Self-Registration
-- ============================================================================

-- 5a: Register table
INSERT INTO [dbo].[system_objects_database_tables] ([key_guid], [pub_name], [pub_schema])
VALUES (N'069D41E1-658D-5FB9-B6F2-1C5363D23320', N'system_objects_queries', N'dbo');
GO

-- 5b: Register columns
DECLARE @T_UUID3  UNIQUEIDENTIFIER = N'4D2EB10B-363E-5AF4-826A-9294146244E4';
DECLARE @T_STR3   UNIQUEIDENTIFIER = N'0093B404-1EEE-563D-9135-4B9E7EECA7A2';
DECLARE @T_TEXT3  UNIQUEIDENTIFIER = N'DCA18974-D648-5DFF-AEFB-122C081145AA';
DECLARE @T_BOOL3  UNIQUEIDENTIFIER = N'12B2F03B-E315-50A5-B631-E6B1EB961A17';
DECLARE @T_DTZ3   UNIQUEIDENTIFIER = N'70F890D3-5AB5-5250-860E-4F7F9624190C';
DECLARE @TBL_SOQ  UNIQUEIDENTIFIER = N'069D41E1-658D-5FB9-B6F2-1C5363D23320';

INSERT INTO [dbo].[system_objects_database_columns]
  ([key_guid],[ref_table_guid],[ref_type_guid],[pub_name],[pub_ordinal],
   [pub_is_nullable],[pub_is_primary_key],[pub_is_identity],[pub_default],[pub_max_length])
VALUES
(N'ABA31F04-FDF3-52A3-B888-879E1120939F',@TBL_SOQ,@T_UUID3,N'key_guid',             1,0,1,0,NULL,               NULL),
(N'BBAB6579-2437-50B3-B18F-906783BA7479',@TBL_SOQ,@T_STR3, N'pub_name',             2,0,0,0,NULL,               256),
(N'645C67DB-06B0-51AF-80A4-0E0B94239984',@TBL_SOQ,@T_TEXT3,N'pub_query_text',       3,0,0,0,NULL,               NULL),
(N'EE6824DB-5202-54E6-AA78-12617C25B36E',@TBL_SOQ,@T_STR3, N'pub_description',      4,1,0,0,NULL,               512),
(N'5343A6EC-50A0-5399-8E8B-114201FA3A2E',@TBL_SOQ,@T_UUID3,N'ref_module_guid',      5,1,0,0,NULL,               NULL),
(N'02E169FB-9EEF-5A99-8140-89608858D028',@TBL_SOQ,@T_BOOL3,N'pub_is_parameterized', 6,0,0,0,N'0',              NULL),
(N'D34CE20F-D6F1-5291-AA0D-F94A2B4C2016',@TBL_SOQ,@T_STR3, N'pub_parameter_names',  7,1,0,0,NULL,               1024),
(N'726D2D32-D163-532C-9455-360A1669A7DB',@TBL_SOQ,@T_BOOL3,N'pub_is_active',        8,0,0,0,N'1',              NULL),
(N'AE848C7E-1FF1-5256-842B-320167EAFF42',@TBL_SOQ,@T_DTZ3, N'priv_created_on',      9,0,0,0,N'SYSUTCDATETIME()',NULL),
(N'09D75271-462E-5E7B-8B84-20989030E21A',@TBL_SOQ,@T_DTZ3, N'priv_modified_on',     10,0,0,0,N'SYSUTCDATETIME()',NULL);
GO

-- 5c: Register FK constraint
DECLARE @TBL_SOQ2     UNIQUEIDENTIFIER = N'069D41E1-658D-5FB9-B6F2-1C5363D23320';
DECLARE @TBL_MODULES2 UNIQUEIDENTIFIER = N'D039D8FB-3F95-5A66-B7FB-AB4BA1301FEA';
DECLARE @COL_SOQ_MOD  UNIQUEIDENTIFIER = N'5343A6EC-50A0-5399-8E8B-114201FA3A2E'; -- system_objects_queries.ref_module_guid
DECLARE @COL_MOD_PK   UNIQUEIDENTIFIER = N'F9B4AE84-8D66-5E23-842B-9BB7D1D8E25E'; -- system_objects_modules.key_guid (from backfill)

INSERT INTO [dbo].[system_objects_database_constraints]
  ([ref_table_guid],[ref_column_guid],[ref_referenced_table_guid],[ref_referenced_column_guid])
VALUES
  (@TBL_SOQ2, @COL_SOQ_MOD, @TBL_MODULES2, @COL_MOD_PK);
GO


-- ============================================================================
-- PHASE 6: Verification
-- ============================================================================

SELECT 'system_objects_queries' AS [table], COUNT(*) AS [rows] FROM [dbo].[system_objects_queries];

-- All seeded queries
SELECT [pub_name], [pub_is_parameterized] AS [parameterized],
       LEN([pub_query_text]) AS [sql_length],
       [pub_parameter_names]
FROM [dbo].[system_objects_queries]
ORDER BY [pub_name];

-- UserContext1 model
SELECT m.[pub_name] AS model, f.[pub_name] AS field, t.[pub_name] AS type, f.[pub_is_list] AS is_list
FROM [dbo].[system_objects_rpc_model_fields] f
JOIN [dbo].[system_objects_rpc_models] m ON m.[key_guid] = f.[ref_model_guid]
LEFT JOIN [dbo].[system_objects_types] t ON t.[key_guid] = f.[ref_type_guid]
WHERE m.[pub_name] = N'UserContext1'
ORDER BY f.[pub_ordinal];

-- get_user_context method registration
SELECT mod.[pub_name] AS module, mm.[pub_name] AS method, rm.[pub_name] AS response_model
FROM [dbo].[system_objects_module_methods] mm
JOIN [dbo].[system_objects_modules] mod ON mod.[key_guid] = mm.[ref_module_guid]
LEFT JOIN [dbo].[system_objects_rpc_models] rm ON rm.[key_guid] = mm.[ref_response_model_guid]
WHERE mm.[pub_name] = N'get_user_context';

-- Object tree self-registration check
SELECT t.[pub_name], COUNT(c.[key_guid]) AS columns
FROM [dbo].[system_objects_database_tables] t
LEFT JOIN [dbo].[system_objects_database_columns] c ON c.[ref_table_guid] = t.[key_guid]
WHERE t.[pub_name] = N'system_objects_queries'
GROUP BY t.[pub_name];