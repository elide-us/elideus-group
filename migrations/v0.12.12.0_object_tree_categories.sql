-- =============================================================================
-- v0.12.12.0_object_tree_categories
-- Date: 2026-04-12
-- Purpose:
--   1) Add object_tree_categories enum category + 14 seeded values (with icons)
--   2) Extend service_enum_values with pub_icon metadata
--   3) Create system_objects_tree_category_tables and self-register metadata
--   4) Seed category -> backing table mappings with root table markers
-- =============================================================================

-- =============================================================================
-- 1) service_enum_values: pub_icon
-- =============================================================================
IF COL_LENGTH(N'dbo.service_enum_values', N'pub_icon') IS NULL
BEGIN
  ALTER TABLE [dbo].[service_enum_values]
    ADD [pub_icon] NVARCHAR(64) NULL;
END
GO

-- Register pub_icon in object-table metadata
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
-- 2) Enum category + values seed (idempotent)
-- =============================================================================
MERGE [dbo].[service_enum_categories] AS target
USING (
  SELECT
    CAST(N'9E735725-2EFF-5978-B92F-73A6CB36DF7F' AS UNIQUEIDENTIFIER) AS [key_guid],
    N'object_tree_categories' AS [pub_name],
    N'Object Tree Categories' AS [pub_display],
    N'Category taxonomy for object-tree table grouping and root-table entry points' AS [pub_description]
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

MERGE [dbo].[service_enum_values] AS target
USING (
  SELECT CAST(N'82FB7F4F-63A6-566F-A28A-60D12D7AF05B' AS UNIQUEIDENTIFIER) AS [key_guid], CAST(N'9E735725-2EFF-5978-B92F-73A6CB36DF7F' AS UNIQUEIDENTIFIER) AS [ref_category_guid], N'database' AS [pub_name], N'Database Tables' AS [pub_display], 10 AS [pub_sequence], N'Database' AS [pub_icon]
  UNION ALL SELECT CAST(N'EFAB32FE-8DF8-58FD-8C68-39D3B9E3BE00' AS UNIQUEIDENTIFIER), CAST(N'9E735725-2EFF-5978-B92F-73A6CB36DF7F' AS UNIQUEIDENTIFIER), N'types', N'Types', 20, N'BadgeInfo'
  UNION ALL SELECT CAST(N'EAB35A4B-2A64-513E-8503-A6A3E68C55A1' AS UNIQUEIDENTIFIER), CAST(N'9E735725-2EFF-5978-B92F-73A6CB36DF7F' AS UNIQUEIDENTIFIER), N'modules', N'Modules', 30, N'Package'
  UNION ALL SELECT CAST(N'00CB3A53-4A72-58AE-A325-D11D59742123' AS UNIQUEIDENTIFIER), CAST(N'9E735725-2EFF-5978-B92F-73A6CB36DF7F' AS UNIQUEIDENTIFIER), N'module_methods', N'Module Methods', 40, N'FunctionSquare'
  UNION ALL SELECT CAST(N'EC86C8B6-7094-5916-A2C5-87584021CED3' AS UNIQUEIDENTIFIER), CAST(N'9E735725-2EFF-5978-B92F-73A6CB36DF7F' AS UNIQUEIDENTIFIER), N'components', N'Components', 50, N'Blocks'
  UNION ALL SELECT CAST(N'768BB84C-EDA5-5893-97C3-9E402773897F' AS UNIQUEIDENTIFIER), CAST(N'9E735725-2EFF-5978-B92F-73A6CB36DF7F' AS UNIQUEIDENTIFIER), N'component_tree', N'Component Tree', 60, N'GitBranch'
  UNION ALL SELECT CAST(N'1722D841-3A33-5991-AE13-E22CB6C03737' AS UNIQUEIDENTIFIER), CAST(N'9E735725-2EFF-5978-B92F-73A6CB36DF7F' AS UNIQUEIDENTIFIER), N'routes', N'Routes', 70, N'Route'
  UNION ALL SELECT CAST(N'807995E6-D7CB-525A-8C6F-F524759C142F' AS UNIQUEIDENTIFIER), CAST(N'9E735725-2EFF-5978-B92F-73A6CB36DF7F' AS UNIQUEIDENTIFIER), N'type_controls', N'Type Controls', 80, N'SlidersHorizontal'
  UNION ALL SELECT CAST(N'19422ABD-0EF2-5EDB-8186-C6446FF2AC87' AS UNIQUEIDENTIFIER), CAST(N'9E735725-2EFF-5978-B92F-73A6CB36DF7F' AS UNIQUEIDENTIFIER), N'pages', N'Pages', 90, N'FileText'
  UNION ALL SELECT CAST(N'4790EB4B-5364-5A89-A0B3-CFDAA60F34C8' AS UNIQUEIDENTIFIER), CAST(N'9E735725-2EFF-5978-B92F-73A6CB36DF7F' AS UNIQUEIDENTIFIER), N'queries', N'Queries', 100, N'SearchCode'
  UNION ALL SELECT CAST(N'401EA20D-EB27-592D-B16C-4949547DDB6D' AS UNIQUEIDENTIFIER), CAST(N'9E735725-2EFF-5978-B92F-73A6CB36DF7F' AS UNIQUEIDENTIFIER), N'io_gateways', N'IO Gateways', 110, N'Plug'
  UNION ALL SELECT CAST(N'26A9F577-4721-53D2-826B-04BCBDBF0ED2' AS UNIQUEIDENTIFIER), CAST(N'9E735725-2EFF-5978-B92F-73A6CB36DF7F' AS UNIQUEIDENTIFIER), N'gateway_identity_providers', N'Gateway Identity Providers', 120, N'ShieldCheck'
  UNION ALL SELECT CAST(N'D137AB9D-704C-543E-AF27-669675537304' AS UNIQUEIDENTIFIER), CAST(N'9E735725-2EFF-5978-B92F-73A6CB36DF7F' AS UNIQUEIDENTIFIER), N'gateway_method_bindings', N'Gateway Method Bindings', 130, N'Workflow'
  UNION ALL SELECT CAST(N'0CC7D0FE-A02E-5D94-ABBD-D0DCC89CBDDC' AS UNIQUEIDENTIFIER), CAST(N'9E735725-2EFF-5978-B92F-73A6CB36DF7F' AS UNIQUEIDENTIFIER), N'enum_catalog', N'Enum Catalog', 140, N'ListChecks'
) AS source
ON target.[key_guid] = source.[key_guid]
WHEN MATCHED THEN
  UPDATE SET
    [ref_category_guid] = source.[ref_category_guid],
    [pub_name] = source.[pub_name],
    [pub_display] = source.[pub_display],
    [pub_sequence] = source.[pub_sequence],
    [pub_icon] = source.[pub_icon]
WHEN NOT MATCHED THEN
  INSERT ([key_guid],[ref_category_guid],[pub_name],[pub_display],[pub_sequence],[pub_icon])
  VALUES (source.[key_guid],source.[ref_category_guid],source.[pub_name],source.[pub_display],source.[pub_sequence],source.[pub_icon]);
GO

-- =============================================================================
-- 3) Create system_objects_tree_category_tables
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
-- 4) Self-register table metadata
-- =============================================================================
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
-- 5) Seed category -> table mappings
-- =============================================================================
;WITH mapping_seed AS (
  SELECT N'database' AS category_name, N'system_objects_database_tables' AS table_name, 10 AS pub_sequence, CAST(1 AS BIT) AS pub_is_root_table
  UNION ALL SELECT N'types', N'system_objects_types', 20, 1
  UNION ALL SELECT N'modules', N'system_objects_modules', 30, 1
  UNION ALL SELECT N'module_methods', N'system_objects_module_methods', 40, 1
  UNION ALL SELECT N'components', N'system_objects_components', 50, 1
  UNION ALL SELECT N'component_tree', N'system_objects_component_tree', 60, 1
  UNION ALL SELECT N'routes', N'system_objects_routes', 70, 1
  UNION ALL SELECT N'type_controls', N'system_objects_type_controls', 80, 1
  UNION ALL SELECT N'pages', N'system_objects_pages', 90, 1
  UNION ALL SELECT N'queries', N'system_objects_queries', 100, 1
  UNION ALL SELECT N'io_gateways', N'system_objects_io_gateways', 110, 1
  UNION ALL SELECT N'gateway_identity_providers', N'system_objects_gateway_identity_providers', 120, 1
  UNION ALL SELECT N'gateway_method_bindings', N'system_objects_gateway_method_bindings', 130, 1
  UNION ALL SELECT N'enum_catalog', N'service_enum_categories', 140, 1
  UNION ALL SELECT N'enum_catalog', N'service_enum_values', 141, 0
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
MERGE [dbo].[system_objects_tree_category_tables] AS target
USING resolved_seed AS source
ON target.[ref_category_guid] = source.[ref_category_guid]
AND target.[ref_table_guid] = source.[ref_table_guid]
WHEN MATCHED THEN
  UPDATE SET
    [pub_sequence] = source.[pub_sequence],
    [pub_is_root_table] = source.[pub_is_root_table],
    [priv_modified_on] = SYSUTCDATETIME()
WHEN NOT MATCHED THEN
  INSERT ([key_guid],[ref_category_guid],[ref_table_guid],[pub_sequence],[pub_is_root_table])
  VALUES (NEWID(),source.[ref_category_guid],source.[ref_table_guid],source.[pub_sequence],source.[pub_is_root_table]);
GO

-- =============================================================================
-- 6) Verification queries
-- =============================================================================
SELECT [pub_name], [pub_display], [pub_sequence], [pub_icon]
FROM [dbo].[service_enum_values]
WHERE [ref_category_guid] = N'9E735725-2EFF-5978-B92F-73A6CB36DF7F'
ORDER BY [pub_sequence];
GO

SELECT c.[pub_name] AS [category_name], t.[pub_name] AS [table_name], m.[pub_sequence], m.[pub_is_root_table]
FROM [dbo].[system_objects_tree_category_tables] m
JOIN [dbo].[service_enum_values] c ON c.[key_guid] = m.[ref_category_guid]
JOIN [dbo].[system_objects_database_tables] t ON t.[key_guid] = m.[ref_table_guid]
WHERE c.[ref_category_guid] = N'9E735725-2EFF-5978-B92F-73A6CB36DF7F'
ORDER BY c.[pub_sequence], m.[pub_sequence];
GO
