SET NOCOUNT ON;

IF NOT EXISTS (
  SELECT 1 FROM system_edt_mappings WHERE element_name = 'DECIMAL_19_5'
)
BEGIN
  INSERT INTO system_edt_mappings (
    element_name, element_mssql_type, element_postgresql_type, element_mysql_type,
    element_python_type, element_odbc_type_code, element_max_length, element_notes
  ) VALUES (
    'DECIMAL_19_5', 'decimal(19,5)', 'numeric(19,5)', 'decimal(19,5)', 'Decimal', 3, 19,
    'Fixed-point financial amount. 19 digits total, 5 after decimal. Stored and computed at 5dp, quantized to 4dp before posting per precision policy.'
  );
END;

IF EXISTS (
  SELECT 1
  FROM sys.indexes
  WHERE object_id = OBJECT_ID(N'[dbo].[finance_journals]')
    AND name = N'UQ_finance_journals_name'
)
BEGIN
  DROP INDEX [UQ_finance_journals_name] ON [dbo].[finance_journals];
END;

IF COL_LENGTH('dbo.finance_journals', 'element_posting_key') IS NULL
BEGIN
  ALTER TABLE [dbo].[finance_journals] ADD
    [element_posting_key]  NVARCHAR(256) NULL,
    [element_source_type]  NVARCHAR(64) NULL,
    [element_source_id]    NVARCHAR(256) NULL,
    [periods_guid]         UNIQUEIDENTIFIER NULL,
    [ledgers_recid]        BIGINT NULL,
    [element_posted_by]    UNIQUEIDENTIFIER NULL,
    [element_posted_on]    DATETIMEOFFSET(7) NULL,
    [element_reversed_by]  BIGINT NULL,
    [element_reversal_of]  BIGINT NULL;
END;

IF NOT EXISTS (
  SELECT 1
  FROM sys.indexes
  WHERE object_id = OBJECT_ID(N'[dbo].[finance_journals]')
    AND name = N'UQ_finance_journals_posting_key'
)
BEGIN
  CREATE UNIQUE INDEX [UQ_finance_journals_posting_key]
    ON [dbo].[finance_journals] ([element_posting_key])
    WHERE [element_posting_key] IS NOT NULL;
END;

IF NOT EXISTS (
  SELECT 1
  FROM sys.foreign_keys
  WHERE name = N'FK_finance_journals_periods_guid'
)
BEGIN
  ALTER TABLE [dbo].[finance_journals]
    ADD CONSTRAINT [FK_finance_journals_periods_guid]
    FOREIGN KEY ([periods_guid]) REFERENCES [dbo].[finance_periods] ([element_guid]);
END;

IF NOT EXISTS (
  SELECT 1
  FROM sys.foreign_keys
  WHERE name = N'FK_finance_journals_ledgers_recid'
)
BEGIN
  ALTER TABLE [dbo].[finance_journals]
    ADD CONSTRAINT [FK_finance_journals_ledgers_recid]
    FOREIGN KEY ([ledgers_recid]) REFERENCES [dbo].[finance_ledgers] ([recid]);
END;

IF NOT EXISTS (
  SELECT 1
  FROM sys.foreign_keys
  WHERE name = N'FK_finance_journals_reversed_by'
)
BEGIN
  ALTER TABLE [dbo].[finance_journals]
    ADD CONSTRAINT [FK_finance_journals_reversed_by]
    FOREIGN KEY ([element_reversed_by]) REFERENCES [dbo].[finance_journals] ([recid]);
END;

IF NOT EXISTS (
  SELECT 1
  FROM sys.foreign_keys
  WHERE name = N'FK_finance_journals_reversal_of'
)
BEGIN
  ALTER TABLE [dbo].[finance_journals]
    ADD CONSTRAINT [FK_finance_journals_reversal_of]
    FOREIGN KEY ([element_reversal_of]) REFERENCES [dbo].[finance_journals] ([recid]);
END;

