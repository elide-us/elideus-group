-- =============================================================================
-- v0.12.12.0_object_tree_categories (CORRECTED)
-- Date: 2026-04-12
-- Purpose:
--   1) Add pub_icon column to service_enum_values (ALTER TABLE, idempotent)
--   2) Register pub_icon column in system_objects_database_columns metadata
--   3) Seed object_tree_categories enum category + 14 top-level values
--   4) Create system_objects_tree_category_tables mapping table
--   5) Self-register the new table in object tree metadata (table, columns, indexes, constraints)
--   6) Seed category → backing table mappings with root table markers
--
-- CORRECTIONS from Codex output:
--   - Icon names changed from Lucide-style to MUI @mui/icons-material names
--     (DynamicIcon component does MuiIcons[name] lookup)
--   - Categories restored to 14 top-level domains from design doc instead of
--     per-table decomposition. Each category groups related tables, not 1:1.
--   - Missing categories added: Security, Sessions, Agents, Configuration,
--     RPC Surface
--   - Removed sub-table categories (module_methods, component_tree,
--     type_controls, gateway_identity_providers, gateway_method_bindings)
--     — these are child tables within their parent category, not top-level nodes
--
-- UUID5 namespace: DECAFBAD-CAFE-FADE-BABE-C0FFEE420B67
-- Category enum:   uuid5(NS, 'enum_category:object_tree_categories')
-- Category values:  uuid5(NS, 'object_tree:{pub_name}')
-- =============================================================================

-- =============================================================================
-- 1) ALTER TABLE: add pub_icon to service_enum_values
-- =============================================================================
IF COL_LENGTH(N'dbo.service_enum_values', N'pub_icon') IS NULL
BEGIN
  ALTER TABLE [dbo].[service_enum_values]
    ADD [pub_icon] NVARCHAR(64) NULL;
END
GO

-- =============================================================================
-- 2) Register pub_icon column in object-table metadata
-- =============================================================================
MERGE [dbo].[system_objects_database_columns] AS target
USING (
  SELECT
    CAST(N'02DADB4F-1BA4-50FC-B456-DAB0217115DA' AS UNIQUEIDENTIFIER) AS [key_guid],
    CAST(N'F4F4783A-4E31-5F42-AD6D-E8BB0E5D8BCF' AS UNIQUEIDENTIFIER) AS [ref_table_guid],
    CAST(N'0093B404-1EEE-563D-9135-4B9E7EECA7A2' AS UNIQUEIDENTIFIER) AS [ref_type_guid],
    N'pub_icon' AS [pub_name],
    8 AS [pub_ordinal],
    1 AS [pub_is_nullable],
    0 AS [pub_is_primary_key],
    0 AS [pub_is_identity],
    CAST(NULL AS NVARCHAR(512)) AS [pub_default],
    64 AS [pub_max_length]
) AS source
ON target.[key_guid] = source.[key_guid]
WHEN MATCHED THEN
  UPDATE SET
    [ref_table_guid] = source.[ref_table_guid],
    [ref_type_guid] = source.[ref_type_guid],
    [pub_name] = source.[pub_name],
    [pub_ordinal] = source.[pub_ordinal],
    [pub_is_nullable] = source.[pub_is_nullable],
    [pub_is_primary_key] = source.[pub_is_primary_key],
    [pub_is_identity] = source.[pub_is_identity],
    [pub_default] = source.[pub_default],
    [pub_max_length] = source.[pub_max_length]
WHEN NOT MATCHED THEN
  INSERT ([key_guid],[ref_table_guid],[ref_type_guid],[pub_name],[pub_ordinal],[pub_is_nullable],[pub_is_primary_key],[pub_is_identity],[pub_default],[pub_max_length])
  VALUES (source.[key_guid],source.[ref_table_guid],source.[ref_type_guid],source.[pub_name],source.[pub_ordinal],source.[pub_is_nullable],source.[pub_is_primary_key],source.[pub_is_identity],source.[pub_default],source.[pub_max_length]);
GO

