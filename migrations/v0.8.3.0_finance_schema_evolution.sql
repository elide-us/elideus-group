SET ANSI_NULLS ON;
SET QUOTED_IDENTIFIER ON;
GO

-- ============================================================================
-- v0.8.3.0 Finance Schema Evolution
-- ============================================================================

-- A1. finance_dimensions — multi-dimensional financial analysis
CREATE TABLE [dbo].[finance_dimensions] (
  [recid] BIGINT IDENTITY(1,1) NOT NULL,
  [element_name] NVARCHAR(64) NOT NULL,
  [element_value] NVARCHAR(128) NOT NULL,
  [element_description] NVARCHAR(512) NULL,
  [element_status] TINYINT NOT NULL DEFAULT ((1)),
  [element_created_on] DATETIMEOFFSET(7) NOT NULL DEFAULT (SYSUTCDATETIME()),
  [element_modified_on] DATETIMEOFFSET(7) NOT NULL DEFAULT (SYSUTCDATETIME()),
  CONSTRAINT [PK_finance_dimensions] PRIMARY KEY ([recid])
);
GO

CREATE UNIQUE NONCLUSTERED INDEX UQ_finance_dimensions_name_value
  ON finance_dimensions (element_name, element_value);
GO

-- A2. finance_journals — journal type definitions
CREATE TABLE [dbo].[finance_journals] (
  [recid] BIGINT IDENTITY(1,1) NOT NULL,
  [element_name] NVARCHAR(64) NOT NULL,
  [element_description] NVARCHAR(512) NULL,
  [numbers_recid] BIGINT NULL,
  [element_status] TINYINT NOT NULL DEFAULT ((1)),
  [element_created_on] DATETIMEOFFSET(7) NOT NULL DEFAULT (SYSUTCDATETIME()),
  [element_modified_on] DATETIMEOFFSET(7) NOT NULL DEFAULT (SYSUTCDATETIME()),
  CONSTRAINT [PK_finance_journals] PRIMARY KEY ([recid]),
  CONSTRAINT [FK_finance_journals_numbers] FOREIGN KEY ([numbers_recid]) REFERENCES [finance_numbers]([recid])
);
GO

CREATE UNIQUE NONCLUSTERED INDEX UQ_finance_journals_name
  ON finance_journals (element_name);
GO

-- A3. finance_ledgers — ledger definitions
CREATE TABLE [dbo].[finance_ledgers] (
  [recid] BIGINT IDENTITY(1,1) NOT NULL,
  [element_name] NVARCHAR(64) NOT NULL,
  [element_description] NVARCHAR(512) NULL,
  [element_chart_of_accounts_guid] UNIQUEIDENTIFIER NULL,
  [element_fiscal_calendar_year] INT NULL,
  [element_status] TINYINT NOT NULL DEFAULT ((1)),
  [element_created_on] DATETIMEOFFSET(7) NOT NULL DEFAULT (SYSUTCDATETIME()),
  [element_modified_on] DATETIMEOFFSET(7) NOT NULL DEFAULT (SYSUTCDATETIME()),
  CONSTRAINT [PK_finance_ledgers] PRIMARY KEY ([recid]),
  CONSTRAINT [FK_finance_ledgers_chart] FOREIGN KEY ([element_chart_of_accounts_guid]) REFERENCES [finance_accounts]([element_guid])
);
GO

CREATE UNIQUE NONCLUSTERED INDEX UQ_finance_ledgers_name
  ON finance_ledgers (element_name);
GO

-- ============================================================================
-- REFLECTION TABLE UPDATES
-- ============================================================================

-- Register new tables
INSERT INTO system_schema_tables (element_name, element_schema) VALUES
  ('finance_dimensions', 'dbo'),
  ('finance_journals', 'dbo'),
  ('finance_ledgers', 'dbo');
GO

