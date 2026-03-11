-- ============================================================
-- v0.8.2.0 — Expand assistant_models table
-- Adds element_api_provider and element_is_active columns
-- ============================================================

-- Add api_provider column (defaults to 'openai' for existing rows)
IF NOT EXISTS (
  SELECT 1 FROM sys.columns
  WHERE object_id = OBJECT_ID('dbo.assistant_models')
  AND name = 'element_api_provider'
)
BEGIN
  ALTER TABLE assistant_models ADD element_api_provider NVARCHAR(64) NOT NULL DEFAULT 'openai';
END
GO

-- Add is_active column (defaults to 1 for existing rows)
IF NOT EXISTS (
  SELECT 1 FROM sys.columns
  WHERE object_id = OBJECT_ID('dbo.assistant_models')
  AND name = 'element_is_active'
)
BEGIN
  ALTER TABLE assistant_models ADD element_is_active BIT NOT NULL DEFAULT 1;
END
GO

-- Add timestamps if they don't exist
IF NOT EXISTS (
  SELECT 1 FROM sys.columns
  WHERE object_id = OBJECT_ID('dbo.assistant_models')
  AND name = 'element_created_on'
)
BEGIN
  ALTER TABLE assistant_models ADD element_created_on DATETIMEOFFSET(7) NOT NULL DEFAULT SYSUTCDATETIME();
END
GO

IF NOT EXISTS (
  SELECT 1 FROM sys.columns
  WHERE object_id = OBJECT_ID('dbo.assistant_models')
  AND name = 'element_modified_on'
)
BEGIN
  ALTER TABLE assistant_models ADD element_modified_on DATETIMEOFFSET(7) NOT NULL DEFAULT SYSUTCDATETIME();
END
GO

-- Reflection table updates
-- system_schema_columns for new columns on assistant_models
INSERT INTO system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT
  (SELECT recid FROM system_schema_tables WHERE element_name = 'assistant_models' AND element_schema = 'dbo'),
  (SELECT recid FROM system_edt_mappings WHERE element_name = 'STRING'),
  'element_api_provider', 3, 0, '(''openai'')', 64, 0, 0
WHERE NOT EXISTS (
  SELECT 1 FROM system_schema_columns c
  JOIN system_schema_tables t ON t.recid = c.tables_recid
  WHERE t.element_name = 'assistant_models' AND c.element_name = 'element_api_provider'
);
GO

INSERT INTO system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT
  (SELECT recid FROM system_schema_tables WHERE element_name = 'assistant_models' AND element_schema = 'dbo'),
  (SELECT recid FROM system_edt_mappings WHERE element_name = 'BOOLEAN'),
  'element_is_active', 4, 0, '((1))', NULL, 0, 0
WHERE NOT EXISTS (
  SELECT 1 FROM system_schema_columns c
  JOIN system_schema_tables t ON t.recid = c.tables_recid
  WHERE t.element_name = 'assistant_models' AND c.element_name = 'element_is_active'
);
GO

INSERT INTO system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT
  (SELECT recid FROM system_schema_tables WHERE element_name = 'assistant_models' AND element_schema = 'dbo'),
  (SELECT recid FROM system_edt_mappings WHERE element_name = 'DATETIME_TZ'),
  'element_created_on', 5, 0, '(sysutcdatetime())', NULL, 0, 0
WHERE NOT EXISTS (
  SELECT 1 FROM system_schema_columns c
  JOIN system_schema_tables t ON t.recid = c.tables_recid
  WHERE t.element_name = 'assistant_models' AND c.element_name = 'element_created_on'
);
GO

INSERT INTO system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT
  (SELECT recid FROM system_schema_tables WHERE element_name = 'assistant_models' AND element_schema = 'dbo'),
  (SELECT recid FROM system_edt_mappings WHERE element_name = 'DATETIME_TZ'),
  'element_modified_on', 6, 0, '(sysutcdatetime())', NULL, 0, 0
WHERE NOT EXISTS (
  SELECT 1 FROM system_schema_columns c
  JOIN system_schema_tables t ON t.recid = c.tables_recid
  WHERE t.element_name = 'assistant_models' AND c.element_name = 'element_modified_on'
);
GO
