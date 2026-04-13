-- ============================================================================
-- v0.12.18.0 — Object Tree Categories: Promote from Enums to Dedicated Tables
--
-- Creates:
--   system_objects_tree_categories     — top-level object tree categories
--   system_objects_tree_subcategories  — future subcategory support
--
-- Migrates 16 object tree category rows from service_enum_values into the
-- new table, retargets the FK on system_objects_tree_category_tables, updates
-- the get_categories query, and removes the migrated enum rows + the now-empty
-- object_tree_categories enum category.
--
-- The new categories table owns depth, icon, and description as first-class
-- columns rather than bolting domain-specific fields onto the generic enum.
--
-- Subcategories follow the rpc_domains → rpc_subdomains relational pattern:
-- separate table, FK to parent category, own sequence and depth.
-- ============================================================================

SET NOCOUNT ON;


-- ============================================================================
-- STEP 1: Create system_objects_tree_categories
-- ============================================================================

IF NOT EXISTS (
  SELECT 1 FROM INFORMATION_SCHEMA.TABLES
  WHERE TABLE_NAME = 'system_objects_tree_categories'
)
BEGIN
  CREATE TABLE [dbo].[system_objects_tree_categories] (
    [key_guid]          UNIQUEIDENTIFIER  NOT NULL,
    [pub_name]          NVARCHAR(64)      NOT NULL,
    [pub_display]       NVARCHAR(128)     NOT NULL,
    [pub_icon]          NVARCHAR(64)      NULL,
    [pub_description]   NVARCHAR(512)     NULL,
    [pub_sequence]      INT               NOT NULL  CONSTRAINT [DF_sotc_sequence] DEFAULT 0,
    [pub_tree_depth]    INT               NOT NULL  CONSTRAINT [DF_sotc_depth] DEFAULT 1,
    [pub_is_active]     BIT               NOT NULL  CONSTRAINT [DF_sotc_active] DEFAULT 1,
    [priv_created_on]   DATETIMEOFFSET(7) NOT NULL  CONSTRAINT [DF_sotc_created] DEFAULT SYSUTCDATETIME(),
    [priv_modified_on]  DATETIMEOFFSET(7) NOT NULL  CONSTRAINT [DF_sotc_modified] DEFAULT SYSUTCDATETIME(),
    CONSTRAINT [PK_system_objects_tree_categories] PRIMARY KEY CLUSTERED ([key_guid]),
    CONSTRAINT [UQ_sotc_name] UNIQUE ([pub_name])
  );
  PRINT 'Created table: system_objects_tree_categories';
END;
GO


-- ============================================================================
-- STEP 2: Create system_objects_tree_subcategories
-- ============================================================================

IF NOT EXISTS (
  SELECT 1 FROM INFORMATION_SCHEMA.TABLES
  WHERE TABLE_NAME = 'system_objects_tree_subcategories'
)
BEGIN
  CREATE TABLE [dbo].[system_objects_tree_subcategories] (
    [key_guid]              UNIQUEIDENTIFIER  NOT NULL,
    [ref_category_guid]     UNIQUEIDENTIFIER  NOT NULL,
    [pub_name]              NVARCHAR(64)      NOT NULL,
    [pub_display]           NVARCHAR(128)     NOT NULL,
    [pub_icon]              NVARCHAR(64)      NULL,
    [pub_description]       NVARCHAR(512)     NULL,
    [pub_sequence]          INT               NOT NULL  CONSTRAINT [DF_sotsc_sequence] DEFAULT 0,
    [pub_is_active]         BIT               NOT NULL  CONSTRAINT [DF_sotsc_active] DEFAULT 1,
    [priv_created_on]       DATETIMEOFFSET(7) NOT NULL  CONSTRAINT [DF_sotsc_created] DEFAULT SYSUTCDATETIME(),
    [priv_modified_on]      DATETIMEOFFSET(7) NOT NULL  CONSTRAINT [DF_sotsc_modified] DEFAULT SYSUTCDATETIME(),
    CONSTRAINT [PK_system_objects_tree_subcategories] PRIMARY KEY CLUSTERED ([key_guid]),
    CONSTRAINT [FK_sotsc_category] FOREIGN KEY ([ref_category_guid])
      REFERENCES [dbo].[system_objects_tree_categories] ([key_guid]),
    CONSTRAINT [UQ_sotsc_category_name] UNIQUE ([ref_category_guid], [pub_name])
  );
  PRINT 'Created table: system_objects_tree_subcategories';
END;
GO


-- ============================================================================
-- STEP 3: Migrate category data from service_enum_values
--
-- Preserves existing key_guids so all FK references remain valid.
-- Depth values:
--   0 = flat list, no tree expansion (Routes, Queries, Configuration)
--   1 = root items, drill handled by builder panel (Types, Modules, etc.)
--   2 = root → children in tree (Database: tables → columns)
-- ============================================================================