-- Columns for finance_dimensions (ordinals 1-7)
INSERT INTO system_schema_columns (
  tables_recid, edt_recid, element_name, element_ordinal, element_nullable,
  element_default, element_max_length, element_is_primary_key, element_is_identity
) VALUES
  ((SELECT recid FROM system_schema_tables WHERE element_name = 'finance_dimensions' AND element_schema = 'dbo'), (SELECT recid FROM system_edt_mappings WHERE element_name = 'INT64_IDENTITY'), 'recid', 1, 0, NULL, NULL, 1, 1),
  ((SELECT recid FROM system_schema_tables WHERE element_name = 'finance_dimensions' AND element_schema = 'dbo'), (SELECT recid FROM system_edt_mappings WHERE element_name = 'STRING'), 'element_name', 2, 0, NULL, 64, 0, 0),
  ((SELECT recid FROM system_schema_tables WHERE element_name = 'finance_dimensions' AND element_schema = 'dbo'), (SELECT recid FROM system_edt_mappings WHERE element_name = 'STRING'), 'element_value', 3, 0, NULL, 128, 0, 0),
  ((SELECT recid FROM system_schema_tables WHERE element_name = 'finance_dimensions' AND element_schema = 'dbo'), (SELECT recid FROM system_edt_mappings WHERE element_name = 'STRING'), 'element_description', 4, 1, NULL, 512, 0, 0),
  ((SELECT recid FROM system_schema_tables WHERE element_name = 'finance_dimensions' AND element_schema = 'dbo'), (SELECT recid FROM system_edt_mappings WHERE element_name = 'INT8'), 'element_status', 5, 0, '((1))', NULL, 0, 0),
  ((SELECT recid FROM system_schema_tables WHERE element_name = 'finance_dimensions' AND element_schema = 'dbo'), (SELECT recid FROM system_edt_mappings WHERE element_name = 'DATETIME_TZ'), 'element_created_on', 6, 0, '(sysutcdatetime())', NULL, 0, 0),
  ((SELECT recid FROM system_schema_tables WHERE element_name = 'finance_dimensions' AND element_schema = 'dbo'), (SELECT recid FROM system_edt_mappings WHERE element_name = 'DATETIME_TZ'), 'element_modified_on', 7, 0, '(sysutcdatetime())', NULL, 0, 0);
GO

-- Columns for finance_journals (ordinals 1-7)
INSERT INTO system_schema_columns (
  tables_recid, edt_recid, element_name, element_ordinal, element_nullable,
  element_default, element_max_length, element_is_primary_key, element_is_identity
) VALUES
  ((SELECT recid FROM system_schema_tables WHERE element_name = 'finance_journals' AND element_schema = 'dbo'), (SELECT recid FROM system_edt_mappings WHERE element_name = 'INT64_IDENTITY'), 'recid', 1, 0, NULL, NULL, 1, 1),
  ((SELECT recid FROM system_schema_tables WHERE element_name = 'finance_journals' AND element_schema = 'dbo'), (SELECT recid FROM system_edt_mappings WHERE element_name = 'STRING'), 'element_name', 2, 0, NULL, 64, 0, 0),
  ((SELECT recid FROM system_schema_tables WHERE element_name = 'finance_journals' AND element_schema = 'dbo'), (SELECT recid FROM system_edt_mappings WHERE element_name = 'STRING'), 'element_description', 3, 1, NULL, 512, 0, 0),
  ((SELECT recid FROM system_schema_tables WHERE element_name = 'finance_journals' AND element_schema = 'dbo'), (SELECT recid FROM system_edt_mappings WHERE element_name = 'INT64'), 'numbers_recid', 4, 1, NULL, NULL, 0, 0),
  ((SELECT recid FROM system_schema_tables WHERE element_name = 'finance_journals' AND element_schema = 'dbo'), (SELECT recid FROM system_edt_mappings WHERE element_name = 'INT8'), 'element_status', 5, 0, '((1))', NULL, 0, 0),
  ((SELECT recid FROM system_schema_tables WHERE element_name = 'finance_journals' AND element_schema = 'dbo'), (SELECT recid FROM system_edt_mappings WHERE element_name = 'DATETIME_TZ'), 'element_created_on', 6, 0, '(sysutcdatetime())', NULL, 0, 0),
  ((SELECT recid FROM system_schema_tables WHERE element_name = 'finance_journals' AND element_schema = 'dbo'), (SELECT recid FROM system_edt_mappings WHERE element_name = 'DATETIME_TZ'), 'element_modified_on', 7, 0, '(sysutcdatetime())', NULL, 0, 0);