-- =============================================================================
-- 3) Enum category + 14 top-level values
--
-- Categories from design doc (ObjectTree_CategoryDesign.md):
--   database        — Tables, Columns, Indexes, Constraints
--   types           — Scalar types + cross-language mappings
--   components      — Registered React components + type-control bindings
--   pages           — Page definitions, component trees, data bindings
--   routes          — URL routing with role-gating
--   modules         — Server modules + module methods
--   rpc_surface     — Domains, Subdomains, Functions, Models, Model Fields
--   security        — Roles, Entitlements, Users, Providers
--   gateways        — IoService gateways, identity strategies, method bindings
--   sessions        — Sessions, Tokens, Devices
--   agents          — MCP/API client registrations
--   enumerations    — Enum categories + values
--   queries         — Data-driven SQL bound to modules
--   configuration   — System config key-value pairs
-- =============================================================================
MERGE [dbo].[service_enum_categories] AS target
USING (
  SELECT
    CAST(N'9E735725-2EFF-5978-B92F-73A6CB36DF7F' AS UNIQUEIDENTIFIER) AS [key_guid],
    N'object_tree_categories' AS [pub_name],
    N'Object Tree Categories' AS [pub_display],
    N'Top-level category taxonomy for object tree navigation and table grouping' AS [pub_description]
) AS source
ON target.[key_guid] = source.[key_guid]
WHEN MATCHED THEN
  UPDATE SET
    [pub_name] = source.[pub_name],
    [pub_display] = source.[pub_display],
    [pub_description] = source.[pub_description]
WHEN NOT MATCHED THEN
  INSERT ([key_guid],[pub_name],[pub_display],[pub_description])
  VALUES (source.[key_guid],source.[pub_name],source.[pub_display],source.[pub_description]);
GO

-- Delete any previous values for this category (clean slate for corrected data)
DELETE FROM [dbo].[service_enum_values]
WHERE [ref_category_guid] = N'9E735725-2EFF-5978-B92F-73A6CB36DF7F';
GO

INSERT INTO [dbo].[service_enum_values]
  ([key_guid], [ref_category_guid], [pub_name], [pub_display], [pub_sequence], [pub_icon])
VALUES
  -- Definition domains
  (N'82FB7F4F-63A6-566F-A28A-60D12D7AF05B', N'9E735725-2EFF-5978-B92F-73A6CB36DF7F', N'database',       N'Database',       10,  N'Storage'),
  (N'EFAB32FE-8DF8-58FD-8C68-39D3B9E3BE00', N'9E735725-2EFF-5978-B92F-73A6CB36DF7F', N'types',          N'Types',          20,  N'DataObject'),
  (N'EC86C8B6-7094-5916-A2C5-87584021CED3', N'9E735725-2EFF-5978-B92F-73A6CB36DF7F', N'components',     N'Components',     30,  N'Widgets'),
  (N'19422ABD-0EF2-5EDB-8186-C6446FF2AC87', N'9E735725-2EFF-5978-B92F-73A6CB36DF7F', N'pages',          N'Pages',          40,  N'WebAsset'),
  (N'1722D841-3A33-5991-AE13-E22CB6C03737', N'9E735725-2EFF-5978-B92F-73A6CB36DF7F', N'routes',         N'Routes',         50,  N'Route'),

  -- Implementation domains
  (N'EAB35A4B-2A64-513E-8503-A6A3E68C55A1', N'9E735725-2EFF-5978-B92F-73A6CB36DF7F', N'modules',        N'Modules',        60,  N'Extension'),
  (N'A7C3D1E2-45F6-5B8A-9D2E-7F1A3C5E8B4D', N'9E735725-2EFF-5978-B92F-73A6CB36DF7F', N'rpc_surface',    N'RPC Surface',    70,  N'Api'),

  -- Security domains
  (N'B8D4E2F3-56A7-5C9B-AE3F-8A2B4D6F9C5E', N'9E735725-2EFF-5978-B92F-73A6CB36DF7F', N'security',       N'Security',       80,  N'Security'),
  (N'401EA20D-EB27-592D-B16C-4949547DDB6D', N'9E735725-2EFF-5978-B92F-73A6CB36DF7F', N'gateways',       N'Gateways',       90,  N'Hub'),
  (N'C9E5F3A4-67B8-5DAC-BF4A-9B3C5E7FA6DF', N'9E735725-2EFF-5978-B92F-73A6CB36DF7F', N'sessions',       N'Sessions',       100, N'VpnKey'),
  (N'DAF6A4B5-78C9-5EBD-CA5B-AC4D6F8AB7EA', N'9E735725-2EFF-5978-B92F-73A6CB36DF7F', N'agents',         N'Agents',         110, N'SmartToy'),

  -- System domains
  (N'0CC7D0FE-A02E-5D94-ABBD-D0DCC89CBDDC', N'9E735725-2EFF-5978-B92F-73A6CB36DF7F', N'enumerations',   N'Enumerations',   120, N'List'),
  (N'4790EB4B-5364-5A89-A0B3-CFDAA60F34C8', N'9E735725-2EFF-5978-B92F-73A6CB36DF7F', N'queries',        N'Queries',        130, N'Code'),
  (N'EBA7B5C6-89DA-5FCE-DB6C-BD5E7A9BC8FB', N'9E735725-2EFF-5978-B92F-73A6CB36DF7F', N'configuration',  N'Configuration',  140, N'Settings');