IF OBJECT_ID(N'[dbo].[finance_journal_lines]', N'U') IS NULL
BEGIN
  CREATE TABLE [dbo].[finance_journal_lines] (
    [recid]                BIGINT IDENTITY(1,1) NOT NULL,
    [journals_recid]       BIGINT NOT NULL,
    [element_line_number]  INT NOT NULL,
    [accounts_guid]        UNIQUEIDENTIFIER NOT NULL,
    [element_debit]        DECIMAL(19,5) NOT NULL DEFAULT (0),
    [element_credit]       DECIMAL(19,5) NOT NULL DEFAULT (0),
    [element_description]  NVARCHAR(512) NULL,
    [element_created_on]   DATETIMEOFFSET(7) NOT NULL DEFAULT (SYSUTCDATETIME()),
    [element_modified_on]  DATETIMEOFFSET(7) NOT NULL DEFAULT (SYSUTCDATETIME()),
    CONSTRAINT [PK_finance_journal_lines] PRIMARY KEY ([recid]),
    CONSTRAINT [FK_journal_lines_journals] FOREIGN KEY ([journals_recid])
      REFERENCES [dbo].[finance_journals] ([recid]),
    CONSTRAINT [FK_journal_lines_accounts] FOREIGN KEY ([accounts_guid])
      REFERENCES [dbo].[finance_accounts] ([element_guid])
  );
END;

IF NOT EXISTS (
  SELECT 1
  FROM sys.indexes
  WHERE object_id = OBJECT_ID(N'[dbo].[finance_journal_lines]')
    AND name = N'IX_journal_lines_journals_recid'
)
BEGIN
  CREATE INDEX [IX_journal_lines_journals_recid]
    ON [dbo].[finance_journal_lines] ([journals_recid]);
END;

IF NOT EXISTS (
  SELECT 1
  FROM sys.indexes
  WHERE object_id = OBJECT_ID(N'[dbo].[finance_journal_lines]')
    AND name = N'UQ_journal_lines_journal_line'
)
BEGIN
  CREATE UNIQUE INDEX [UQ_journal_lines_journal_line]
    ON [dbo].[finance_journal_lines] ([journals_recid], [element_line_number]);
END;

IF OBJECT_ID(N'[dbo].[finance_journal_line_dimensions]', N'U') IS NULL
BEGIN
  CREATE TABLE [dbo].[finance_journal_line_dimensions] (
    [recid]              BIGINT IDENTITY(1,1) NOT NULL,
    [lines_recid]        BIGINT NOT NULL,
    [dimensions_recid]   BIGINT NOT NULL,
    CONSTRAINT [PK_finance_journal_line_dimensions] PRIMARY KEY ([recid]),
    CONSTRAINT [FK_line_dimensions_lines] FOREIGN KEY ([lines_recid])
      REFERENCES [dbo].[finance_journal_lines] ([recid]),
    CONSTRAINT [FK_line_dimensions_dimensions] FOREIGN KEY ([dimensions_recid])
      REFERENCES [dbo].[finance_dimensions] ([recid])
  );
END;

IF NOT EXISTS (
  SELECT 1
  FROM sys.indexes
  WHERE object_id = OBJECT_ID(N'[dbo].[finance_journal_line_dimensions]')
    AND name = N'UQ_line_dimensions_line_dim'
)
BEGIN
  CREATE UNIQUE INDEX [UQ_line_dimensions_line_dim]
    ON [dbo].[finance_journal_line_dimensions] ([lines_recid], [dimensions_recid]);
END;

-- ============================================================
-- Schema reflection metadata for journal engine tables
-- ============================================================

IF NOT EXISTS (
  SELECT 1 FROM system_schema_tables WHERE element_name = 'finance_journal_lines' AND element_schema = 'dbo'
)
BEGIN
  INSERT INTO system_schema_tables (element_name, element_schema)
  VALUES ('finance_journal_lines', 'dbo');
END;

IF NOT EXISTS (
  SELECT 1 FROM system_schema_tables WHERE element_name = 'finance_journal_line_dimensions' AND element_schema = 'dbo'
)
BEGIN
  INSERT INTO system_schema_tables (element_name, element_schema)
  VALUES ('finance_journal_line_dimensions', 'dbo');
END;

