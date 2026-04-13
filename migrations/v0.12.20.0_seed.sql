-- ============================================================================
-- v0.12.20.0 — Builder Component Infrastructure
--
-- Adds pub_builder_component column to system_objects_tree_categories.
-- Registers DatabaseBuilder, TypesBuilder, ModulesBuilder as components.
-- Sets builder component references on the three categories that have builders.
-- Updates the get_categories query to return builderComponent.
--
-- After this migration, Codex Task B can refactor ObjectEditor to resolve
-- builders dynamically from category.builderComponent instead of string
-- matching on categoryName.
--
-- REMINDER: After running this migration, also update the Pydantic model
-- ObjectTreeCategory1 in rpc/public/route/models.py to add:
--   builderComponent: str | None = None
-- (same pattern as the treeDepth fix)
-- ============================================================================

SET NOCOUNT ON;


-- ============================================================================
-- STEP 1: Add pub_builder_component column
-- ============================================================================

IF NOT EXISTS (
  SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS
  WHERE TABLE_NAME = 'system_objects_tree_categories'
    AND COLUMN_NAME = 'pub_builder_component'
)
BEGIN
  ALTER TABLE [dbo].[system_objects_tree_categories]
    ADD [pub_builder_component] NVARCHAR(128) NULL;
  PRINT 'Added column: system_objects_tree_categories.pub_builder_component';
END;
GO


-- ============================================================================
-- STEP 2: Register builder components in system_objects_components
--
-- These are the three existing builder TSX files that are currently imported
-- directly by ObjectEditor but not registered in the component registry data.
-- ============================================================================

MERGE [dbo].[system_objects_components] AS target
USING (VALUES
  (N'A1F2B3C4-D5E6-5F7A-8B9C-1D2E3F4A5B6C',
   N'DatabaseBuilder', N'section',
   N'Object Tree editor for Database category. Table and column CRUD with type picker.'),
  (N'B2A3C4D5-E6F7-5A8B-9C0D-2E3F4A5B6C7D',
   N'TypesBuilder', N'section',
   N'Object Tree editor for Types category. EDT type CRUD with cross-platform mappings and component bindings.'),
  (N'C3B4D5E6-F7A8-5B9C-0D1E-3F4A5B6C7D8E',
   N'ModulesBuilder', N'section',
   N'Object Tree editor for Modules category. Module metadata and method CRUD with contract references.')
) AS src ([key_guid], [pub_name], [pub_category], [pub_description])
ON target.[key_guid] = src.[key_guid]
WHEN MATCHED THEN UPDATE SET
  [pub_name]        = src.[pub_name],
  [pub_category]    = src.[pub_category],
  [pub_description] = src.[pub_description],
  [priv_modified_on]= SYSUTCDATETIME()
WHEN NOT MATCHED THEN INSERT
  ([key_guid], [pub_name], [pub_category], [pub_description])
VALUES
  (src.[key_guid], src.[pub_name], src.[pub_category], src.[pub_description]);

PRINT 'Registered builder components: DatabaseBuilder, TypesBuilder, ModulesBuilder';
GO


-- ============================================================================
-- STEP 3: Set builder component names on categories
-- ============================================================================

UPDATE [dbo].[system_objects_tree_categories]
SET [pub_builder_component] = N'DatabaseBuilder',
    [priv_modified_on] = SYSUTCDATETIME()
WHERE [pub_name] = N'database';

UPDATE [dbo].[system_objects_tree_categories]
SET [pub_builder_component] = N'TypesBuilder',
    [priv_modified_on] = SYSUTCDATETIME()
WHERE [pub_name] = N'types';

UPDATE [dbo].[system_objects_tree_categories]
SET [pub_builder_component] = N'ModulesBuilder',
    [priv_modified_on] = SYSUTCDATETIME()
WHERE [pub_name] = N'modules';

PRINT 'Set builderComponent on database, types, modules categories';
GO


-- ============================================================================
-- STEP 4: Update get_categories query to return builderComponent
-- ============================================================================

UPDATE [dbo].[system_objects_queries]
SET [pub_query_text] = N'SELECT
  c.key_guid AS guid,
  c.pub_name AS name,
  c.pub_display AS display,
  c.pub_icon AS icon,
  c.pub_sequence AS sequence,
  c.pub_tree_depth AS treeDepth,
  c.pub_description AS description,
  c.pub_builder_component AS builderComponent
FROM system_objects_tree_categories c
WHERE c.pub_is_active = 1
ORDER BY c.pub_sequence
FOR JSON PATH, INCLUDE_NULL_VALUES;',
    [priv_modified_on] = SYSUTCDATETIME()
WHERE [pub_name] = N'cms.object_tree.get_categories';

PRINT 'Updated query: cms.object_tree.get_categories (added builderComponent)';
GO


-- ============================================================================
-- VERIFICATION
-- ============================================================================

PRINT '--- Categories with builder bindings ---';
SELECT pub_name, pub_display, pub_builder_component
FROM [dbo].[system_objects_tree_categories]
WHERE pub_builder_component IS NOT NULL
ORDER BY pub_sequence;

PRINT '--- Builder components in registry ---';
SELECT pub_name, pub_category, pub_description
FROM [dbo].[system_objects_components]
WHERE pub_name IN (N'DatabaseBuilder', N'TypesBuilder', N'ModulesBuilder');

PRINT '--- Query field check ---';
SELECT pub_name,
  CASE WHEN pub_query_text LIKE N'%builderComponent%' THEN 'YES' ELSE 'NO' END AS has_builderComponent
FROM [dbo].[system_objects_queries]
WHERE pub_name = N'cms.object_tree.get_categories';

PRINT '';
PRINT '*** CODE CHANGES REQUIRED (Codex Task B) ***';
PRINT '1. rpc/public/route/models.py — add to ObjectTreeCategory1:';
PRINT '     builderComponent: str | None = None';
PRINT '2. client/src/api/rpc.ts — add to ObjectTreeCategory interface:';
PRINT '     builderComponent: string | null;';
PRINT '3. client/src/engine/registry.ts — add imports + registry entries:';
PRINT '     DatabaseBuilder, TypesBuilder, ModulesBuilder';
PRINT '4. client/src/components/ObjectEditor.tsx — replace categoryName switch:';
PRINT '     resolve from COMPONENT_REGISTRY[selected.builderComponent]';
PRINT '';
PRINT 'v0.12.20.0 seed complete.';
GO