IF OBJECT_ID(N'dbo.finance_status_codes', N'U') IS NULL
BEGIN
  CREATE TABLE [dbo].[finance_status_codes] (
    [recid] BIGINT IDENTITY(1,1) NOT NULL,
    [element_domain] NVARCHAR(64) NOT NULL,
    [element_code] TINYINT NOT NULL,
    [element_name] NVARCHAR(64) NOT NULL,
    [element_description] NVARCHAR(512) NULL,
    [element_status] TINYINT NOT NULL CONSTRAINT [DF_finance_status_codes_element_status] DEFAULT (1),
    [element_created_on] DATETIMEOFFSET(7) NOT NULL CONSTRAINT [DF_finance_status_codes_element_created_on] DEFAULT (SYSUTCDATETIME()),
    [element_modified_on] DATETIMEOFFSET(7) NOT NULL CONSTRAINT [DF_finance_status_codes_element_modified_on] DEFAULT (SYSUTCDATETIME()),
    CONSTRAINT [PK_finance_status_codes] PRIMARY KEY ([recid]),
    CONSTRAINT [UQ_finance_status_codes_domain_code] UNIQUE ([element_domain], [element_code])
  );
END;
GO

INSERT INTO system_schema_tables (element_name, element_schema)
SELECT 'finance_status_codes', 'dbo'
WHERE NOT EXISTS (
  SELECT 1
  FROM system_schema_tables
  WHERE element_name = 'finance_status_codes'
    AND element_schema = 'dbo'
);
GO

DECLARE @finance_status_codes_table_recid BIGINT;
SELECT @finance_status_codes_table_recid = recid
FROM system_schema_tables
WHERE element_name = 'finance_status_codes'
  AND element_schema = 'dbo';

DELETE c
FROM system_schema_columns c
WHERE c.tables_recid = @finance_status_codes_table_recid;

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
  (@finance_status_codes_table_recid, 3, 'recid', 1, 0, NULL, NULL, 1, 1),
  (@finance_status_codes_table_recid, 8, 'element_domain', 2, 0, NULL, 64, 0, 0),
  (@finance_status_codes_table_recid, 11, 'element_code', 3, 0, NULL, NULL, 0, 0),
  (@finance_status_codes_table_recid, 8, 'element_name', 4, 0, NULL, 64, 0, 0),
  (@finance_status_codes_table_recid, 8, 'element_description', 5, 1, NULL, 512, 0, 0),
  (@finance_status_codes_table_recid, 11, 'element_status', 6, 0, '(1)', NULL, 0, 0),
  (@finance_status_codes_table_recid, 7, 'element_created_on', 7, 0, '(sysutcdatetime())', NULL, 0, 0),
  (@finance_status_codes_table_recid, 7, 'element_modified_on', 8, 0, '(sysutcdatetime())', NULL, 0, 0);
GO

DELETE i
FROM system_schema_indexes i
INNER JOIN system_schema_tables t ON t.recid = i.tables_recid
WHERE t.element_schema = 'dbo'
  AND t.element_name = 'finance_status_codes';

INSERT INTO system_schema_indexes (tables_recid, element_name, element_columns, element_is_unique)
VALUES
  (
    (SELECT recid FROM system_schema_tables WHERE element_name = 'finance_status_codes' AND element_schema = 'dbo'),
    'UQ_finance_status_codes_domain_code',
    'element_domain,element_code',
    1
  );
GO

DELETE fk
FROM system_schema_foreign_keys fk
INNER JOIN system_schema_tables t ON t.recid = fk.tables_recid
WHERE t.element_schema = 'dbo'
  AND t.element_name = 'finance_status_codes';
GO

INSERT INTO finance_status_codes (
  element_domain,
  element_code,
  element_name,
  element_description,
  element_status,
  element_created_on,
  element_modified_on
)
SELECT
  seed.element_domain,
  seed.element_code,
  seed.element_name,
  seed.element_description,
  1,
  SYSUTCDATETIME(),
  SYSUTCDATETIME()
FROM (
  VALUES
    ('import', 0, 'pending', 'Import created, awaiting processing'),
    ('import', 1, 'completed', 'Import processing completed successfully'),
    ('import', 2, 'failed', 'Import processing failed'),
    ('import', 3, 'promoted', 'Import promoted to journal'),
    ('import', 4, 'approved', 'Import approved for promotion'),
    ('import', 5, 'rejected', 'Import rejected'),
    ('journal', 0, 'draft', 'Journal created, not yet posted'),
    ('journal', 1, 'posted', 'Journal posted to general ledger'),
    ('journal', 2, 'reversed', 'Journal has been reversed'),
    ('period', 1, 'open', 'Period is open for posting'),
    ('period', 2, 'closed', 'Period is closed, no new postings'),
    ('period', 3, 'locked', 'Period is locked, no modifications'),
    ('period_close_type', 0, 'none', 'Not a closing period'),
    ('period_close_type', 1, 'quarterly', 'Quarterly closing period'),
    ('period_close_type', 2, 'annual', 'Annual closing period'),
    ('async_task', 0, 'queued', 'Task queued for processing'),
    ('async_task', 1, 'running', 'Task is currently running'),
    ('async_task', 2, 'polling', 'Task is polling for external result'),
    ('async_task', 3, 'waiting_callback', 'Task waiting for callback'),
    ('async_task', 4, 'completed', 'Task completed successfully'),
    ('async_task', 5, 'failed', 'Task failed'),
    ('async_task', 6, 'cancelled', 'Task was cancelled'),
    ('async_task', 7, 'timed_out', 'Task timed out'),
    ('element', 0, 'inactive', 'Record is inactive/deleted'),
    ('element', 1, 'active', 'Record is active'),
    ('credit_lot', 1, 'active', 'Credit lot is active and available'),
    ('credit_lot', 2, 'exhausted', 'Credit lot fully consumed'),
    ('credit_lot', 3, 'expired', 'Credit lot has expired')
) seed(element_domain, element_code, element_name, element_description)
WHERE NOT EXISTS (
  SELECT 1
  FROM finance_status_codes existing
  WHERE existing.element_domain = seed.element_domain
    AND existing.element_code = seed.element_code
);
GO