GO

-- Columns for finance_ledgers (ordinals 1-8)
INSERT INTO system_schema_columns (
  tables_recid, edt_recid, element_name, element_ordinal, element_nullable,
  element_default, element_max_length, element_is_primary_key, element_is_identity
) VALUES
  ((SELECT recid FROM system_schema_tables WHERE element_name = 'finance_ledgers' AND element_schema = 'dbo'), (SELECT recid FROM system_edt_mappings WHERE element_name = 'INT64_IDENTITY'), 'recid', 1, 0, NULL, NULL, 1, 1),
  ((SELECT recid FROM system_schema_tables WHERE element_name = 'finance_ledgers' AND element_schema = 'dbo'), (SELECT recid FROM system_edt_mappings WHERE element_name = 'STRING'), 'element_name', 2, 0, NULL, 64, 0, 0),
  ((SELECT recid FROM system_schema_tables WHERE element_name = 'finance_ledgers' AND element_schema = 'dbo'), (SELECT recid FROM system_edt_mappings WHERE element_name = 'STRING'), 'element_description', 3, 1, NULL, 512, 0, 0),
  ((SELECT recid FROM system_schema_tables WHERE element_name = 'finance_ledgers' AND element_schema = 'dbo'), (SELECT recid FROM system_edt_mappings WHERE element_name = 'UUID'), 'element_chart_of_accounts_guid', 4, 1, NULL, NULL, 0, 0),
  ((SELECT recid FROM system_schema_tables WHERE element_name = 'finance_ledgers' AND element_schema = 'dbo'), (SELECT recid FROM system_edt_mappings WHERE element_name = 'INT32'), 'element_fiscal_calendar_year', 5, 1, NULL, NULL, 0, 0),
  ((SELECT recid FROM system_schema_tables WHERE element_name = 'finance_ledgers' AND element_schema = 'dbo'), (SELECT recid FROM system_edt_mappings WHERE element_name = 'INT8'), 'element_status', 6, 0, '((1))', NULL, 0, 0),
  ((SELECT recid FROM system_schema_tables WHERE element_name = 'finance_ledgers' AND element_schema = 'dbo'), (SELECT recid FROM system_edt_mappings WHERE element_name = 'DATETIME_TZ'), 'element_created_on', 7, 0, '(sysutcdatetime())', NULL, 0, 0),
  ((SELECT recid FROM system_schema_tables WHERE element_name = 'finance_ledgers' AND element_schema = 'dbo'), (SELECT recid FROM system_edt_mappings WHERE element_name = 'DATETIME_TZ'), 'element_modified_on', 8, 0, '(sysutcdatetime())', NULL, 0, 0);
GO

-- New indexes
INSERT INTO system_schema_indexes (tables_recid, element_name, element_columns, element_is_unique) VALUES
  ((SELECT recid FROM system_schema_tables WHERE element_name = 'finance_dimensions' AND element_schema = 'dbo'), 'UQ_finance_dimensions_name_value', 'element_name, element_value', 1),
  ((SELECT recid FROM system_schema_tables WHERE element_name = 'finance_journals' AND element_schema = 'dbo'), 'UQ_finance_journals_name', 'element_name', 1),
  ((SELECT recid FROM system_schema_tables WHERE element_name = 'finance_ledgers' AND element_schema = 'dbo'), 'UQ_finance_ledgers_name', 'element_name', 1);
GO

-- New foreign keys
INSERT INTO system_schema_foreign_keys (
  tables_recid, element_column_name, referenced_tables_recid, element_referenced_column
) VALUES
  ((SELECT recid FROM system_schema_tables WHERE element_name = 'finance_journals' AND element_schema = 'dbo'), 'numbers_recid', (SELECT recid FROM system_schema_tables WHERE element_name = 'finance_numbers' AND element_schema = 'dbo'), 'recid'),
  ((SELECT recid FROM system_schema_tables WHERE element_name = 'finance_ledgers' AND element_schema = 'dbo'), 'element_chart_of_accounts_guid', (SELECT recid FROM system_schema_tables WHERE element_name = 'finance_accounts' AND element_schema = 'dbo'), 'element_guid');
GO
