SET NOCOUNT ON;
GO

UPDATE [dbo].[finance_numbers]
SET [element_max_number] = 999999,
    [element_modified_on] = SYSUTCDATETIME()
WHERE [element_max_number] IS NULL
   OR [element_max_number] = 0;
GO

IF EXISTS (
  SELECT 1 FROM sys.indexes
  WHERE object_id = OBJECT_ID(N'dbo.finance_numbers')
    AND name = N'UQ_finance_numbers_account'
    AND has_filter = 0
)
BEGIN
  DROP INDEX [UQ_finance_numbers_account] ON [dbo].[finance_numbers];
END;
GO

IF NOT EXISTS (
  SELECT 1 FROM sys.indexes
  WHERE object_id = OBJECT_ID(N'dbo.finance_numbers')
    AND name = N'UQ_finance_numbers_account'
    AND is_unique = 1
    AND has_filter = 1
)
BEGIN
  CREATE UNIQUE INDEX [UQ_finance_numbers_account]
    ON [dbo].[finance_numbers] ([accounts_guid])
    WHERE [element_sequence_status] = 1;
END;
GO

DECLARE @finance_numbers_table_recid BIGINT;
SELECT @finance_numbers_table_recid = [recid]
FROM [dbo].[system_schema_tables]
WHERE [element_name] = 'finance_numbers'
  AND [element_schema] = 'dbo';

IF NOT EXISTS (
  SELECT 1
  FROM [dbo].[system_schema_columns]
  WHERE [tables_recid] = @finance_numbers_table_recid
    AND [element_name] = 'element_max_number'
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
  VALUES (
    @finance_numbers_table_recid,
    2,
    'element_max_number',
    12,
    0,
    NULL,
    NULL,
    0,
    0
  );
END;
GO

DECLARE @finance_numbers_table_recid BIGINT;
SELECT @finance_numbers_table_recid = [recid]
FROM [dbo].[system_schema_tables]
WHERE [element_name] = 'finance_numbers'
  AND [element_schema] = 'dbo';

IF NOT EXISTS (
  SELECT 1
  FROM [dbo].[system_schema_columns]
  WHERE [tables_recid] = @finance_numbers_table_recid
    AND [element_name] = 'element_sequence_status'
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
  VALUES (
    @finance_numbers_table_recid,
    11,
    'element_sequence_status',
    13,
    0,
    '((1))',
    NULL,
    0,
    0
  );
END;
GO

DECLARE @finance_numbers_table_recid BIGINT;
SELECT @finance_numbers_table_recid = [recid]
FROM [dbo].[system_schema_tables]
WHERE [element_name] = 'finance_numbers'
  AND [element_schema] = 'dbo';

DELETE FROM [dbo].[system_schema_indexes]
WHERE [tables_recid] = @finance_numbers_table_recid
  AND [element_name] = 'UQ_finance_numbers_account';
GO

DECLARE @finance_numbers_table_recid BIGINT;
SELECT @finance_numbers_table_recid = [recid]
FROM [dbo].[system_schema_tables]
WHERE [element_name] = 'finance_numbers'
  AND [element_schema] = 'dbo';

INSERT INTO [dbo].[system_schema_indexes] (
  [tables_recid],
  [element_name],
  [element_columns],
  [element_is_unique]
)
SELECT
  @finance_numbers_table_recid,
  'UQ_finance_numbers_account',
  'accounts_guid',
  1
WHERE @finance_numbers_table_recid IS NOT NULL
  AND NOT EXISTS (
    SELECT 1
    FROM [dbo].[system_schema_indexes]
    WHERE [tables_recid] = @finance_numbers_table_recid
      AND [element_name] = 'UQ_finance_numbers_account'
  );
GO
