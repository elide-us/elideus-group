IF OBJECT_ID(N'dbo.finance_products', N'U') IS NULL
BEGIN
  CREATE TABLE [dbo].[finance_products] (
    [recid] BIGINT IDENTITY(1,1) NOT NULL,
    [element_sku] NVARCHAR(32) NOT NULL,
    [element_name] NVARCHAR(200) NOT NULL,
    [element_description] NVARCHAR(512) NULL,
    [element_category] NVARCHAR(64) NOT NULL,
    [element_price] DECIMAL(19,5) NOT NULL CONSTRAINT [DF_finance_products_element_price] DEFAULT ((0)),
    [element_currency] NVARCHAR(3) NOT NULL CONSTRAINT [DF_finance_products_element_currency] DEFAULT ('USD'),
    [element_credits] INT NOT NULL CONSTRAINT [DF_finance_products_element_credits] DEFAULT ((0)),
    [element_enablement_key] NVARCHAR(64) NULL,
    [element_is_recurring] BIT NOT NULL CONSTRAINT [DF_finance_products_element_is_recurring] DEFAULT ((0)),
    [element_sort_order] INT NOT NULL CONSTRAINT [DF_finance_products_element_sort_order] DEFAULT ((0)),
    [element_status] TINYINT NOT NULL CONSTRAINT [DF_finance_products_element_status] DEFAULT ((1)),
    [element_created_on] DATETIMEOFFSET(7) NOT NULL CONSTRAINT [DF_finance_products_element_created_on] DEFAULT (SYSUTCDATETIME()),
    [element_modified_on] DATETIMEOFFSET(7) NOT NULL CONSTRAINT [DF_finance_products_element_modified_on] DEFAULT (SYSUTCDATETIME()),
    CONSTRAINT [PK_finance_products] PRIMARY KEY ([recid])
  );
END
GO

IF NOT EXISTS (
  SELECT 1
  FROM sys.indexes
  WHERE object_id = OBJECT_ID(N'[dbo].[finance_products]')
    AND name = N'UQ_finance_products_sku'
)
BEGIN
  CREATE UNIQUE INDEX [UQ_finance_products_sku]
    ON [dbo].[finance_products] ([element_sku]);
END
GO

IF OBJECT_ID(N'dbo.finance_product_journal_config', N'U') IS NULL
BEGIN
  CREATE TABLE [dbo].[finance_product_journal_config] (
    [recid] BIGINT IDENTITY(1,1) NOT NULL,
    [element_category] NVARCHAR(64) NOT NULL,
    [element_journal_scope] NVARCHAR(64) NOT NULL,
    [journals_recid] BIGINT NOT NULL,
    [periods_guid] UNIQUEIDENTIFIER NOT NULL,
    [element_approved_by] NVARCHAR(128) NULL,
    [element_approved_on] DATETIMEOFFSET(7) NULL,
    [element_activated_by] NVARCHAR(128) NULL,
    [element_activated_on] DATETIMEOFFSET(7) NULL,
    [element_status] TINYINT NOT NULL CONSTRAINT [DF_finance_product_journal_config_element_status] DEFAULT ((0)),
    [element_created_on] DATETIMEOFFSET(7) NOT NULL CONSTRAINT [DF_finance_product_journal_config_element_created_on] DEFAULT (SYSUTCDATETIME()),
    [element_modified_on] DATETIMEOFFSET(7) NOT NULL CONSTRAINT [DF_finance_product_journal_config_element_modified_on] DEFAULT (SYSUTCDATETIME()),
    CONSTRAINT [PK_finance_product_journal_config] PRIMARY KEY ([recid])
  );
END
GO

IF NOT EXISTS (
  SELECT 1 FROM sys.foreign_keys WHERE name = N'FK_product_journal_config_journals'
)
BEGIN
  ALTER TABLE [dbo].[finance_product_journal_config]
  ADD CONSTRAINT [FK_product_journal_config_journals]
    FOREIGN KEY ([journals_recid]) REFERENCES [dbo].[finance_journals] ([recid]);
END
GO

IF NOT EXISTS (
  SELECT 1 FROM sys.foreign_keys WHERE name = N'FK_product_journal_config_periods'
)
BEGIN
  ALTER TABLE [dbo].[finance_product_journal_config]
  ADD CONSTRAINT [FK_product_journal_config_periods]
    FOREIGN KEY ([periods_guid]) REFERENCES [dbo].[finance_periods] ([element_guid]);
END
GO

IF NOT EXISTS (
  SELECT 1
  FROM sys.indexes
  WHERE object_id = OBJECT_ID(N'[dbo].[finance_product_journal_config]')
    AND name = N'UQ_product_journal_config_category_period'
)
BEGIN
  CREATE UNIQUE INDEX [UQ_product_journal_config_category_period]
    ON [dbo].[finance_product_journal_config] ([element_category], [periods_guid])
    WHERE [element_status] IN (1, 2);
