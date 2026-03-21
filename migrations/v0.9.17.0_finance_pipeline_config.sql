IF OBJECT_ID(N'dbo.finance_pipeline_config', N'U') IS NULL
BEGIN
  CREATE TABLE [dbo].[finance_pipeline_config] (
    [recid] BIGINT IDENTITY(1,1) NOT NULL,
    [element_pipeline] NVARCHAR(64) NOT NULL,
    [element_key] NVARCHAR(128) NOT NULL,
    [element_value] NVARCHAR(512) NOT NULL,
    [element_description] NVARCHAR(512) NULL,
    [element_status] TINYINT NOT NULL CONSTRAINT [DF_finance_pipeline_config_element_status] DEFAULT (1),
    [element_created_on] DATETIMEOFFSET(7) NOT NULL CONSTRAINT [DF_finance_pipeline_config_element_created_on] DEFAULT (SYSUTCDATETIME()),
    [element_modified_on] DATETIMEOFFSET(7) NOT NULL CONSTRAINT [DF_finance_pipeline_config_element_modified_on] DEFAULT (SYSUTCDATETIME()),
    CONSTRAINT [PK_finance_pipeline_config] PRIMARY KEY ([recid]),
    CONSTRAINT [UQ_finance_pipeline_config_pipeline_key] UNIQUE ([element_pipeline], [element_key])
  );
END;
GO

INSERT INTO system_schema_tables (element_name, element_schema)
SELECT 'finance_pipeline_config', 'dbo'
WHERE NOT EXISTS (
  SELECT 1
  FROM system_schema_tables
  WHERE element_name = 'finance_pipeline_config'
    AND element_schema = 'dbo'
);
GO

DECLARE @finance_pipeline_config_table_recid BIGINT;
SELECT @finance_pipeline_config_table_recid = recid
FROM system_schema_tables
WHERE element_name = 'finance_pipeline_config'
  AND element_schema = 'dbo';

DELETE c
FROM system_schema_columns c
WHERE c.tables_recid = @finance_pipeline_config_table_recid;

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
  (@finance_pipeline_config_table_recid, 3, 'recid', 1, 0, NULL, NULL, 1, 1),
  (@finance_pipeline_config_table_recid, 8, 'element_pipeline', 2, 0, NULL, 64, 0, 0),
  (@finance_pipeline_config_table_recid, 8, 'element_key', 3, 0, NULL, 128, 0, 0),
  (@finance_pipeline_config_table_recid, 8, 'element_value', 4, 0, NULL, 512, 0, 0),
  (@finance_pipeline_config_table_recid, 8, 'element_description', 5, 1, NULL, 512, 0, 0),
  (@finance_pipeline_config_table_recid, 11, 'element_status', 6, 0, '(1)', NULL, 0, 0),
  (@finance_pipeline_config_table_recid, 7, 'element_created_on', 7, 0, '(sysutcdatetime())', NULL, 0, 0),
  (@finance_pipeline_config_table_recid, 7, 'element_modified_on', 8, 0, '(sysutcdatetime())', NULL, 0, 0);
GO

DELETE i
FROM system_schema_indexes i
INNER JOIN system_schema_tables t ON t.recid = i.tables_recid
WHERE t.element_schema = 'dbo'
  AND t.element_name = 'finance_pipeline_config';

INSERT INTO system_schema_indexes (tables_recid, element_name, element_columns, element_is_unique)
VALUES
  (
    (SELECT recid FROM system_schema_tables WHERE element_name = 'finance_pipeline_config' AND element_schema = 'dbo'),
    'UQ_finance_pipeline_config_pipeline_key',
    'element_pipeline,element_key',
    1
  );
GO

DELETE fk
FROM system_schema_foreign_keys fk
INNER JOIN system_schema_tables t ON t.recid = fk.tables_recid
WHERE t.element_schema = 'dbo'
  AND t.element_name = 'finance_pipeline_config';
GO

INSERT INTO finance_pipeline_config (
  element_pipeline,
  element_key,
  element_value,
  element_description,
  element_status,
  element_created_on,
  element_modified_on
)
SELECT
  seed.element_pipeline,
  seed.element_key,
  seed.element_value,
  seed.element_description,
  1,
  SYSUTCDATETIME(),
  SYSUTCDATETIME()
FROM (
  VALUES
    ('billing_import', 'ap_account_number', '2200', 'Accounts payable contra account for billing imports'),
    ('billing_import', 'default_dimension_recids', '[15,4]', 'Default dimension recids applied to billing import journal lines'),
    ('billing_import', 'source_type_invoice', 'azure_invoice', 'Source type string for Azure invoice imports'),
    ('billing_import', 'source_type_usage', 'azure_billing_import', 'Source type string for Azure usage/cost imports'),
    ('credit_consumption', 'deferred_revenue_account_number', '2100', 'Deferred revenue account debited on credit consumption'),
    ('credit_consumption', 'revenue_account_number', '4010', 'Revenue account credited on credit consumption'),
    ('credit_purchase', 'cash_account_number', '1100', 'Cash account debited on credit purchase'),
    ('credit_purchase', 'deferred_revenue_account_number', '2100', 'Deferred revenue account credited on credit purchase')
) seed(element_pipeline, element_key, element_value, element_description)
WHERE NOT EXISTS (
  SELECT 1
  FROM finance_pipeline_config existing
  WHERE existing.element_pipeline = seed.element_pipeline
    AND existing.element_key = seed.element_key
);
GO
