IF COL_LENGTH('dbo.finance_staging_line_items', 'element_record_type') IS NULL
BEGIN
  ALTER TABLE [dbo].[finance_staging_line_items]
  ADD [element_record_type] NVARCHAR(20) NOT NULL CONSTRAINT [DF_finance_staging_line_items_element_record_type] DEFAULT ('usage');
END;
GO

IF OBJECT_ID(N'dbo.finance_staging_azure_invoices', N'U') IS NULL
BEGIN
  CREATE TABLE [dbo].[finance_staging_azure_invoices] (
    [recid] BIGINT IDENTITY(1,1) NOT NULL,
    [imports_recid] BIGINT NOT NULL,
    [element_invoice_name] NVARCHAR(128) NOT NULL,
    [element_invoice_date] DATE NULL,
    [element_invoice_period_start] DATE NULL,
    [element_invoice_period_end] DATE NULL,
    [element_due_date] DATE NULL,
    [element_invoice_type] NVARCHAR(64) NULL,
    [element_status] NVARCHAR(32) NULL,
    [element_billed_amount] DECIMAL(19,5) NULL,
    [element_amount_due] DECIMAL(19,5) NULL,
    [element_currency] NVARCHAR(10) NULL,
    [element_subscription_id] NVARCHAR(256) NULL,
    [element_subscription_name] NVARCHAR(512) NULL,
    [element_purchase_order] NVARCHAR(256) NULL,
    [element_raw_json] NVARCHAR(MAX) NULL,
    [element_created_on] DATETIMEOFFSET(7) NOT NULL DEFAULT (SYSUTCDATETIME()),
    [element_modified_on] DATETIMEOFFSET(7) NOT NULL DEFAULT (SYSUTCDATETIME()),
    CONSTRAINT [PK_finance_staging_azure_invoices] PRIMARY KEY ([recid]),
    CONSTRAINT [FK_finance_staging_azure_invoices_imports_recid] FOREIGN KEY ([imports_recid])
      REFERENCES [dbo].[finance_staging_imports] ([recid]),
    CONSTRAINT [UQ_finance_staging_azure_invoices_element_invoice_name] UNIQUE ([element_invoice_name])
  );
END;
GO

IF NOT EXISTS (
  SELECT 1
  FROM sys.indexes
  WHERE [name] = N'IX_finance_staging_azure_invoices_imports_recid'
    AND [object_id] = OBJECT_ID(N'dbo.finance_staging_azure_invoices')
)
BEGIN
  CREATE INDEX [IX_finance_staging_azure_invoices_imports_recid]
    ON [dbo].[finance_staging_azure_invoices] ([imports_recid]);
END;

IF NOT EXISTS (
  SELECT 1
  FROM sys.indexes
  WHERE [name] = N'IX_finance_staging_azure_invoices_invoice_date'
    AND [object_id] = OBJECT_ID(N'dbo.finance_staging_azure_invoices')
)
BEGIN
  CREATE INDEX [IX_finance_staging_azure_invoices_invoice_date]
    ON [dbo].[finance_staging_azure_invoices] ([element_invoice_date]);
END;
GO

INSERT INTO system_schema_tables (element_name, element_schema)
SELECT v.element_name, v.element_schema
FROM (VALUES
  ('finance_staging_azure_invoices', 'dbo')
) v(element_name, element_schema)
WHERE NOT EXISTS (
  SELECT 1
  FROM system_schema_tables t
  WHERE t.element_name = v.element_name
    AND t.element_schema = v.element_schema
);
GO

DECLARE @line_items_table_recid BIGINT;
SELECT @line_items_table_recid = recid
FROM system_schema_tables
WHERE element_name = 'finance_staging_line_items'
  AND element_schema = 'dbo';

IF NOT EXISTS (
  SELECT 1
  FROM system_schema_columns
  WHERE tables_recid = @line_items_table_recid
    AND element_name = 'element_record_type'
)
BEGIN
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
    (@line_items_table_recid, 8, 'element_record_type', 14, 0, '(''usage'')', 20, 0, 0);
END;
GO

DECLARE @azure_invoices_table_recid BIGINT;
SELECT @azure_invoices_table_recid = recid
FROM system_schema_tables
WHERE element_name = 'finance_staging_azure_invoices'
  AND element_schema = 'dbo';