DELETE FROM system_schema_columns
WHERE tables_recid = (SELECT recid FROM system_schema_tables WHERE element_name = 'finance_journal_lines' AND element_schema = 'dbo');

INSERT INTO system_schema_columns (
  tables_recid, edt_recid, element_name, element_ordinal, element_nullable,
  element_default, element_max_length, element_is_primary_key, element_is_identity
) VALUES
  ((SELECT recid FROM system_schema_tables WHERE element_name = 'finance_journal_lines' AND element_schema = 'dbo'), (SELECT recid FROM system_edt_mappings WHERE element_name = 'INT64_IDENTITY'), 'recid', 1, 0, NULL, NULL, 1, 1),
  ((SELECT recid FROM system_schema_tables WHERE element_name = 'finance_journal_lines' AND element_schema = 'dbo'), (SELECT recid FROM system_edt_mappings WHERE element_name = 'INT64'), 'journals_recid', 2, 0, NULL, NULL, 0, 0),
  ((SELECT recid FROM system_schema_tables WHERE element_name = 'finance_journal_lines' AND element_schema = 'dbo'), (SELECT recid FROM system_edt_mappings WHERE element_name = 'INT32'), 'element_line_number', 3, 0, NULL, NULL, 0, 0),
  ((SELECT recid FROM system_schema_tables WHERE element_name = 'finance_journal_lines' AND element_schema = 'dbo'), (SELECT recid FROM system_edt_mappings WHERE element_name = 'UUID'), 'accounts_guid', 4, 0, NULL, NULL, 0, 0),
  ((SELECT recid FROM system_schema_tables WHERE element_name = 'finance_journal_lines' AND element_schema = 'dbo'), (SELECT recid FROM system_edt_mappings WHERE element_name = 'DECIMAL_19_5'), 'element_debit', 5, 0, '((0))', NULL, 0, 0),
  ((SELECT recid FROM system_schema_tables WHERE element_name = 'finance_journal_lines' AND element_schema = 'dbo'), (SELECT recid FROM system_edt_mappings WHERE element_name = 'DECIMAL_19_5'), 'element_credit', 6, 0, '((0))', NULL, 0, 0),
  ((SELECT recid FROM system_schema_tables WHERE element_name = 'finance_journal_lines' AND element_schema = 'dbo'), (SELECT recid FROM system_edt_mappings WHERE element_name = 'STRING'), 'element_description', 7, 1, NULL, 512, 0, 0),
  ((SELECT recid FROM system_schema_tables WHERE element_name = 'finance_journal_lines' AND element_schema = 'dbo'), (SELECT recid FROM system_edt_mappings WHERE element_name = 'DATETIME_TZ'), 'element_created_on', 8, 0, '(sysutcdatetime())', NULL, 0, 0),
  ((SELECT recid FROM system_schema_tables WHERE element_name = 'finance_journal_lines' AND element_schema = 'dbo'), (SELECT recid FROM system_edt_mappings WHERE element_name = 'DATETIME_TZ'), 'element_modified_on', 9, 0, '(sysutcdatetime())', NULL, 0, 0);

DELETE FROM system_schema_columns
WHERE tables_recid = (SELECT recid FROM system_schema_tables WHERE element_name = 'finance_journal_line_dimensions' AND element_schema = 'dbo');

INSERT INTO system_schema_columns (
  tables_recid, edt_recid, element_name, element_ordinal, element_nullable,
  element_default, element_max_length, element_is_primary_key, element_is_identity
) VALUES
  ((SELECT recid FROM system_schema_tables WHERE element_name = 'finance_journal_line_dimensions' AND element_schema = 'dbo'), (SELECT recid FROM system_edt_mappings WHERE element_name = 'INT64_IDENTITY'), 'recid', 1, 0, NULL, NULL, 1, 1),
  ((SELECT recid FROM system_schema_tables WHERE element_name = 'finance_journal_line_dimensions' AND element_schema = 'dbo'), (SELECT recid FROM system_edt_mappings WHERE element_name = 'INT64'), 'lines_recid', 2, 0, NULL, NULL, 0, 0),
  ((SELECT recid FROM system_schema_tables WHERE element_name = 'finance_journal_line_dimensions' AND element_schema = 'dbo'), (SELECT recid FROM system_edt_mappings WHERE element_name = 'INT64'), 'dimensions_recid', 3, 0, NULL, NULL, 0, 0);

