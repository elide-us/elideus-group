SET NOCOUNT ON;
GO

IF COL_LENGTH('dbo.finance_numbers', 'element_max_number') IS NULL
BEGIN
  ALTER TABLE [dbo].[finance_numbers]
    ADD [element_max_number] BIGINT NULL;
END;
GO

IF COL_LENGTH('dbo.finance_numbers', 'element_sequence_status') IS NULL
BEGIN
  ALTER TABLE [dbo].[finance_numbers]
    ADD [element_sequence_status] TINYINT NOT NULL
      CONSTRAINT [DF_finance_numbers_element_sequence_status] DEFAULT ((1));
END;
GO


IF COL_LENGTH('dbo.finance_numbers', 'element_sequence_status') IS NOT NULL
  AND NOT EXISTS (
    SELECT 1
    FROM sys.default_constraints dc
    INNER JOIN sys.columns c
      ON c.object_id = dc.parent_object_id
     AND c.column_id = dc.parent_column_id
    WHERE dc.parent_object_id = OBJECT_ID(N'dbo.finance_numbers')
      AND c.name = 'element_sequence_status'
  )
BEGIN
  ALTER TABLE [dbo].[finance_numbers]
    ADD CONSTRAINT [DF_finance_numbers_element_sequence_status]
    DEFAULT ((1)) FOR [element_sequence_status];
END;
GO

BEGIN TRY
  IF COL_LENGTH('dbo.finance_numbers', 'element_display_format') IS NULL
  BEGIN
    THROW 52001, 'Column dbo.finance_numbers.element_display_format is required for element_max_number backfill.', 1;
  END;

  IF EXISTS (
    SELECT 1
    FROM [dbo].[finance_numbers] fn
    CROSS APPLY (
      SELECT hash_count = LEN(fn.[element_display_format]) - LEN(REPLACE(fn.[element_display_format], '#', ''))
    ) p
    WHERE fn.[element_display_format] IS NOT NULL
      AND LTRIM(RTRIM(fn.[element_display_format])) <> ''
      AND p.hash_count > 18
  )
  BEGIN
    DECLARE @malformed_recids NVARCHAR(400);

    SELECT @malformed_recids = STRING_AGG(CONVERT(NVARCHAR(30), x.[recid]), ',')
    FROM (
      SELECT TOP (10) fn.[recid]
      FROM [dbo].[finance_numbers] fn
      CROSS APPLY (
        SELECT hash_count = LEN(fn.[element_display_format]) - LEN(REPLACE(fn.[element_display_format], '#', ''))
      ) p
      WHERE fn.[element_display_format] IS NOT NULL
        AND LTRIM(RTRIM(fn.[element_display_format])) <> ''
        AND p.hash_count > 18
      ORDER BY fn.[recid]
    ) x;

    THROW 52002, CONCAT('Malformed element_display_format detected (more than 18 # placeholders). recids=', ISNULL(@malformed_recids, 'unknown')), 1;
  END;

  UPDATE fn
  SET [element_max_number] = CASE
    WHEN fn.[element_display_format] IS NULL OR LTRIM(RTRIM(fn.[element_display_format])) = '' THEN 999999
    WHEN p.hash_count = 0 THEN 999999
    ELSE CAST(POWER(CAST(10 AS DECIMAL(38, 0)), p.hash_count) - 1 AS BIGINT)
  END
  FROM [dbo].[finance_numbers] fn
  CROSS APPLY (
    SELECT hash_count = LEN(fn.[element_display_format]) - LEN(REPLACE(fn.[element_display_format], '#', ''))
  ) p
  WHERE fn.[element_max_number] IS NULL;
END TRY
BEGIN CATCH
  DECLARE @backfill_error NVARCHAR(4000) = ERROR_MESSAGE();
  THROW 52003, CONCAT('finance_numbers element_max_number backfill failed: ', @backfill_error), 1;
END CATCH;
GO

IF EXISTS (
  SELECT 1
  FROM [dbo].[finance_numbers]
  WHERE [element_max_number] IS NULL
)
BEGIN
  THROW 52004, 'Cannot enforce NOT NULL on dbo.finance_numbers.element_max_number because NULL values remain.', 1;
END;
GO

IF EXISTS (
  SELECT 1
  FROM sys.columns
  WHERE object_id = OBJECT_ID(N'dbo.finance_numbers')
    AND name = 'element_max_number'
    AND is_nullable = 1
)
BEGIN
  ALTER TABLE [dbo].[finance_numbers]
    ALTER COLUMN [element_max_number] BIGINT NOT NULL;
END;
GO

IF EXISTS (
  SELECT 1
  FROM sys.columns
  WHERE object_id = OBJECT_ID(N'dbo.finance_numbers')
    AND name = 'element_sequence_status'
    AND is_nullable = 1
)
BEGIN
  UPDATE [dbo].[finance_numbers]
  SET [element_sequence_status] = ISNULL([element_sequence_status], 1)
  WHERE [element_sequence_status] IS NULL;

  ALTER TABLE [dbo].[finance_numbers]
    ALTER COLUMN [element_sequence_status] TINYINT NOT NULL;
END;
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
SELECT @finance_numbers_table_recid = recid
FROM [dbo].[system_schema_tables]
WHERE [element_name] = 'finance_numbers'
  AND [element_schema] = 'dbo';

IF @finance_numbers_table_recid IS NULL
BEGIN
  THROW 52005, 'system_schema_tables entry for dbo.finance_numbers is missing.', 1;
END;

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
  SELECT
    @finance_numbers_table_recid,
    2,
    'element_max_number',
    ISNULL(MAX([element_ordinal]), 0) + 1,
    0,
    NULL,
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
  SELECT
    @finance_numbers_table_recid,
    11,
    'element_sequence_status',
    ISNULL(MAX([element_ordinal]), 0) + 1,
    0,
    '((1))',
    NULL,
    0,
    0
  FROM [dbo].[system_schema_columns]
  WHERE [tables_recid] = @finance_numbers_table_recid;
END;
GO

DELETE FROM [dbo].[system_schema_indexes]
WHERE [tables_recid] = (
    SELECT recid
    FROM [dbo].[system_schema_tables]
    WHERE [element_name] = 'finance_numbers'
      AND [element_schema] = 'dbo'
  )
  AND [element_name] = 'UQ_finance_numbers_account';

INSERT INTO [dbo].[system_schema_indexes] (
  [tables_recid],
  [element_name],
  [element_columns],
  [element_is_unique]
)
SELECT
  t.recid,
  'UQ_finance_numbers_account',
  'accounts_guid',
  1
FROM [dbo].[system_schema_tables] t
WHERE t.[element_name] = 'finance_numbers'
  AND t.[element_schema] = 'dbo'
  AND NOT EXISTS (
    SELECT 1
    FROM [dbo].[system_schema_indexes] i
    WHERE i.[tables_recid] = t.recid
      AND i.[element_name] = 'UQ_finance_numbers_account'
  );
GO
