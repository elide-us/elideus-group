IF OBJECT_ID(N'dbo.finance_staging_purge_log', N'U') IS NULL
BEGIN
  CREATE TABLE [dbo].[finance_staging_purge_log] (
    [recid] BIGINT IDENTITY(1,1) NOT NULL,
    [vendors_recid] BIGINT NOT NULL,
    [element_period_key] NVARCHAR(32) NOT NULL,
    [element_purged_keys] NVARCHAR(MAX) NOT NULL CONSTRAINT [DF_finance_staging_purge_log_element_purged_keys] DEFAULT ('{"batch_purged":[]}'),
    [element_purged_count] INT NOT NULL CONSTRAINT [DF_finance_staging_purge_log_element_purged_count] DEFAULT (0),
    [element_purged_on] DATETIMEOFFSET(7) NOT NULL CONSTRAINT [DF_finance_staging_purge_log_element_purged_on] DEFAULT (SYSUTCDATETIME()),
    [element_created_on] DATETIMEOFFSET(7) NOT NULL CONSTRAINT [DF_finance_staging_purge_log_element_created_on] DEFAULT (SYSUTCDATETIME()),
    [element_modified_on] DATETIMEOFFSET(7) NOT NULL CONSTRAINT [DF_finance_staging_purge_log_element_modified_on] DEFAULT (SYSUTCDATETIME()),
    CONSTRAINT [PK_finance_staging_purge_log] PRIMARY KEY ([recid]),
    CONSTRAINT [FK_finance_staging_purge_log_vendors_recid]
      FOREIGN KEY ([vendors_recid]) REFERENCES [dbo].[finance_vendors] ([recid]),
    CONSTRAINT [UQ_finance_staging_purge_log_vendor_period]
      UNIQUE ([vendors_recid], [element_period_key])
  );
END;
GO

IF NOT EXISTS (
  SELECT 1
  FROM sys.indexes
  WHERE [name] = N'IX_finance_staging_purge_log_vendors_recid'
    AND [object_id] = OBJECT_ID(N'dbo.finance_staging_purge_log')
)
BEGIN
  CREATE INDEX [IX_finance_staging_purge_log_vendors_recid]
    ON [dbo].[finance_staging_purge_log] ([vendors_recid]);
END;
GO

INSERT INTO system_schema_tables (element_name, element_schema)
SELECT 'finance_staging_purge_log', 'dbo'
WHERE NOT EXISTS (
  SELECT 1
  FROM system_schema_tables
  WHERE element_name = 'finance_staging_purge_log'
    AND element_schema = 'dbo'
);
GO

DECLARE @purge_log_table_recid BIGINT;
SELECT @purge_log_table_recid = recid
FROM system_schema_tables
WHERE element_name = 'finance_staging_purge_log'
  AND element_schema = 'dbo';

DELETE c
FROM system_schema_columns c
WHERE c.tables_recid = @purge_log_table_recid;

INSERT INTO system_schema_columns (
  tables_recid,
  edt_recid,
  element_name,
  element_ordinal,
  element_nullable,
  element_default,
  element_max_length,
  element_is_primary_key,
  element_is_identity
)
VALUES
  (@purge_log_table_recid, 3, 'recid', 1, 0, NULL, NULL, 1, 1),
  (@purge_log_table_recid, 2, 'vendors_recid', 2, 0, NULL, NULL, 0, 0),
  (@purge_log_table_recid, 8, 'element_period_key', 3, 0, NULL, 32, 0, 0),
  (@purge_log_table_recid, 9, 'element_purged_keys', 4, 0, '(''{"batch_purged":[]}'')', NULL, 0, 0),
  (@purge_log_table_recid, 1, 'element_purged_count', 5, 0, '(0)', NULL, 0, 0),
  (@purge_log_table_recid, 7, 'element_purged_on', 6, 0, '(sysutcdatetime())', NULL, 0, 0),
  (@purge_log_table_recid, 7, 'element_created_on', 7, 0, '(sysutcdatetime())', NULL, 0, 0),
  (@purge_log_table_recid, 7, 'element_modified_on', 8, 0, '(sysutcdatetime())', NULL, 0, 0);
GO

DELETE i
FROM system_schema_indexes i
INNER JOIN system_schema_tables t ON t.recid = i.tables_recid
WHERE t.element_schema = 'dbo'
  AND t.element_name = 'finance_staging_purge_log';

INSERT INTO system_schema_indexes (tables_recid, element_name, element_columns, element_is_unique)
VALUES
  ((SELECT recid FROM system_schema_tables WHERE element_name = 'finance_staging_purge_log' AND element_schema = 'dbo'), 'IX_finance_staging_purge_log_vendors_recid', 'vendors_recid', 0),
  ((SELECT recid FROM system_schema_tables WHERE element_name = 'finance_staging_purge_log' AND element_schema = 'dbo'), 'UQ_finance_staging_purge_log_vendor_period', 'vendors_recid,element_period_key', 1);
GO

DELETE fk
FROM system_schema_foreign_keys fk
INNER JOIN system_schema_tables t ON t.recid = fk.tables_recid
WHERE t.element_schema = 'dbo'
  AND t.element_name = 'finance_staging_purge_log';

INSERT INTO system_schema_foreign_keys (
  tables_recid,
  element_column_name,
  referenced_tables_recid,
  element_referenced_column
)
VALUES
  (
    (SELECT recid FROM system_schema_tables WHERE element_name = 'finance_staging_purge_log' AND element_schema = 'dbo'),
    'vendors_recid',
    (SELECT recid FROM system_schema_tables WHERE element_name = 'finance_vendors' AND element_schema = 'dbo'),
    'recid'
  );
GO