DELETE FROM system_schema_columns
WHERE tables_recid = (SELECT recid FROM system_schema_tables WHERE element_name = 'finance_journals' AND element_schema = 'dbo')
  AND element_name IN (
    'element_posting_key',
    'element_source_type',
    'element_source_id',
    'periods_guid',
    'ledgers_recid',
    'element_posted_by',
    'element_posted_on',
    'element_reversed_by',
    'element_reversal_of'
  );

INSERT INTO system_schema_columns (
  tables_recid, edt_recid, element_name, element_ordinal, element_nullable,
  element_default, element_max_length, element_is_primary_key, element_is_identity
) VALUES
  ((SELECT recid FROM system_schema_tables WHERE element_name = 'finance_journals' AND element_schema = 'dbo'), (SELECT recid FROM system_edt_mappings WHERE element_name = 'STRING'), 'element_posting_key', 8, 1, NULL, 256, 0, 0),
  ((SELECT recid FROM system_schema_tables WHERE element_name = 'finance_journals' AND element_schema = 'dbo'), (SELECT recid FROM system_edt_mappings WHERE element_name = 'STRING'), 'element_source_type', 9, 1, NULL, 64, 0, 0),
  ((SELECT recid FROM system_schema_tables WHERE element_name = 'finance_journals' AND element_schema = 'dbo'), (SELECT recid FROM system_edt_mappings WHERE element_name = 'STRING'), 'element_source_id', 10, 1, NULL, 256, 0, 0),
  ((SELECT recid FROM system_schema_tables WHERE element_name = 'finance_journals' AND element_schema = 'dbo'), (SELECT recid FROM system_edt_mappings WHERE element_name = 'UUID'), 'periods_guid', 11, 1, NULL, NULL, 0, 0),
  ((SELECT recid FROM system_schema_tables WHERE element_name = 'finance_journals' AND element_schema = 'dbo'), (SELECT recid FROM system_edt_mappings WHERE element_name = 'INT64'), 'ledgers_recid', 12, 1, NULL, NULL, 0, 0),
  ((SELECT recid FROM system_schema_tables WHERE element_name = 'finance_journals' AND element_schema = 'dbo'), (SELECT recid FROM system_edt_mappings WHERE element_name = 'UUID'), 'element_posted_by', 13, 1, NULL, NULL, 0, 0),
  ((SELECT recid FROM system_schema_tables WHERE element_name = 'finance_journals' AND element_schema = 'dbo'), (SELECT recid FROM system_edt_mappings WHERE element_name = 'DATETIME_TZ'), 'element_posted_on', 14, 1, NULL, NULL, 0, 0),
  ((SELECT recid FROM system_schema_tables WHERE element_name = 'finance_journals' AND element_schema = 'dbo'), (SELECT recid FROM system_edt_mappings WHERE element_name = 'INT64'), 'element_reversed_by', 15, 1, NULL, NULL, 0, 0),
  ((SELECT recid FROM system_schema_tables WHERE element_name = 'finance_journals' AND element_schema = 'dbo'), (SELECT recid FROM system_edt_mappings WHERE element_name = 'INT64'), 'element_reversal_of', 16, 1, NULL, NULL, 0, 0);

DELETE FROM system_schema_indexes
WHERE tables_recid = (SELECT recid FROM system_schema_tables WHERE element_name = 'finance_journals' AND element_schema = 'dbo')
  AND element_name IN ('UQ_finance_journals_name', 'UQ_finance_journals_posting_key');

DELETE FROM system_schema_indexes
WHERE tables_recid = (SELECT recid FROM system_schema_tables WHERE element_name = 'finance_journal_lines' AND element_schema = 'dbo');

DELETE FROM system_schema_indexes
WHERE tables_recid = (SELECT recid FROM system_schema_tables WHERE element_name = 'finance_journal_line_dimensions' AND element_schema = 'dbo');

