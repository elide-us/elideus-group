SET NOCOUNT ON;
GO

IF COL_LENGTH('dbo.finance_numbers', 'element_sequence_type') IS NULL
BEGIN
  ALTER TABLE [dbo].[finance_numbers]
    ADD [element_sequence_type] NVARCHAR(20) NOT NULL
      CONSTRAINT [DF_finance_numbers_element_sequence_type] DEFAULT ('continuous');
END;
GO

IF COL_LENGTH('dbo.finance_numbers', 'element_series_number') IS NULL
BEGIN
  ALTER TABLE [dbo].[finance_numbers]
    ADD [element_series_number] INT NOT NULL
      CONSTRAINT [DF_finance_numbers_element_series_number] DEFAULT ((1));
END;
GO

IF COL_LENGTH('dbo.finance_numbers', 'element_scope') IS NULL
BEGIN
  ALTER TABLE [dbo].[finance_numbers]
    ADD [element_scope] NVARCHAR(64) NULL;
END;
GO

UPDATE [dbo].[finance_numbers]
SET [element_sequence_type] = 'non_continuous',
    [element_series_number] = 1,
    [element_scope] = NULL,
    [element_modified_on] = SYSUTCDATETIME()
WHERE [element_prefix] = 'LOT';
GO

UPDATE [dbo].[finance_numbers]
SET [element_sequence_type] = 'continuous',
    [element_series_number] = 1,
    [element_scope] = NULL,
    [element_modified_on] = SYSUTCDATETIME()
WHERE [element_prefix] = 'JRN';
GO

UPDATE [dbo].[finance_numbers]
SET [element_series_number] = 0,
    [element_modified_on] = SYSUTCDATETIME()
WHERE [recid] = 12
  AND [element_prefix] = 'LOT'
  AND [element_account_number] = 'LOT-SEQ';
GO

IF EXISTS (
  SELECT 1
  FROM sys.indexes
  WHERE object_id = OBJECT_ID(N'dbo.finance_numbers')
    AND name = N'UQ_finance_numbers_account'
)
BEGIN
  DROP INDEX [UQ_finance_numbers_account] ON [dbo].[finance_numbers];
END;
GO

IF NOT EXISTS (
  SELECT 1
  FROM sys.indexes
  WHERE object_id = OBJECT_ID(N'dbo.finance_numbers')
    AND name = N'IX_finance_numbers_accounts_guid'
)
BEGIN
  CREATE INDEX [IX_finance_numbers_accounts_guid]
    ON [dbo].[finance_numbers] ([accounts_guid]);
END;
GO

IF NOT EXISTS (
  SELECT 1
  FROM sys.indexes
  WHERE object_id = OBJECT_ID(N'dbo.finance_numbers')
    AND name = N'UQ_finance_numbers_prefix_account_series'
)
BEGIN
  CREATE UNIQUE INDEX [UQ_finance_numbers_prefix_account_series]
    ON [dbo].[finance_numbers] ([element_prefix], [element_account_number], [element_series_number]);
END;
GO

DECLARE @finance_numbers_table_recid BIGINT;
SELECT @finance_numbers_table_recid = [recid]
FROM [dbo].[system_schema_tables]
WHERE [element_name] = 'finance_numbers'
  AND [element_schema] = 'dbo';

IF @finance_numbers_table_recid IS NULL
BEGIN
  THROW 52020, 'system_schema_tables entry for dbo.finance_numbers is missing.', 1;
END;

IF NOT EXISTS (
  SELECT 1
  FROM [dbo].[system_schema_columns]
  WHERE [tables_recid] = @finance_numbers_table_recid
    AND [element_name] = 'element_sequence_type'
)
BEGIN
  INSERT INTO [dbo].[system_schema_columns] (
    [tables_recid],
    [edt_recid],
    [element_name],
    [element_ordinal],
    [element_nullable],
    [element_default],
    [element_max_length],
    [element_is_primary_key],
    [element_is_identity]
  )
  SELECT
    @finance_numbers_table_recid,
    8,
    'element_sequence_type',
    ISNULL(MAX([element_ordinal]), 0) + 1,
    0,
    '(''continuous'')',
    20,
    0,
    0
  FROM [dbo].[system_schema_columns]
  WHERE [tables_recid] = @finance_numbers_table_recid;
END;

IF NOT EXISTS (
  SELECT 1
  FROM [dbo].[system_schema_columns]
  WHERE [tables_recid] = @finance_numbers_table_recid
    AND [element_name] = 'element_series_number'
)
BEGIN
  INSERT INTO [dbo].[system_schema_columns] (
    [tables_recid],
    [edt_recid],
    [element_name],
    [element_ordinal],
    [element_nullable],
    [element_default],
    [element_max_length],
    [element_is_primary_key],
    [element_is_identity]
  )
  SELECT
    @finance_numbers_table_recid,
    1,
    'element_series_number',
    ISNULL(MAX([element_ordinal]), 0) + 1,
    0,
    '((1))',
    NULL,
    0,
    0
  FROM [dbo].[system_schema_columns]
  WHERE [tables_recid] = @finance_numbers_table_recid;