GO

-- =============================================================================
-- 4) Create system_objects_tree_category_tables
-- =============================================================================
IF OBJECT_ID(N'dbo.system_objects_tree_category_tables', N'U') IS NULL
BEGIN
  CREATE TABLE [dbo].[system_objects_tree_category_tables] (
    [key_guid]            UNIQUEIDENTIFIER  NOT NULL CONSTRAINT [DF_sotct_guid]        DEFAULT NEWID(),
    [ref_category_guid]   UNIQUEIDENTIFIER  NOT NULL,
    [ref_table_guid]      UNIQUEIDENTIFIER  NOT NULL,
    [pub_sequence]        INT               NOT NULL CONSTRAINT [DF_sotct_sequence]    DEFAULT 0,
    [pub_is_root_table]   BIT               NOT NULL CONSTRAINT [DF_sotct_is_root]     DEFAULT 0,
    [priv_created_on]     DATETIMEOFFSET(7) NOT NULL CONSTRAINT [DF_sotct_created_on]  DEFAULT SYSUTCDATETIME(),
    [priv_modified_on]    DATETIMEOFFSET(7) NOT NULL CONSTRAINT [DF_sotct_modified_on] DEFAULT SYSUTCDATETIME(),
    CONSTRAINT [PK_system_objects_tree_category_tables] PRIMARY KEY CLUSTERED ([key_guid]),
    CONSTRAINT [FK_sotct_category] FOREIGN KEY ([ref_category_guid]) REFERENCES [dbo].[service_enum_values] ([key_guid]),
    CONSTRAINT [FK_sotct_table]    FOREIGN KEY ([ref_table_guid])    REFERENCES [dbo].[system_objects_database_tables] ([key_guid]),
    CONSTRAINT [UQ_sotct_category_table] UNIQUE ([ref_category_guid], [ref_table_guid])
  );
END
GO

IF NOT EXISTS (
  SELECT 1 FROM sys.indexes
  WHERE [name] = N'IX_sotct_category' AND [object_id] = OBJECT_ID(N'dbo.system_objects_tree_category_tables')
)
BEGIN
  CREATE INDEX [IX_sotct_category] ON [dbo].[system_objects_tree_category_tables] ([ref_category_guid]);
END
GO

IF NOT EXISTS (
  SELECT 1 FROM sys.indexes
  WHERE [name] = N'IX_sotct_table' AND [object_id] = OBJECT_ID(N'dbo.system_objects_tree_category_tables')
)
BEGIN
  CREATE INDEX [IX_sotct_table] ON [dbo].[system_objects_tree_category_tables] ([ref_table_guid]);
END
GO

