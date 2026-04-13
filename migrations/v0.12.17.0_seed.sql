-- ============================================================================
-- Object Tree Contract Nodes Migration
-- v0.12.6.0 — Contract Nodes Reorganization
-- 
-- Task 1: Remove Sessions node from Object Tree
-- Task 2: Create RPC Contracts category (split from RPC Surface)
-- Task 3: Create Database Contracts category + DDL tables
-- Task 4: Create App Contracts category + DDL table
--
-- Execute in SSMS against target database.
-- All GUIDs are inline — no DECLARE variables across GO boundaries.
-- ============================================================================


-- ============================================================================
-- TASK 1: Remove Sessions node
-- Delete the enum value and its 3 tree_category_tables mappings.
-- The session tables remain — they just leave the Object Tree.
-- ============================================================================

-- Remove tree_category_tables for Sessions category
DELETE FROM [dbo].[system_objects_tree_category_tables]
WHERE [ref_category_guid] = N'C9E5F3A4-67B8-5DAC-BF4A-9B3C5E7FA6DF';

-- Remove the Sessions enum value from object_tree_categories
DELETE FROM [dbo].[service_enum_values]
WHERE [key_guid] = N'C9E5F3A4-67B8-5DAC-BF4A-9B3C5E7FA6DF';

PRINT 'Task 1 complete: Sessions node removed from Object Tree.';
GO


-- ============================================================================
-- TASK 2: Create RPC Contracts category
-- Pull rpc_models and rpc_model_fields out of RPC Surface into their own node.
-- ============================================================================

-- Insert new enum value: RPC Contracts at sequence 75
INSERT INTO [dbo].[service_enum_values]
  ([key_guid], [ref_category_guid], [pub_name], [pub_display], [pub_sequence], [pub_icon])
VALUES
  (N'F4A8C2D1-93E7-5BAF-CB6D-AE5F7B8DC9E3',   -- new deterministic GUID
   N'9E735725-2EFF-5978-B92F-73A6CB36DF7F',     -- object_tree_categories enum
   N'rpc_contracts',
   N'RPC Contracts',
   75,
   N'Schema');

-- Move rpc_models from RPC Surface to RPC Contracts
UPDATE [dbo].[system_objects_tree_category_tables]
SET [ref_category_guid] = N'F4A8C2D1-93E7-5BAF-CB6D-AE5F7B8DC9E3',
    [pub_sequence] = 1,
    [pub_is_root_table] = 1,
    [priv_modified_on] = SYSUTCDATETIME()
WHERE [ref_category_guid] = N'A7C3D1E2-45F6-5B8A-9D2E-7F1A3C5E8B4D'
  AND [ref_table_guid] = N'1F64750F-DCE9-5AC1-93FE-362AF3A96B94';   -- system_objects_rpc_models

-- Move rpc_model_fields from RPC Surface to RPC Contracts
UPDATE [dbo].[system_objects_tree_category_tables]
SET [ref_category_guid] = N'F4A8C2D1-93E7-5BAF-CB6D-AE5F7B8DC9E3',
    [pub_sequence] = 2,
    [pub_is_root_table] = 0,
    [priv_modified_on] = SYSUTCDATETIME()
WHERE [ref_category_guid] = N'A7C3D1E2-45F6-5B8A-9D2E-7F1A3C5E8B4D'
  AND [ref_table_guid] = N'435807CF-4798-560C-BA94-64DB94B8F259';   -- system_objects_rpc_model_fields

PRINT 'Task 2 complete: RPC Contracts category created, models/fields moved from RPC Surface.';
GO


-- ============================================================================
-- TASK 3: Create Database Contracts category + DDL tables
-- New tables: system_objects_database_views, system_objects_database_view_columns
-- ============================================================================

