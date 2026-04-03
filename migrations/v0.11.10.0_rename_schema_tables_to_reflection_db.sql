-- Rename system_schema_* tables to reflection_db_*
-- Rename system_edt_mappings to reflection_db_edt_mappings

EXEC sp_rename 'system_edt_mappings', 'reflection_db_edt_mappings';
GO
EXEC sp_rename 'system_schema_tables', 'reflection_db_tables';
GO
EXEC sp_rename 'system_schema_columns', 'reflection_db_columns';
GO
EXEC sp_rename 'system_schema_indexes', 'reflection_db_indexes';
GO
EXEC sp_rename 'system_schema_foreign_keys', 'reflection_db_foreign_keys';
GO
EXEC sp_rename 'system_schema_views', 'reflection_db_views';
GO

-- Update the reflection metadata: system_schema_tables stores its own name
-- Update the cached table names in the tables registry itself
UPDATE reflection_db_tables
SET element_name = 'reflection_db_edt_mappings'
WHERE element_schema = 'dbo' AND element_name = 'system_edt_mappings';

UPDATE reflection_db_tables
SET element_name = 'reflection_db_tables'
WHERE element_schema = 'dbo' AND element_name = 'system_schema_tables';

UPDATE reflection_db_tables
SET element_name = 'reflection_db_columns'
WHERE element_schema = 'dbo' AND element_name = 'system_schema_columns';

UPDATE reflection_db_tables
SET element_name = 'reflection_db_indexes'
WHERE element_schema = 'dbo' AND element_name = 'system_schema_indexes';

UPDATE reflection_db_tables
SET element_name = 'reflection_db_foreign_keys'
WHERE element_schema = 'dbo' AND element_name = 'system_schema_foreign_keys';

UPDATE reflection_db_tables
SET element_name = 'reflection_db_views'
WHERE element_schema = 'dbo' AND element_name = 'system_schema_views';
GO