MERGE [dbo].[system_objects_tree_categories] AS target
USING (
  SELECT
    [key_guid],
    [pub_name],
    [pub_display],
    [pub_icon],
    [pub_sequence],
    CASE [pub_name]
      WHEN 'database'           THEN 2   -- tables → columns
      WHEN 'database_contracts' THEN 1   -- views (future drill)
      WHEN 'types'              THEN 1   -- type list, drill in builder
      WHEN 'components'         THEN 1   -- component list, drill in builder
      WHEN 'pages'              THEN 1   -- page list, drill in builder
      WHEN 'routes'             THEN 0   -- flat route list
      WHEN 'modules'            THEN 1   -- module list, drill in builder
      WHEN 'app_contracts'      THEN 1   -- contract list, drill in builder
      WHEN 'rpc_surface'        THEN 1   -- domain list, drill in builder
      WHEN 'rpc_contracts'      THEN 1   -- model list, drill in builder
      WHEN 'security'           THEN 1   -- role list, drill in builder
      WHEN 'gateways'           THEN 1   -- gateway list, drill in builder
      WHEN 'agents'             THEN 1   -- agent list, drill in builder
      WHEN 'enumerations'       THEN 1   -- enum category list, drill in builder
      WHEN 'queries'            THEN 0   -- flat query list
      WHEN 'configuration'      THEN 0   -- flat config list
      ELSE 1
    END AS [pub_tree_depth]
  FROM [dbo].[service_enum_values]
  WHERE [ref_category_guid] = N'9E735725-2EFF-5978-B92F-73A6CB36DF7F'
) AS src
ON target.[key_guid] = src.[key_guid]
WHEN MATCHED THEN UPDATE SET
  [pub_name]        = src.[pub_name],
  [pub_display]     = src.[pub_display],
  [pub_icon]        = src.[pub_icon],
  [pub_sequence]    = src.[pub_sequence],
  [pub_tree_depth]  = src.[pub_tree_depth],
  [priv_modified_on]= SYSUTCDATETIME()
WHEN NOT MATCHED THEN INSERT
  ([key_guid], [pub_name], [pub_display], [pub_icon], [pub_sequence], [pub_tree_depth])
VALUES
  (src.[key_guid], src.[pub_name], src.[pub_display], src.[pub_icon], src.[pub_sequence], src.[pub_tree_depth]);

PRINT 'Migrated category data to system_objects_tree_categories';
GO


-- ============================================================================
-- STEP 4: Retarget FK on system_objects_tree_category_tables
--
-- Drop the old FK pointing at service_enum_values, add new FK pointing at
-- system_objects_tree_categories. The key_guids are identical so no data
-- changes needed in the junction table itself.
-- ============================================================================

-- Find and drop existing FK (name may vary by environment)
DECLARE @fk_name NVARCHAR(256);
SELECT @fk_name = fk.name
FROM sys.foreign_keys fk
JOIN sys.foreign_key_columns fkc ON fk.object_id = fkc.constraint_object_id
JOIN sys.columns c ON fkc.parent_column_id = c.column_id
  AND fkc.parent_object_id = c.object_id
WHERE fk.parent_object_id = OBJECT_ID('system_objects_tree_category_tables')
  AND c.name = 'ref_category_guid';

IF @fk_name IS NOT NULL
BEGIN
  EXEC('ALTER TABLE [dbo].[system_objects_tree_category_tables] DROP CONSTRAINT [' + @fk_name + ']');
  PRINT 'Dropped old FK: ' + @fk_name;
END;

-- Add new FK pointing at the dedicated categories table
ALTER TABLE [dbo].[system_objects_tree_category_tables]
  ADD CONSTRAINT [FK_sotct_tree_category]
  FOREIGN KEY ([ref_category_guid])
  REFERENCES [dbo].[system_objects_tree_categories] ([key_guid]);

PRINT 'Added FK: FK_sotct_tree_category → system_objects_tree_categories';
GO


-- ============================================================================
-- STEP 5: Update the get_categories query
--
-- Change from querying service_enum_values to querying the new categories
-- table. Now returns pub_tree_depth and pub_description. No longer needs
-- the category_enum_guid parameter — the table IS the category list.
-- ============================================================================

UPDATE [dbo].[system_objects_queries]
SET [pub_query_text] = N'SELECT
  c.key_guid AS guid,
  c.pub_name AS name,
  c.pub_display AS display,
  c.pub_icon AS icon,
  c.pub_sequence AS sequence,
  c.pub_tree_depth AS treeDepth,
  c.pub_description AS description
FROM system_objects_tree_categories c
WHERE c.pub_is_active = 1
ORDER BY c.pub_sequence
FOR JSON PATH, INCLUDE_NULL_VALUES;',
    [pub_description] = N'Fetch object tree categories from the dedicated categories table.',
    [pub_is_parameterized] = 0,
    [pub_parameter_names] = NULL,
    [priv_modified_on] = SYSUTCDATETIME()