-- =============================================================================
-- 5) Self-register table metadata
-- =============================================================================

-- Table registration
MERGE [dbo].[system_objects_database_tables] AS target
USING (
  SELECT CAST(N'110D7461-11A2-542E-99CC-E41D20921721' AS UNIQUEIDENTIFIER) AS [key_guid],
         N'system_objects_tree_category_tables' AS [pub_name],
         N'dbo' AS [pub_schema]
) AS source
ON target.[key_guid] = source.[key_guid]
WHEN MATCHED THEN
  UPDATE SET [pub_name] = source.[pub_name], [pub_schema] = source.[pub_schema]
WHEN NOT MATCHED THEN
  INSERT ([key_guid],[pub_name],[pub_schema]) VALUES (source.[key_guid],source.[pub_name],source.[pub_schema]);
GO

-- Column registration
MERGE [dbo].[system_objects_database_columns] AS target
USING (
  SELECT CAST(N'D2BAE0CC-B502-597A-A4E1-E403EB99CEAC' AS UNIQUEIDENTIFIER) AS [key_guid], CAST(N'110D7461-11A2-542E-99CC-E41D20921721' AS UNIQUEIDENTIFIER) AS [ref_table_guid], CAST(N'4D2EB10B-363E-5AF4-826A-9294146244E4' AS UNIQUEIDENTIFIER) AS [ref_type_guid], N'key_guid' AS [pub_name], 1 AS [pub_ordinal], 0 AS [pub_is_nullable], 1 AS [pub_is_primary_key], 0 AS [pub_is_identity], CAST(N'NEWID()' AS NVARCHAR(512)) AS [pub_default], CAST(NULL AS INT) AS [pub_max_length]
  UNION ALL SELECT CAST(N'DB87DBFF-A88D-5ACB-8AB9-392CC89B2AC4' AS UNIQUEIDENTIFIER), CAST(N'110D7461-11A2-542E-99CC-E41D20921721' AS UNIQUEIDENTIFIER), CAST(N'4D2EB10B-363E-5AF4-826A-9294146244E4' AS UNIQUEIDENTIFIER), N'ref_category_guid', 2, 0, 0, 0, NULL, NULL
  UNION ALL SELECT CAST(N'48C3E5F2-17CD-5F88-BE04-09043EF3753D' AS UNIQUEIDENTIFIER), CAST(N'110D7461-11A2-542E-99CC-E41D20921721' AS UNIQUEIDENTIFIER), CAST(N'4D2EB10B-363E-5AF4-826A-9294146244E4' AS UNIQUEIDENTIFIER), N'ref_table_guid', 3, 0, 0, 0, NULL, NULL
  UNION ALL SELECT CAST(N'7ED8C744-E033-580F-AE54-A7BD7E984716' AS UNIQUEIDENTIFIER), CAST(N'110D7461-11A2-542E-99CC-E41D20921721' AS UNIQUEIDENTIFIER), CAST(N'E3EDE0CE-2A03-501E-A796-3487BEA03B7B' AS UNIQUEIDENTIFIER), N'pub_sequence', 4, 0, 0, 0, N'0', NULL
  UNION ALL SELECT CAST(N'488010C2-D7E9-54AE-A523-8234AAFE3559' AS UNIQUEIDENTIFIER), CAST(N'110D7461-11A2-542E-99CC-E41D20921721' AS UNIQUEIDENTIFIER), CAST(N'12B2F03B-E315-50A5-B631-E6B1EB961A17' AS UNIQUEIDENTIFIER), N'pub_is_root_table', 5, 0, 0, 0, N'0', NULL
  UNION ALL SELECT CAST(N'6BEED23E-F43E-5B9D-B980-0F5123C3A77D' AS UNIQUEIDENTIFIER), CAST(N'110D7461-11A2-542E-99CC-E41D20921721' AS UNIQUEIDENTIFIER), CAST(N'70F890D3-5AB5-5250-860E-4F7F9624190C' AS UNIQUEIDENTIFIER), N'priv_created_on', 6, 0, 0, 0, N'SYSUTCDATETIME()', NULL
  UNION ALL SELECT CAST(N'13ADF57F-910A-5516-B5F4-79837BAFE23E' AS UNIQUEIDENTIFIER), CAST(N'110D7461-11A2-542E-99CC-E41D20921721' AS UNIQUEIDENTIFIER), CAST(N'70F890D3-5AB5-5250-860E-4F7F9624190C' AS UNIQUEIDENTIFIER), N'priv_modified_on', 7, 0, 0, 0, N'SYSUTCDATETIME()', NULL
) AS source
ON target.[key_guid] = source.[key_guid]
WHEN MATCHED THEN
  UPDATE SET
    [ref_table_guid] = source.[ref_table_guid],
    [ref_type_guid] = source.[ref_type_guid],
    [pub_name] = source.[pub_name],
    [pub_ordinal] = source.[pub_ordinal],
    [pub_is_nullable] = source.[pub_is_nullable],
    [pub_is_primary_key] = source.[pub_is_primary_key],
    [pub_is_identity] = source.[pub_is_identity],
    [pub_default] = source.[pub_default],
    [pub_max_length] = source.[pub_max_length]
