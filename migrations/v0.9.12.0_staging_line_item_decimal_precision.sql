IF NOT EXISTS (
  SELECT 1
  FROM system_edt_mappings
  WHERE element_name = 'DECIMAL_28_12'
)
BEGIN
  INSERT INTO system_edt_mappings (
    element_name,
    element_mssql_type,
    element_postgresql_type,
    element_mysql_type,
    element_python_type,
    element_odbc_type_code,
    element_max_length,
    element_notes
  )
  VALUES (
    'DECIMAL_28_12',
    'decimal(28,12)',
    'numeric(28,12)',
    'decimal(28,12)',
    'Decimal',
    3,
    28,
    'High-precision staging decimal. 28 digits total, 12 after decimal. Used in staging tables to preserve full provider precision before GL quantization.'
  );
END;
GO

IF EXISTS (
  SELECT 1
  FROM sys.columns
  WHERE object_id = OBJECT_ID(N'dbo.finance_staging_line_items')
    AND name = 'element_quantity'
    AND ([precision] <> 28 OR scale <> 12)
)
BEGIN
  ALTER TABLE [dbo].[finance_staging_line_items]
  ALTER COLUMN [element_quantity] DECIMAL(28,12) NULL;
END;
GO

IF EXISTS (
  SELECT 1
  FROM sys.columns
  WHERE object_id = OBJECT_ID(N'dbo.finance_staging_line_items')
    AND name = 'element_unit_price'
    AND ([precision] <> 28 OR scale <> 12)
)
BEGIN
  ALTER TABLE [dbo].[finance_staging_line_items]
  ALTER COLUMN [element_unit_price] DECIMAL(28,12) NULL;
END;
GO

IF EXISTS (
  SELECT 1
  FROM sys.columns
  WHERE object_id = OBJECT_ID(N'dbo.finance_staging_line_items')
    AND name = 'element_amount'
    AND ([precision] <> 28 OR scale <> 12)
)
BEGIN
  ALTER TABLE [dbo].[finance_staging_line_items]
  ALTER COLUMN [element_amount] DECIMAL(28,12) NOT NULL;
END;
GO

UPDATE c
SET c.edt_recid = m.recid
FROM system_schema_columns AS c
INNER JOIN system_schema_tables AS t
  ON t.recid = c.tables_recid
INNER JOIN system_edt_mappings AS m
  ON m.element_name = 'DECIMAL_28_12'
WHERE t.element_schema = 'dbo'
  AND t.element_name = 'finance_staging_line_items'
  AND c.element_name IN ('element_quantity', 'element_unit_price', 'element_amount')
  AND c.edt_recid <> m.recid;
GO