WHERE [pub_name] = N'cms.object_tree.get_categories';

PRINT 'Updated query: cms.object_tree.get_categories (now reads from tree_categories, no parameters)';
GO


-- ============================================================================
-- STEP 6: Register new tables in database reflection registry
-- ============================================================================

MERGE [dbo].[system_objects_database_tables] AS target
USING (VALUES
  (N'F1A2B3C4-D5E6-5F7A-8B9C-0D1E2F3A4B5C', N'system_objects_tree_categories', N'dbo'),
  (N'A2B3C4D5-E6F7-5A8B-9C0D-1E2F3A4B5C6D', N'system_objects_tree_subcategories', N'dbo')
) AS src ([key_guid], [pub_name], [pub_schema])
ON target.[key_guid] = src.[key_guid]
WHEN NOT MATCHED THEN
  INSERT ([key_guid], [pub_name], [pub_schema])
  VALUES (src.[key_guid], src.[pub_name], src.[pub_schema]);

PRINT 'Registered new tables in reflection registry';
GO


-- ============================================================================
-- STEP 7: Clean up migrated enum rows
--
-- Remove the 16 object tree category rows from service_enum_values.
-- Also remove the object_tree_categories enum category itself from
-- service_enum_categories (if it exists there).
-- ============================================================================

DELETE FROM [dbo].[service_enum_values]
WHERE [ref_category_guid] = N'9E735725-2EFF-5978-B92F-73A6CB36DF7F';

PRINT 'Removed migrated enum values (object tree categories)';

-- Remove the category definition if it exists in service_enum_categories
DELETE FROM [dbo].[service_enum_categories]
WHERE [key_guid] = N'9E735725-2EFF-5978-B92F-73A6CB36DF7F';

PRINT 'Removed object_tree_categories enum category';
GO


-- ============================================================================
-- STEP 8: Update CmsWorkbenchModule.read_object_tree_categories()
--
-- The server method currently passes the enum category GUID as a parameter:
--   self._run_query("cms.object_tree.get_categories", ("9E735725-...",))
--
-- The updated query no longer takes parameters. The server method call
-- must change from:
--   await self._run_query("cms.object_tree.get_categories", ("9E735725-...",))
-- to:
--   await self._run_query("cms.object_tree.get_categories")
--
-- This is a CODE CHANGE in:
--   server/modules/cms_workbench_module.py → read_object_tree_categories()
--
-- The _run_query method needs to handle the case where params is empty/omitted.
-- Currently: async def _run_query(self, query_name: str, params: tuple = ())
-- This already supports empty params via the default, so the call just changes.
-- ============================================================================

PRINT '*** CODE CHANGE REQUIRED ***';
PRINT 'In server/modules/cms_workbench_module.py, method read_object_tree_categories():';
PRINT '  BEFORE: await self._run_query("cms.object_tree.get_categories", ("9E735725-2EFF-5978-B92F-73A6CB36DF7F",))';
PRINT '  AFTER:  await self._run_query("cms.object_tree.get_categories")';
PRINT '';
PRINT 'In client/src/api/rpc.ts, add treeDepth to ObjectTreeCategory interface:';
PRINT '  treeDepth: number;';
PRINT '';
PRINT 'In client/src/components/ObjectTreeView.tsx:';
PRINT '  Use category.treeDepth to control expand chevron visibility.';
PRINT '  treeDepth >= 2 → show expand on L1 children';
PRINT '  treeDepth < 2  → L1 children are leaf nodes (no chevron)';
GO


-- ============================================================================
-- VERIFICATION
-- ============================================================================

PRINT '--- Categories table contents ---';
SELECT pub_name, pub_display, pub_sequence, pub_tree_depth, pub_icon
FROM [dbo].[system_objects_tree_categories]
ORDER BY pub_sequence;

PRINT '--- FK validation: tree_category_tables → categories ---';
SELECT
  c.pub_name AS category_name,
  t.pub_name AS table_name,
  ct.pub_sequence,
  ct.pub_is_root_table
FROM [dbo].[system_objects_tree_category_tables] ct
JOIN [dbo].[system_objects_tree_categories] c ON c.key_guid = ct.ref_category_guid
JOIN [dbo].[system_objects_database_tables] t ON t.key_guid = ct.ref_table_guid
ORDER BY c.pub_sequence, ct.pub_sequence;

PRINT '--- Remaining enum values (should have zero object tree rows) ---';
SELECT COUNT(*) AS remaining_ot_enums
FROM [dbo].[service_enum_values]
WHERE [ref_category_guid] = N'9E735725-2EFF-5978-B92F-73A6CB36DF7F';

PRINT '--- Updated query text ---';
SELECT pub_name, pub_is_parameterized, pub_parameter_names
FROM [dbo].[system_objects_queries]
WHERE pub_name = N'cms.object_tree.get_categories';

PRINT 'v0.12.18.0 category promotion complete.';
GO