WHEN NOT MATCHED THEN
  INSERT ([key_guid],[ref_table_guid],[ref_type_guid],[pub_name],[pub_ordinal],[pub_is_nullable],[pub_is_primary_key],[pub_is_identity],[pub_default],[pub_max_length])
  VALUES (source.[key_guid],source.[ref_table_guid],source.[ref_type_guid],source.[pub_name],source.[pub_ordinal],source.[pub_is_nullable],source.[pub_is_primary_key],source.[pub_is_identity],source.[pub_default],source.[pub_max_length]);
GO

-- Index registration
MERGE [dbo].[system_objects_database_indexes] AS target
USING (
  SELECT CAST(N'110D7461-11A2-542E-99CC-E41D20921721' AS UNIQUEIDENTIFIER) AS [ref_table_guid], N'UQ_sotct_category_table' AS [pub_name], N'ref_category_guid,ref_table_guid' AS [pub_columns], 1 AS [pub_is_unique]
  UNION ALL SELECT CAST(N'110D7461-11A2-542E-99CC-E41D20921721' AS UNIQUEIDENTIFIER), N'IX_sotct_category', N'ref_category_guid', 0
  UNION ALL SELECT CAST(N'110D7461-11A2-542E-99CC-E41D20921721' AS UNIQUEIDENTIFIER), N'IX_sotct_table', N'ref_table_guid', 0
) AS source
ON target.[ref_table_guid] = source.[ref_table_guid] AND target.[pub_name] = source.[pub_name]
WHEN MATCHED THEN
  UPDATE SET [pub_columns] = source.[pub_columns], [pub_is_unique] = source.[pub_is_unique]
WHEN NOT MATCHED THEN
  INSERT ([ref_table_guid],[pub_name],[pub_columns],[pub_is_unique])
  VALUES (source.[ref_table_guid],source.[pub_name],source.[pub_columns],source.[pub_is_unique]);
GO

-- Constraint registration
MERGE [dbo].[system_objects_database_constraints] AS target
USING (
  SELECT CAST(N'110D7461-11A2-542E-99CC-E41D20921721' AS UNIQUEIDENTIFIER) AS [ref_table_guid], CAST(N'DB87DBFF-A88D-5ACB-8AB9-392CC89B2AC4' AS UNIQUEIDENTIFIER) AS [ref_column_guid], CAST(N'F4F4783A-4E31-5F42-AD6D-E8BB0E5D8BCF' AS UNIQUEIDENTIFIER) AS [ref_referenced_table_guid], CAST(N'3CF8E90D-C44F-538F-A092-4D596A4CDFB2' AS UNIQUEIDENTIFIER) AS [ref_referenced_column_guid]
  UNION ALL SELECT CAST(N'110D7461-11A2-542E-99CC-E41D20921721' AS UNIQUEIDENTIFIER), CAST(N'48C3E5F2-17CD-5F88-BE04-09043EF3753D' AS UNIQUEIDENTIFIER), CAST(N'78D4E217-6810-5A05-8999-ED57016229B6' AS UNIQUEIDENTIFIER), CAST(N'01ED6065-9D06-569A-9138-557E549B3B13' AS UNIQUEIDENTIFIER)
) AS source
ON target.[ref_table_guid] = source.[ref_table_guid]
   AND target.[ref_column_guid] = source.[ref_column_guid]