-- 3a. Create system_objects_database_views table
IF NOT EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'system_objects_database_views')
BEGIN
  CREATE TABLE [dbo].[system_objects_database_views] (
    [key_guid]          UNIQUEIDENTIFIER  NOT NULL,
    [pub_name]          NVARCHAR(128)     NOT NULL,
    [pub_schema]        NVARCHAR(64)      NOT NULL  CONSTRAINT [DF_sodb_views_schema] DEFAULT N'dbo',
    [pub_description]   NVARCHAR(512)     NULL,
    [pub_is_active]     BIT               NOT NULL  CONSTRAINT [DF_sodb_views_active] DEFAULT 1,
    [priv_created_on]   DATETIMEOFFSET(7) NOT NULL  CONSTRAINT [DF_sodb_views_created] DEFAULT SYSUTCDATETIME(),
    [priv_modified_on]  DATETIMEOFFSET(7) NOT NULL  CONSTRAINT [DF_sodb_views_modified] DEFAULT SYSUTCDATETIME(),
    CONSTRAINT [PK_system_objects_database_views] PRIMARY KEY CLUSTERED ([key_guid]),
    CONSTRAINT [UQ_system_objects_database_views_schema_name] UNIQUE ([pub_schema], [pub_name])
  );
  PRINT 'Created table: system_objects_database_views';
END;
GO

-- 3b. Create system_objects_database_view_columns table
IF NOT EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'system_objects_database_view_columns')
BEGIN
  CREATE TABLE [dbo].[system_objects_database_view_columns] (
    [key_guid]          UNIQUEIDENTIFIER  NOT NULL,
    [ref_view_guid]     UNIQUEIDENTIFIER  NOT NULL,
    [pub_name]          NVARCHAR(128)     NOT NULL,
    [pub_ordinal]       INT               NOT NULL  CONSTRAINT [DF_sodb_vcols_ordinal] DEFAULT 0,
    [ref_type_guid]     UNIQUEIDENTIFIER  NULL,
    [pub_is_nullable]   BIT               NOT NULL  CONSTRAINT [DF_sodb_vcols_nullable] DEFAULT 0,
    [pub_description]   NVARCHAR(512)     NULL,
    [priv_created_on]   DATETIMEOFFSET(7) NOT NULL  CONSTRAINT [DF_sodb_vcols_created] DEFAULT SYSUTCDATETIME(),
    [priv_modified_on]  DATETIMEOFFSET(7) NOT NULL  CONSTRAINT [DF_sodb_vcols_modified] DEFAULT SYSUTCDATETIME(),
    CONSTRAINT [PK_system_objects_database_view_columns] PRIMARY KEY CLUSTERED ([key_guid]),
    CONSTRAINT [FK_sodb_vcols_view] FOREIGN KEY ([ref_view_guid])
      REFERENCES [dbo].[system_objects_database_views] ([key_guid]),
    CONSTRAINT [FK_sodb_vcols_type] FOREIGN KEY ([ref_type_guid])
      REFERENCES [dbo].[system_objects_types] ([key_guid])
  );
  PRINT 'Created table: system_objects_database_view_columns';
END;
GO

-- 3c. Register the new tables in the database reflection registry
MERGE [dbo].[system_objects_database_tables] AS target
USING (VALUES
  (N'A1B2C3D4-E5F6-5A7B-8C9D-0E1F2A3B4C5D', N'system_objects_database_views', N'dbo'),
  (N'B2C3D4E5-F6A7-5B8C-9D0E-1F2A3B4C5D6E', N'system_objects_database_view_columns', N'dbo')
) AS src ([key_guid], [pub_name], [pub_schema])
ON target.[key_guid] = src.[key_guid]
WHEN NOT MATCHED THEN
  INSERT ([key_guid], [pub_name], [pub_schema])
  VALUES (src.[key_guid], src.[pub_name], src.[pub_schema]);

-- 3d. Insert enum value: Database Contracts at sequence 15
INSERT INTO [dbo].[service_enum_values]
  ([key_guid], [ref_category_guid], [pub_name], [pub_display], [pub_sequence], [pub_icon])
VALUES
  (N'D3E4F5A6-B7C8-5D9E-AF0B-1C2D3E4F5A6B',   -- new deterministic GUID
   N'9E735725-2EFF-5978-B92F-73A6CB36DF7F',     -- object_tree_categories enum
   N'database_contracts',
   N'Database Contracts',
   15,
   N'ViewColumn');

-- 3e. Map tables to Database Contracts category
INSERT INTO [dbo].[system_objects_tree_category_tables]
  ([key_guid], [ref_category_guid], [ref_table_guid], [pub_sequence], [pub_is_root_table])
