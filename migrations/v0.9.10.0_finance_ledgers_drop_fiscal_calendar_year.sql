IF COL_LENGTH('dbo.finance_ledgers', 'element_fiscal_calendar_year') IS NOT NULL
BEGIN
  DECLARE @drop_finance_ledgers_fiscal_year_default_sql NVARCHAR(MAX);

  SELECT @drop_finance_ledgers_fiscal_year_default_sql =
    N'ALTER TABLE [dbo].[finance_ledgers] DROP CONSTRAINT [' + dc.name + N'];'
  FROM sys.default_constraints dc
  INNER JOIN sys.columns c
    ON c.default_object_id = dc.object_id
  INNER JOIN sys.tables t
    ON t.object_id = c.object_id
  INNER JOIN sys.schemas s
    ON s.schema_id = t.schema_id
  WHERE s.name = 'dbo'
    AND t.name = 'finance_ledgers'
    AND c.name = 'element_fiscal_calendar_year';

  IF @drop_finance_ledgers_fiscal_year_default_sql IS NOT NULL
  BEGIN
    EXEC sp_executesql @drop_finance_ledgers_fiscal_year_default_sql;
  END;

  ALTER TABLE [dbo].[finance_ledgers]
    DROP COLUMN [element_fiscal_calendar_year];
END;
GO

DECLARE @finance_ledgers_table_recid BIGINT = (
  SELECT recid
  FROM [dbo].[system_schema_tables]
  WHERE element_name = 'finance_ledgers'
    AND element_schema = 'dbo'
);

IF @finance_ledgers_table_recid IS NOT NULL
BEGIN
  DELETE FROM [dbo].[system_schema_columns]
  WHERE tables_recid = @finance_ledgers_table_recid
    AND element_name = 'element_fiscal_calendar_year';

  UPDATE reflection_columns
  SET reflection_columns.element_ordinal = table_columns.column_id
  FROM [dbo].[system_schema_columns] reflection_columns
  INNER JOIN sys.tables t
    ON t.name = 'finance_ledgers'
  INNER JOIN sys.schemas s
    ON s.schema_id = t.schema_id
    AND s.name = 'dbo'
  INNER JOIN sys.columns table_columns
    ON table_columns.object_id = t.object_id
    AND table_columns.name = reflection_columns.element_name
  WHERE reflection_columns.tables_recid = @finance_ledgers_table_recid;
END;
GO