WHEN MATCHED THEN
  UPDATE SET
    [ref_referenced_table_guid] = source.[ref_referenced_table_guid],
    [ref_referenced_column_guid] = source.[ref_referenced_column_guid]
WHEN NOT MATCHED THEN
  INSERT ([ref_table_guid],[ref_column_guid],[ref_referenced_table_guid],[ref_referenced_column_guid])
  VALUES (source.[ref_table_guid],source.[ref_column_guid],source.[ref_referenced_table_guid],source.[ref_referenced_column_guid]);
GO

-- =============================================================================
-- 6) Seed category → table mappings
--
-- Each category maps to one or more backing tables.
-- pub_is_root_table=1 marks the primary entry point table for the category.
-- Additional tables (root=0) are child/related tables in that domain.
--
-- NOTE: Only tables already registered in system_objects_database_tables
-- can be referenced here. The CTE resolves names to GUIDs via JOIN.
-- Categories whose backing tables are not yet registered will silently
-- produce zero rows — this is correct and they can be seeded later.
-- =============================================================================

-- Clear previous mappings for clean re-seed
DELETE FROM [dbo].[system_objects_tree_category_tables];
GO

;WITH mapping_seed AS (
  -- Database: tables → columns → indexes → constraints
  SELECT N'database' AS category_name, N'system_objects_database_tables' AS table_name, 1 AS pub_sequence, CAST(1 AS BIT) AS pub_is_root_table
  UNION ALL SELECT N'database', N'system_objects_database_columns',     2, 0
  UNION ALL SELECT N'database', N'system_objects_database_indexes',     3, 0
  UNION ALL SELECT N'database', N'system_objects_database_constraints', 4, 0

  -- Types: type definitions + type-to-control bindings
  UNION ALL SELECT N'types', N'system_objects_types',          1, 1
  UNION ALL SELECT N'types', N'system_objects_type_controls',  2, 0

  -- Components: component registry + component tree instances
  UNION ALL SELECT N'components', N'system_objects_components',     1, 1
  UNION ALL SELECT N'components', N'system_objects_component_tree', 2, 0

  -- Pages: page definitions + data bindings
  UNION ALL SELECT N'pages', N'system_objects_pages',              1, 1
  UNION ALL SELECT N'pages', N'system_objects_page_data_bindings', 2, 0

  -- Routes
  UNION ALL SELECT N'routes', N'system_objects_routes', 1, 1

  -- Modules: module registry + module methods
  UNION ALL SELECT N'modules', N'system_objects_modules',        1, 1
  UNION ALL SELECT N'modules', N'system_objects_module_methods', 2, 0

  -- RPC Surface: domains → subdomains → functions + models → fields
  UNION ALL SELECT N'rpc_surface', N'system_objects_rpc_domains',      1, 1
  UNION ALL SELECT N'rpc_surface', N'system_objects_rpc_subdomains',   2, 0
  UNION ALL SELECT N'rpc_surface', N'system_objects_rpc_functions',    3, 0
  UNION ALL SELECT N'rpc_surface', N'system_objects_rpc_models',       4, 0
  UNION ALL SELECT N'rpc_surface', N'system_objects_rpc_model_fields', 5, 0

  -- Security: roles, entitlements, users, providers
  -- (these tables may not all be registered in system_objects_database_tables yet)
  UNION ALL SELECT N'security', N'system_auth_roles',        1, 1
  UNION ALL SELECT N'security', N'system_auth_entitlements', 2, 0
  UNION ALL SELECT N'security', N'system_users',             3, 0

  -- Gateways: io gateways + identity providers + method bindings
  UNION ALL SELECT N'gateways', N'system_objects_io_gateways',                  1, 1
  UNION ALL SELECT N'gateways', N'system_objects_gateway_identity_providers',   2, 0
  UNION ALL SELECT N'gateways', N'system_objects_gateway_method_bindings',      3, 0

  -- Sessions: sessions + tokens + devices
  UNION ALL SELECT N'sessions', N'system_sessions',         1, 1
  UNION ALL SELECT N'sessions', N'system_session_tokens',   2, 0
  UNION ALL SELECT N'sessions', N'system_session_devices',  3, 0

  -- Agents: agent clients + user links + auth codes
  UNION ALL SELECT N'agents', N'service_agent_clients',      1, 1
  UNION ALL SELECT N'agents', N'service_agent_client_users', 2, 0
  UNION ALL SELECT N'agents', N'service_agent_auth_codes',   3, 0

  -- Enumerations: categories + values
  UNION ALL SELECT N'enumerations', N'service_enum_categories', 1, 1
  UNION ALL SELECT N'enumerations', N'service_enum_values',     2, 0

  -- Queries
  UNION ALL SELECT N'queries', N'system_objects_queries', 1, 1

  -- Configuration
  UNION ALL SELECT N'configuration', N'system_config', 1, 1

  -- Self-reference: the tree category table itself belongs to Database
  UNION ALL SELECT N'database', N'system_objects_tree_category_tables', 5, 0
), resolved_seed AS (
  SELECT
    c.[key_guid] AS [ref_category_guid],
    t.[key_guid] AS [ref_table_guid],
    m.[pub_sequence],
    m.[pub_is_root_table]
  FROM mapping_seed m
  INNER JOIN [dbo].[service_enum_values] c
    ON c.[pub_name] = m.[category_name]
   AND c.[ref_category_guid] = N'9E735725-2EFF-5978-B92F-73A6CB36DF7F'
  INNER JOIN [dbo].[system_objects_database_tables] t
    ON t.[pub_name] = m.[table_name]
   AND t.[pub_schema] = N'dbo'
)
INSERT INTO [dbo].[system_objects_tree_category_tables]
  ([key_guid], [ref_category_guid], [ref_table_guid], [pub_sequence], [pub_is_root_table])
