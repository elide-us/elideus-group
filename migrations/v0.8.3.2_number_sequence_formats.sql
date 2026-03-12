SET ANSI_NULLS ON;
SET QUOTED_IDENTIFIER ON;
GO

-- ============================================================================
-- v0.8.3.2 Number Sequence Format Fields + Periods FK
-- ============================================================================

-- A1. Add format fields to finance_numbers
ALTER TABLE finance_numbers ADD element_pattern NVARCHAR(256) NULL;
GO
ALTER TABLE finance_numbers ADD element_display_format NVARCHAR(256) NULL;
GO

-- A2. Add numbers_recid FK to finance_periods
ALTER TABLE finance_periods ADD numbers_recid BIGINT NULL;
GO
ALTER TABLE finance_periods ADD CONSTRAINT FK_finance_periods_numbers
  FOREIGN KEY (numbers_recid) REFERENCES finance_numbers(recid);
GO

-- ============================================================================
-- REFLECTION TABLE UPDATES
-- ============================================================================

-- New columns on finance_numbers (ordinals 10-11, after existing 9 columns)
INSERT INTO system_schema_columns (
  tables_recid, edt_recid, element_name, element_ordinal, element_nullable,
  element_default, element_max_length, element_is_primary_key, element_is_identity
) VALUES
  ((SELECT recid FROM system_schema_tables WHERE element_name = 'finance_numbers' AND element_schema = 'dbo'), (SELECT recid FROM system_edt_mappings WHERE element_name = 'STRING'), 'element_pattern', 10, 1, NULL, 256, 0, 0),
  ((SELECT recid FROM system_schema_tables WHERE element_name = 'finance_numbers' AND element_schema = 'dbo'), (SELECT recid FROM system_edt_mappings WHERE element_name = 'STRING'), 'element_display_format', 11, 1, NULL, 256, 0, 0);
GO

-- New column on finance_periods (ordinal 16, after existing 15 columns)
INSERT INTO system_schema_columns (
  tables_recid, edt_recid, element_name, element_ordinal, element_nullable,
  element_default, element_max_length, element_is_primary_key, element_is_identity
) VALUES
  ((SELECT recid FROM system_schema_tables WHERE element_name = 'finance_periods' AND element_schema = 'dbo'), (SELECT recid FROM system_edt_mappings WHERE element_name = 'INT64'), 'numbers_recid', 16, 1, NULL, NULL, 0, 0);
GO

-- New foreign key
INSERT INTO system_schema_foreign_keys (
  tables_recid, element_column_name, referenced_tables_recid, element_referenced_column
) VALUES
  ((SELECT recid FROM system_schema_tables WHERE element_name = 'finance_periods' AND element_schema = 'dbo'), 'numbers_recid', (SELECT recid FROM system_schema_tables WHERE element_name = 'finance_numbers' AND element_schema = 'dbo'), 'recid');
GO