END
GO

INSERT INTO system_schema_tables (element_name, element_schema)
SELECT 'finance_products', 'dbo'
WHERE NOT EXISTS (
  SELECT 1 FROM system_schema_tables WHERE element_name = 'finance_products' AND element_schema = 'dbo'
);
GO

INSERT INTO system_schema_tables (element_name, element_schema)
SELECT 'finance_product_journal_config', 'dbo'
WHERE NOT EXISTS (
  SELECT 1 FROM system_schema_tables WHERE element_name = 'finance_product_journal_config' AND element_schema = 'dbo'
);
GO

DECLARE @finance_products_table_recid BIGINT = (
  SELECT recid FROM system_schema_tables WHERE element_name = 'finance_products' AND element_schema = 'dbo'
);
DELETE FROM system_schema_columns WHERE tables_recid = @finance_products_table_recid;
INSERT INTO system_schema_columns
  (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
VALUES
  (@finance_products_table_recid, 3, 'recid', 1, 0, NULL, NULL, 1, 1),
  (@finance_products_table_recid, 8, 'element_sku', 2, 0, NULL, 32, 0, 0),
  (@finance_products_table_recid, 8, 'element_name', 3, 0, NULL, 200, 0, 0),
  (@finance_products_table_recid, 8, 'element_description', 4, 1, NULL, 512, 0, 0),
  (@finance_products_table_recid, 8, 'element_category', 5, 0, NULL, 64, 0, 0),
  (@finance_products_table_recid, 13, 'element_price', 6, 0, '((0))', NULL, 0, 0),
  (@finance_products_table_recid, 8, 'element_currency', 7, 0, '(''USD'')', 3, 0, 0),
  (@finance_products_table_recid, 1, 'element_credits', 8, 0, '((0))', NULL, 0, 0),
  (@finance_products_table_recid, 8, 'element_enablement_key', 9, 1, NULL, 64, 0, 0),
  (@finance_products_table_recid, 5, 'element_is_recurring', 10, 0, '((0))', NULL, 0, 0),
  (@finance_products_table_recid, 1, 'element_sort_order', 11, 0, '((0))', NULL, 0, 0),
  (@finance_products_table_recid, 11, 'element_status', 12, 0, '((1))', NULL, 0, 0),
  (@finance_products_table_recid, 7, 'element_created_on', 13, 0, '(sysutcdatetime())', NULL, 0, 0),
  (@finance_products_table_recid, 7, 'element_modified_on', 14, 0, '(sysutcdatetime())', NULL, 0, 0);
GO

DECLARE @finance_product_journal_config_table_recid BIGINT = (
  SELECT recid FROM system_schema_tables WHERE element_name = 'finance_product_journal_config' AND element_schema = 'dbo'
);
DELETE FROM system_schema_columns WHERE tables_recid = @finance_product_journal_config_table_recid;
INSERT INTO system_schema_columns
  (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
VALUES
  (@finance_product_journal_config_table_recid, 3, 'recid', 1, 0, NULL, NULL, 1, 1),
  (@finance_product_journal_config_table_recid, 8, 'element_category', 2, 0, NULL, 64, 0, 0),
  (@finance_product_journal_config_table_recid, 8, 'element_journal_scope', 3, 0, NULL, 64, 0, 0),
  (@finance_product_journal_config_table_recid, 2, 'journals_recid', 4, 0, NULL, NULL, 0, 0),
  (@finance_product_journal_config_table_recid, 4, 'periods_guid', 5, 0, NULL, NULL, 0, 0),
  (@finance_product_journal_config_table_recid, 8, 'element_approved_by', 6, 1, NULL, 128, 0, 0),
  (@finance_product_journal_config_table_recid, 7, 'element_approved_on', 7, 1, NULL, NULL, 0, 0),
  (@finance_product_journal_config_table_recid, 8, 'element_activated_by', 8, 1, NULL, 128, 0, 0),
  (@finance_product_journal_config_table_recid, 7, 'element_activated_on', 9, 1, NULL, NULL, 0, 0),
  (@finance_product_journal_config_table_recid, 11, 'element_status', 10, 0, '((0))', NULL, 0, 0),
  (@finance_product_journal_config_table_recid, 7, 'element_created_on', 11, 0, '(sysutcdatetime())', NULL, 0, 0),
  (@finance_product_journal_config_table_recid, 7, 'element_modified_on', 12, 0, '(sysutcdatetime())', NULL, 0, 0);
GO

DELETE FROM system_schema_indexes WHERE tables_recid IN (@finance_products_table_recid, @finance_product_journal_config_table_recid);
INSERT INTO system_schema_indexes (tables_recid, element_name, element_columns, element_is_unique)
VALUES
  (@finance_products_table_recid, 'UQ_finance_products_sku', 'element_sku', 1),
  (@finance_product_journal_config_table_recid, 'UQ_product_journal_config_category_period', 'element_category,periods_guid', 1);
GO

DELETE FROM system_schema_foreign_keys WHERE tables_recid = @finance_product_journal_config_table_recid;
INSERT INTO system_schema_foreign_keys (tables_recid, element_column, ref_tables_recid, ref_element_column)
VALUES
  (@finance_product_journal_config_table_recid, 'journals_recid', (SELECT recid FROM system_schema_tables WHERE element_name = 'finance_journals' AND element_schema = 'dbo'), 'recid'),
  (@finance_product_journal_config_table_recid, 'periods_guid', (SELECT recid FROM system_schema_tables WHERE element_name = 'finance_periods' AND element_schema = 'dbo'), 'element_guid');
GO

INSERT INTO finance_status_codes (element_domain, element_code, element_name, element_description)
SELECT v.element_domain, v.element_code, v.element_name, v.element_description
FROM (VALUES
  ('product', 0, 'inactive', 'Inactive product'),
  ('product', 1, 'active', 'Active product'),
  ('product_journal_config', 0, 'draft', 'Draft product journal config'),
  ('product_journal_config', 1, 'approved', 'Approved product journal config'),
  ('product_journal_config', 2, 'active', 'Active product journal config'),
  ('product_journal_config', 3, 'closed', 'Closed product journal config')
) v(element_domain, element_code, element_name, element_description)
WHERE NOT EXISTS (
  SELECT 1
  FROM finance_status_codes existing
  WHERE existing.element_domain = v.element_domain
    AND existing.element_code = v.element_code
);
GO

INSERT INTO finance_products (
  element_sku,
  element_name,
  element_description,
  element_category,
  element_price,
  element_currency,
  element_credits,
  element_enablement_key,
  element_is_recurring,
  element_sort_order,
  element_status
)
SELECT seed.element_sku, seed.element_name, seed.element_description, seed.element_category, seed.element_price, seed.element_currency, seed.element_credits, seed.element_enablement_key, seed.element_is_recurring, seed.element_sort_order, seed.element_status
FROM (VALUES
  ('STOR-ENABLE', 'Enable Storage', 'Turn on storage access for your account.', 'enablement', CAST(0.00000 AS DECIMAL(19,5)), 'USD', 0, 'ROLE_STORAGE', 0, 10, 1),
  ('CRED-5K', 'Purchase 5,000 AI Credits', 'Add 5,000 AI credits to your wallet.', 'credit_purchase', CAST(50.00000 AS DECIMAL(19,5)), 'USD', 5000, NULL, 0, 20, 1),
  ('CRED-10K', 'Purchase 10,000 AI Credits', 'Add 10,000 AI credits to your wallet.', 'credit_purchase', CAST(100.00000 AS DECIMAL(19,5)), 'USD', 10000, NULL, 0, 30, 1),
  ('CRED-20K', 'Purchase 20,000 AI Credits', 'Add 20,000 AI credits to your wallet.', 'credit_purchase', CAST(200.00000 AS DECIMAL(19,5)), 'USD', 20000, NULL, 0, 40, 1),
  ('CRED-50K', 'Purchase 50,000 AI Credits', 'Add 50,000 AI credits to your wallet.', 'credit_purchase', CAST(500.00000 AS DECIMAL(19,5)), 'USD', 50000, NULL, 0, 50, 1),
  ('DISC-ENABLE', 'Enable Discord Bot', 'Enable the Discord bot integration for your account.', 'enablement', CAST(0.00000 AS DECIMAL(19,5)), 'USD', 0, 'ROLE_DISCORD_BOT', 0, 60, 1)
) seed(element_sku, element_name, element_description, element_category, element_price, element_currency, element_credits, element_enablement_key, element_is_recurring, element_sort_order, element_status)
WHERE NOT EXISTS (
  SELECT 1 FROM finance_products existing WHERE existing.element_sku = seed.element_sku
);
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
SELECT seed.element_pipeline, seed.element_key, seed.element_value, seed.element_description, 1, SYSUTCDATETIME(), SYSUTCDATETIME()
FROM (VALUES
  ('credit_purchase', 'payment_clearing_account_number', '1300', 'Payment Processor Clearing account debited on credit purchase'),
  ('credit_purchase', 'merchant_fee_account_number', '5010', 'Merchant Fee Expense account for payment processor fees')
) seed(element_pipeline, element_key, element_value, element_description)
WHERE NOT EXISTS (
  SELECT 1
  FROM finance_pipeline_config existing
  WHERE existing.element_pipeline = seed.element_pipeline
    AND existing.element_key = seed.element_key
);
GO