DELETE c
FROM system_schema_columns c
WHERE c.tables_recid = @azure_invoices_table_recid;

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
  (@azure_invoices_table_recid, 3, 'recid', 1, 0, NULL, NULL, 1, 1),
  (@azure_invoices_table_recid, 2, 'imports_recid', 2, 0, NULL, NULL, 0, 0),
  (@azure_invoices_table_recid, 8, 'element_invoice_name', 3, 0, NULL, 128, 0, 0),
  (@azure_invoices_table_recid, 12, 'element_invoice_date', 4, 1, NULL, NULL, 0, 0),
  (@azure_invoices_table_recid, 12, 'element_invoice_period_start', 5, 1, NULL, NULL, 0, 0),
  (@azure_invoices_table_recid, 12, 'element_invoice_period_end', 6, 1, NULL, NULL, 0, 0),
  (@azure_invoices_table_recid, 12, 'element_due_date', 7, 1, NULL, NULL, 0, 0),
  (@azure_invoices_table_recid, 8, 'element_invoice_type', 8, 1, NULL, 64, 0, 0),
  (@azure_invoices_table_recid, 8, 'element_status', 9, 1, NULL, 32, 0, 0),
  (@azure_invoices_table_recid, 13, 'element_billed_amount', 10, 1, NULL, NULL, 0, 0),
  (@azure_invoices_table_recid, 13, 'element_amount_due', 11, 1, NULL, NULL, 0, 0),
  (@azure_invoices_table_recid, 8, 'element_currency', 12, 1, NULL, 10, 0, 0),
  (@azure_invoices_table_recid, 8, 'element_subscription_id', 13, 1, NULL, 256, 0, 0),
  (@azure_invoices_table_recid, 8, 'element_subscription_name', 14, 1, NULL, 512, 0, 0),
  (@azure_invoices_table_recid, 8, 'element_purchase_order', 15, 1, NULL, 256, 0, 0),
  (@azure_invoices_table_recid, 9, 'element_raw_json', 16, 1, NULL, NULL, 0, 0),
  (@azure_invoices_table_recid, 7, 'element_created_on', 17, 0, '(sysutcdatetime())', NULL, 0, 0),
  (@azure_invoices_table_recid, 7, 'element_modified_on', 18, 0, '(sysutcdatetime())', NULL, 0, 0);
GO

DELETE i
FROM system_schema_indexes i
INNER JOIN system_schema_tables t ON t.recid = i.tables_recid
WHERE t.element_schema = 'dbo'
  AND t.element_name = 'finance_staging_azure_invoices';

INSERT INTO system_schema_indexes (tables_recid, element_name, element_columns, element_is_unique)
VALUES
  ((SELECT recid FROM system_schema_tables WHERE element_name = 'finance_staging_azure_invoices' AND element_schema = 'dbo'), 'IX_finance_staging_azure_invoices_imports_recid', 'imports_recid', 0),
  ((SELECT recid FROM system_schema_tables WHERE element_name = 'finance_staging_azure_invoices' AND element_schema = 'dbo'), 'UQ_finance_staging_azure_invoices_element_invoice_name', 'element_invoice_name', 1),
  ((SELECT recid FROM system_schema_tables WHERE element_name = 'finance_staging_azure_invoices' AND element_schema = 'dbo'), 'IX_finance_staging_azure_invoices_invoice_date', 'element_invoice_date', 0);
GO

DELETE fk
FROM system_schema_foreign_keys fk
INNER JOIN system_schema_tables t ON t.recid = fk.tables_recid
WHERE t.element_schema = 'dbo'
  AND t.element_name = 'finance_staging_azure_invoices';

INSERT INTO system_schema_foreign_keys (
  tables_recid,
  element_column_name,
  referenced_tables_recid,
  element_referenced_column
)
VALUES
  (
    (SELECT recid FROM system_schema_tables WHERE element_name = 'finance_staging_azure_invoices' AND element_schema = 'dbo'),
    'imports_recid',
    (SELECT recid FROM system_schema_tables WHERE element_name = 'finance_staging_imports' AND element_schema = 'dbo'),
    'recid'
  );
GO