VALUES
  -- system_objects_database_views (root)
  (NEWID(),
   N'D3E4F5A6-B7C8-5D9E-AF0B-1C2D3E4F5A6B',
   N'A1B2C3D4-E5F6-5A7B-8C9D-0E1F2A3B4C5D',
   1, 1),
  -- system_objects_database_view_columns (child)
  (NEWID(),
   N'D3E4F5A6-B7C8-5D9E-AF0B-1C2D3E4F5A6B',
   N'B2C3D4E5-F6A7-5B8C-9D0E-1F2A3B4C5D6E',
   2, 0);

PRINT 'Task 3 complete: Database Contracts category + tables created.';
GO


-- ============================================================================
-- TASK 4: Create App Contracts category + DDL table
-- New table: system_objects_module_contracts
-- This is the function signature registry — IDE-style class API management.
-- Separate from RPC contracts; defines what modules accept and return internally.
-- ============================================================================

-- 4a. Create system_objects_module_contracts table
-- Each row defines the typed signature of a module method.
-- ref_module_guid + ref_method_guid locate the function.
-- ref_request_model_guid and ref_response_model_guid point to typed shapes
-- that describe what goes in and what comes out at the module boundary.
IF NOT EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'system_objects_module_contracts')
BEGIN
  CREATE TABLE [dbo].[system_objects_module_contracts] (
    [key_guid]                UNIQUEIDENTIFIER  NOT NULL,
    [ref_module_guid]         UNIQUEIDENTIFIER  NOT NULL,
    [ref_method_guid]         UNIQUEIDENTIFIER  NOT NULL,
    [pub_name]                NVARCHAR(128)     NOT NULL,
    [pub_description]         NVARCHAR(512)     NULL,
    [pub_version]             INT               NOT NULL  CONSTRAINT [DF_somc_version] DEFAULT 1,
    [ref_request_model_guid]  UNIQUEIDENTIFIER  NULL,
    [ref_response_model_guid] UNIQUEIDENTIFIER  NULL,
    [pub_is_async]            BIT               NOT NULL  CONSTRAINT [DF_somc_async] DEFAULT 1,
    [pub_is_internal_only]    BIT               NOT NULL  CONSTRAINT [DF_somc_internal] DEFAULT 0,
    [pub_is_active]           BIT               NOT NULL  CONSTRAINT [DF_somc_active] DEFAULT 1,
    [priv_created_on]         DATETIMEOFFSET(7) NOT NULL  CONSTRAINT [DF_somc_created] DEFAULT SYSUTCDATETIME(),
    [priv_modified_on]        DATETIMEOFFSET(7) NOT NULL  CONSTRAINT [DF_somc_modified] DEFAULT SYSUTCDATETIME(),
    CONSTRAINT [PK_system_objects_module_contracts] PRIMARY KEY CLUSTERED ([key_guid]),
    CONSTRAINT [FK_somc_module] FOREIGN KEY ([ref_module_guid])
      REFERENCES [dbo].[system_objects_modules] ([key_guid]),
    CONSTRAINT [FK_somc_method] FOREIGN KEY ([ref_method_guid])
      REFERENCES [dbo].[system_objects_module_methods] ([key_guid]),
    CONSTRAINT [FK_somc_request_model] FOREIGN KEY ([ref_request_model_guid])
      REFERENCES [dbo].[system_objects_rpc_models] ([key_guid]),
    CONSTRAINT [FK_somc_response_model] FOREIGN KEY ([ref_response_model_guid])
      REFERENCES [dbo].[system_objects_rpc_models] ([key_guid]),
    CONSTRAINT [UQ_somc_method_version] UNIQUE ([ref_method_guid], [pub_version])
  );
  PRINT 'Created table: system_objects_module_contracts';
END;
GO

-- 4b. Register the new table in the database reflection registry
MERGE [dbo].[system_objects_database_tables] AS target
USING (VALUES
  (N'C3D4E5F6-A7B8-5C9D-0E1F-2A3B4C5D6E7F', N'system_objects_module_contracts', N'dbo')
) AS src ([key_guid], [pub_name], [pub_schema])
ON target.[key_guid] = src.[key_guid]
WHEN NOT MATCHED THEN
  INSERT ([key_guid], [pub_name], [pub_schema])
  VALUES (src.[key_guid], src.[pub_name], src.[pub_schema]);