INSERT INTO system_schema_indexes (tables_recid, element_name, element_columns, element_is_unique) VALUES
  ((SELECT recid FROM system_schema_tables WHERE element_name = 'finance_journals' AND element_schema = 'dbo'), 'UQ_finance_journals_posting_key', 'element_posting_key', 1),
  ((SELECT recid FROM system_schema_tables WHERE element_name = 'finance_journal_lines' AND element_schema = 'dbo'), 'IX_journal_lines_journals_recid', 'journals_recid', 0),
  ((SELECT recid FROM system_schema_tables WHERE element_name = 'finance_journal_lines' AND element_schema = 'dbo'), 'UQ_journal_lines_journal_line', 'journals_recid,element_line_number', 1),
  ((SELECT recid FROM system_schema_tables WHERE element_name = 'finance_journal_line_dimensions' AND element_schema = 'dbo'), 'UQ_line_dimensions_line_dim', 'lines_recid,dimensions_recid', 1);

DELETE FROM system_schema_foreign_keys
WHERE tables_recid = (SELECT recid FROM system_schema_tables WHERE element_name = 'finance_journals' AND element_schema = 'dbo')
  AND element_column_name IN ('periods_guid', 'ledgers_recid', 'element_reversed_by', 'element_reversal_of');

DELETE FROM system_schema_foreign_keys
WHERE tables_recid = (SELECT recid FROM system_schema_tables WHERE element_name = 'finance_journal_lines' AND element_schema = 'dbo');

DELETE FROM system_schema_foreign_keys
WHERE tables_recid = (SELECT recid FROM system_schema_tables WHERE element_name = 'finance_journal_line_dimensions' AND element_schema = 'dbo');

INSERT INTO system_schema_foreign_keys (tables_recid, element_column_name, referenced_tables_recid, element_referenced_column) VALUES
  ((SELECT recid FROM system_schema_tables WHERE element_name = 'finance_journals' AND element_schema = 'dbo'), 'periods_guid', (SELECT recid FROM system_schema_tables WHERE element_name = 'finance_periods' AND element_schema = 'dbo'), 'element_guid'),
  ((SELECT recid FROM system_schema_tables WHERE element_name = 'finance_journals' AND element_schema = 'dbo'), 'ledgers_recid', (SELECT recid FROM system_schema_tables WHERE element_name = 'finance_ledgers' AND element_schema = 'dbo'), 'recid'),
  ((SELECT recid FROM system_schema_tables WHERE element_name = 'finance_journals' AND element_schema = 'dbo'), 'element_reversed_by', (SELECT recid FROM system_schema_tables WHERE element_name = 'finance_journals' AND element_schema = 'dbo'), 'recid'),
  ((SELECT recid FROM system_schema_tables WHERE element_name = 'finance_journals' AND element_schema = 'dbo'), 'element_reversal_of', (SELECT recid FROM system_schema_tables WHERE element_name = 'finance_journals' AND element_schema = 'dbo'), 'recid'),
  ((SELECT recid FROM system_schema_tables WHERE element_name = 'finance_journal_lines' AND element_schema = 'dbo'), 'journals_recid', (SELECT recid FROM system_schema_tables WHERE element_name = 'finance_journals' AND element_schema = 'dbo'), 'recid'),
  ((SELECT recid FROM system_schema_tables WHERE element_name = 'finance_journal_lines' AND element_schema = 'dbo'), 'accounts_guid', (SELECT recid FROM system_schema_tables WHERE element_name = 'finance_accounts' AND element_schema = 'dbo'), 'element_guid'),
  ((SELECT recid FROM system_schema_tables WHERE element_name = 'finance_journal_line_dimensions' AND element_schema = 'dbo'), 'lines_recid', (SELECT recid FROM system_schema_tables WHERE element_name = 'finance_journal_lines' AND element_schema = 'dbo'), 'recid'),
  ((SELECT recid FROM system_schema_tables WHERE element_name = 'finance_journal_line_dimensions' AND element_schema = 'dbo'), 'dimensions_recid', (SELECT recid FROM system_schema_tables WHERE element_name = 'finance_dimensions' AND element_schema = 'dbo'), 'recid');