END;

IF NOT EXISTS (
  SELECT 1
  FROM [dbo].[system_schema_columns]
  WHERE [tables_recid] = @finance_numbers_table_recid
    AND [element_name] = 'element_scope'
)
BEGIN
  INSERT INTO [dbo].[system_schema_columns] (
    [tables_recid],
    [edt_recid],
    [element_name],
    [element_ordinal],
    [element_nullable],
    [element_default],
    [element_max_length],
    [element_is_primary_key],
    [element_is_identity]
  )
  SELECT
    @finance_numbers_table_recid,
    8,
    'element_scope',
    ISNULL(MAX([element_ordinal]), 0) + 1,
    1,
    NULL,
    64,
    0,
    0
  FROM [dbo].[system_schema_columns]
  WHERE [tables_recid] = @finance_numbers_table_recid;
END;
GO

DELETE FROM [dbo].[system_schema_indexes]
WHERE [tables_recid] = (
    SELECT [recid]
    FROM [dbo].[system_schema_tables]
    WHERE [element_name] = 'finance_numbers'
      AND [element_schema] = 'dbo'
  )
  AND [element_name] IN (
    'UQ_finance_numbers_account',
    'IX_finance_numbers_accounts_guid',
    'UQ_finance_numbers_prefix_account_series'
  );
GO

INSERT INTO [dbo].[system_schema_indexes] (
  [tables_recid],
  [element_name],
  [element_columns],
  [element_is_unique]
)
SELECT
  t.[recid],
  seed.[element_name],
  seed.[element_columns],
  seed.[element_is_unique]
FROM [dbo].[system_schema_tables] t
CROSS JOIN (
  VALUES
    ('IX_finance_numbers_accounts_guid', 'accounts_guid', 0),
    ('UQ_finance_numbers_prefix_account_series', 'element_prefix,element_account_number,element_series_number', 1)
) seed([element_name], [element_columns], [element_is_unique])
WHERE t.[element_name] = 'finance_numbers'
  AND t.[element_schema] = 'dbo';
GO

INSERT INTO [dbo].[finance_status_codes] (
  [element_domain],
  [element_code],
  [element_name],
  [element_description],
  [element_status],
  [element_created_on],
  [element_modified_on]
)
SELECT
  seed.[element_domain],
  seed.[element_code],
  seed.[element_name],
  seed.[element_description],
  1,
  SYSUTCDATETIME(),
  SYSUTCDATETIME()
FROM (
  VALUES
    ('number_sequence', 0, 'inactive', 'Number sequence is inactive'),
    ('number_sequence', 1, 'active', 'Number sequence is active'),
    ('number_sequence_type', 1, 'continuous', 'Sequence allocates a strictly continuous series'),
    ('number_sequence_type', 2, 'non_continuous', 'Sequence allocates reserved number blocks')
) seed([element_domain], [element_code], [element_name], [element_description])
WHERE NOT EXISTS (
  SELECT 1
  FROM [dbo].[finance_status_codes] existing
  WHERE existing.[element_domain] = seed.[element_domain]
    AND existing.[element_code] = seed.[element_code]
);
GO

IF NOT EXISTS (SELECT 1 FROM [dbo].[finance_accounts] WHERE [element_number] = '5600')
BEGIN
  INSERT INTO [dbo].[finance_accounts] (
    [element_guid],
    [element_number],
    [element_name],
    [element_type],
    [element_parent],
    [is_posting],
    [element_status]
  )
  VALUES (NEWID(), '5600', 'Number Sequences', 4, '7C3B3F89-E616-45E1-B1A3-E392F3B5ABDF', 0, 1);
END;
GO

DECLARE @seq_parent_guid UNIQUEIDENTIFIER = (
  SELECT [element_guid]
  FROM [dbo].[finance_accounts]
  WHERE [element_number] = '5600'
);

IF NOT EXISTS (SELECT 1 FROM [dbo].[finance_accounts] WHERE [element_number] = '5610')
BEGIN
  INSERT INTO [dbo].[finance_accounts] (
    [element_guid],
    [element_number],
    [element_name],
    [element_type],
    [element_parent],
    [is_posting],
    [element_status]
  )
  VALUES (NEWID(), '5610', 'Journal Sequences', 4, @seq_parent_guid, 0, 1);
END;