SELECT
  NEWID(),
  [ref_category_guid],
  [ref_table_guid],
  [pub_sequence],
  [pub_is_root_table]
FROM resolved_seed;
GO

-- =============================================================================
-- 7) Verification
-- =============================================================================

-- All 14 categories with icons
SELECT [pub_name], [pub_display], [pub_sequence], [pub_icon]
FROM [dbo].[service_enum_values]
WHERE [ref_category_guid] = N'9E735725-2EFF-5978-B92F-73A6CB36DF7F'
ORDER BY [pub_sequence];
GO

-- Category → table mappings (shows which categories resolved vs which had missing tables)
SELECT
  c.[pub_display] AS [category],
  t.[pub_name] AS [table_name],
  m.[pub_sequence] AS [seq],
  CASE WHEN m.[pub_is_root_table] = 1 THEN 'ROOT' ELSE '' END AS [root]
FROM [dbo].[system_objects_tree_category_tables] m
JOIN [dbo].[service_enum_values] c ON c.[key_guid] = m.[ref_category_guid]
JOIN [dbo].[system_objects_database_tables] t ON t.[key_guid] = m.[ref_table_guid]
ORDER BY c.[pub_sequence], m.[pub_sequence];
GO

-- Categories with zero table mappings (tables not yet registered)
SELECT c.[pub_display] AS [category_without_tables]
FROM [dbo].[service_enum_values] c
WHERE c.[ref_category_guid] = N'9E735725-2EFF-5978-B92F-73A6CB36DF7F'
  AND NOT EXISTS (
    SELECT 1 FROM [dbo].[system_objects_tree_category_tables] m
    WHERE m.[ref_category_guid] = c.[key_guid]
  )
ORDER BY c.[pub_sequence];
GO