-- 4c. Insert enum value: App Contracts at sequence 65
INSERT INTO [dbo].[service_enum_values]
  ([key_guid], [ref_category_guid], [pub_name], [pub_display], [pub_sequence], [pub_icon])
VALUES
  (N'E5F6A7B8-C9D0-5E1F-BA2C-3D4E5F6A7B8C',   -- new deterministic GUID
   N'9E735725-2EFF-5978-B92F-73A6CB36DF7F',     -- object_tree_categories enum
   N'app_contracts',
   N'App Contracts',
   65,
   N'Description');

-- 4d. Map tables to App Contracts category
-- Root: system_objects_module_contracts (the signature registry)
-- Child 1: system_objects_modules (context — which module owns the method)
-- Child 2: system_objects_module_methods (context — which method is being contracted)
INSERT INTO [dbo].[system_objects_tree_category_tables]
  ([key_guid], [ref_category_guid], [ref_table_guid], [pub_sequence], [pub_is_root_table])
VALUES
  -- system_objects_module_contracts (root)
  (NEWID(),
   N'E5F6A7B8-C9D0-5E1F-BA2C-3D4E5F6A7B8C',
   N'C3D4E5F6-A7B8-5C9D-0E1F-2A3B4C5D6E7F',
   1, 1),
  -- system_objects_modules (child — module context)
  (NEWID(),
   N'E5F6A7B8-C9D0-5E1F-BA2C-3D4E5F6A7B8C',
   N'D039D8FB-3F95-5A66-B7FB-AB4BA1301FEA',
   2, 0),
  -- system_objects_module_methods (child — method context)
  (NEWID(),
   N'E5F6A7B8-C9D0-5E1F-BA2C-3D4E5F6A7B8C',
   N'65E5E8F3-7EFF-57F7-B4F9-087C191B7B5E',
   3, 0);

PRINT 'Task 4 complete: App Contracts category + table created.';
GO


-- ============================================================================
-- VERIFICATION: Dump final state
-- ============================================================================

PRINT '--- Object Tree Categories (final) ---';
SELECT pub_name, pub_display, pub_sequence, pub_icon
FROM [dbo].[service_enum_values]
WHERE [ref_category_guid] = N'9E735725-2EFF-5978-B92F-73A6CB36DF7F'
ORDER BY pub_sequence;

PRINT '--- RPC Surface table mappings (should be 3: domains, subdomains, functions) ---';
SELECT t.pub_name, m.pub_sequence, m.pub_is_root_table
FROM [dbo].[system_objects_tree_category_tables] m
JOIN [dbo].[system_objects_database_tables] t ON m.ref_table_guid = t.key_guid
WHERE m.ref_category_guid = N'A7C3D1E2-45F6-5B8A-9D2E-7F1A3C5E8B4D'
ORDER BY m.pub_sequence;

PRINT '--- RPC Contracts table mappings (should be 2: models, model_fields) ---';
SELECT t.pub_name, m.pub_sequence, m.pub_is_root_table
FROM [dbo].[system_objects_tree_category_tables] m
JOIN [dbo].[system_objects_database_tables] t ON m.ref_table_guid = t.key_guid
WHERE m.ref_category_guid = N'F4A8C2D1-93E7-5BAF-CB6D-AE5F7B8DC9E3'
ORDER BY m.pub_sequence;

PRINT '--- Database Contracts table mappings (should be 2: views, view_columns) ---';
SELECT t.pub_name, m.pub_sequence, m.pub_is_root_table
FROM [dbo].[system_objects_tree_category_tables] m
JOIN [dbo].[system_objects_database_tables] t ON m.ref_table_guid = t.key_guid
WHERE m.ref_category_guid = N'D3E4F5A6-B7C8-5D9E-AF0B-1C2D3E4F5A6B'
ORDER BY m.pub_sequence;

PRINT '--- App Contracts table mappings (should be 3: contracts, modules, methods) ---';
SELECT t.pub_name, m.pub_sequence, m.pub_is_root_table
FROM [dbo].[system_objects_tree_category_tables] m
JOIN [dbo].[system_objects_database_tables] t ON m.ref_table_guid = t.key_guid
WHERE m.ref_category_guid = N'E5F6A7B8-C9D0-5E1F-BA2C-3D4E5F6A7B8C'
ORDER BY m.pub_sequence;
GO