IF NOT EXISTS (SELECT 1 FROM [dbo].[finance_accounts] WHERE [element_number] = '5620')
BEGIN
  INSERT INTO [dbo].[finance_accounts] (
    [element_guid],
    [element_number],
    [element_name],
    [element_type],
    [element_parent],
    [is_posting],
    [element_status]
  )
  VALUES (NEWID(), '5620', 'Lot Sequences', 4, @seq_parent_guid, 0, 1);
END;

IF NOT EXISTS (SELECT 1 FROM [dbo].[finance_accounts] WHERE [element_number] = '5630')
BEGIN
  INSERT INTO [dbo].[finance_accounts] (
    [element_guid],
    [element_number],
    [element_name],
    [element_type],
    [element_parent],
    [is_posting],
    [element_status]
  )
  VALUES (NEWID(), '5630', 'Transaction Sequences', 4, @seq_parent_guid, 0, 1);
END;
GO

UPDATE [dbo].[finance_numbers]
SET [element_sequence_status] = 0,
    [element_modified_on] = SYSUTCDATETIME()
WHERE [recid] IN (11, 12)
  AND [element_account_number] IN ('JRN-SEQ', 'LOT-SEQ');
GO

INSERT INTO [dbo].[finance_numbers] (
  [accounts_guid],
  [element_prefix],
  [element_account_number],
  [element_last_number],
  [element_max_number],
  [element_allocation_size],
  [element_reset_policy],
  [element_sequence_status],
  [element_sequence_type],
  [element_series_number],
  [element_scope],
  [element_pattern],
  [element_display_format],
  [element_created_on],
  [element_modified_on]
)
SELECT
  account_seed.[accounts_guid],
  seq.[element_prefix],
  seq.[element_account_number],
  0,
  99999999,
  seq.[element_allocation_size],
  'Never',
  1,
  seq.[element_sequence_type],
  1,
  seq.[element_scope],
  seq.[element_pattern],
  seq.[element_display_format],
  SYSUTCDATETIME(),
  SYSUTCDATETIME()
FROM (
  VALUES
    ('5610', 'JRN', 'JRN-GEN', 1, 'continuous', 'general', 'JRN-GEN-{series:03d}-{number:08d}', 'JRN-GEN-###-########'),
    ('5610', 'JRN', 'JRN-IMP', 1, 'continuous', 'billing_import', 'JRN-IMP-{series:03d}-{number:08d}', 'JRN-IMP-###-########'),
    ('5610', 'JRN', 'JRN-EQC', 1, 'continuous', 'equity_contribution', 'JRN-EQC-{series:03d}-{number:08d}', 'JRN-EQC-###-########'),
    ('5610', 'JRN', 'JRN-CRP', 1, 'continuous', 'credit_purchase', 'JRN-CRP-{series:03d}-{number:08d}', 'JRN-CRP-###-########'),
    ('5610', 'JRN', 'JRN-CRC', 1, 'continuous', 'credit_consumption', 'JRN-CRC-{series:03d}-{number:08d}', 'JRN-CRC-###-########'),
    ('5610', 'JRN', 'JRN-REV', 1, 'continuous', 'reversal', 'JRN-REV-{series:03d}-{number:08d}', 'JRN-REV-###-########'),
    ('5610', 'JRN', 'JRN-REF', 1, 'continuous', 'refund', 'JRN-REF-{series:03d}-{number:08d}', 'JRN-REF-###-########'),
    ('5620', 'LOT', 'LOT-SEQ', 10, 'non_continuous', 'credit_lot', 'LOT-{series:03d}-{number:08d}', 'LOT-###-########'),
    ('5630', 'TXN', 'TXN-SEQ', 10, 'non_continuous', 'payment', 'TXN-{series:03d}-{number:08d}', 'TXN-###-########'),
    ('5630', 'RCT', 'RCT-SEQ', 10, 'non_continuous', 'receipt', 'RCT-{series:03d}-{number:08d}', 'RCT-###-########'),
    ('5630', 'IMP', 'IMP-SEQ', 10, 'non_continuous', 'staging_import', 'IMP-{series:03d}-{number:08d}', 'IMP-###-########')
) seq([account_root], [element_prefix], [element_account_number], [element_allocation_size], [element_sequence_type], [element_scope], [element_pattern], [element_display_format])
CROSS APPLY (
  SELECT [element_guid] AS [accounts_guid]
  FROM [dbo].[finance_accounts]
  WHERE [element_number] = seq.[account_root]
) account_seed
WHERE NOT EXISTS (
  SELECT 1
  FROM [dbo].[finance_numbers] existing
  WHERE existing.[element_prefix] = seq.[element_prefix]
    AND existing.[element_account_number] = seq.[element_account_number]
    AND existing.[element_series_number] = 1
);
GO
