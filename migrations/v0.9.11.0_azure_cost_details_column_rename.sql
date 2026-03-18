IF OBJECT_ID(N'dbo.finance_staging_azure_cost_details', N'U') IS NOT NULL
BEGIN
  DECLARE @drop_index_sql NVARCHAR(MAX) = NULL;

  SELECT @drop_index_sql = STRING_AGG(
    N'DROP INDEX [' + i.[name] + N'] ON [dbo].[finance_staging_azure_cost_details];',
    CHAR(10)
  )
  FROM sys.indexes AS i
  WHERE i.object_id = OBJECT_ID(N'dbo.finance_staging_azure_cost_details', N'U')
    AND i.index_id > 1
    AND i.is_hypothetical = 0;

  IF @drop_index_sql IS NOT NULL
  BEGIN
    EXEC sp_executesql @drop_index_sql;
  END;
END;
GO

IF OBJECT_ID(N'dbo.finance_staging_azure_cost_details', N'U') IS NOT NULL
BEGIN
  DECLARE @drop_fk_sql NVARCHAR(MAX) = NULL;

  SELECT @drop_fk_sql = STRING_AGG(
    N'ALTER TABLE [dbo].[finance_staging_azure_cost_details] DROP CONSTRAINT [' + fk.[name] + N'];',
    CHAR(10)
  )
  FROM sys.foreign_keys AS fk
  WHERE fk.parent_object_id = OBJECT_ID(N'dbo.finance_staging_azure_cost_details', N'U');

  IF @drop_fk_sql IS NOT NULL
  BEGIN
    EXEC sp_executesql @drop_fk_sql;
  END;
END;
GO

IF OBJECT_ID(N'dbo.finance_staging_azure_cost_details', N'U') IS NOT NULL
BEGIN
  DECLARE @drop_pk_sql NVARCHAR(MAX) = NULL;

  SELECT @drop_pk_sql = STRING_AGG(
    N'ALTER TABLE [dbo].[finance_staging_azure_cost_details] DROP CONSTRAINT [' + kc.[name] + N'];',
    CHAR(10)
  )
  FROM sys.key_constraints AS kc
  WHERE kc.parent_object_id = OBJECT_ID(N'dbo.finance_staging_azure_cost_details', N'U')
    AND kc.[type] = 'PK';

  IF @drop_pk_sql IS NOT NULL
  BEGIN
    EXEC sp_executesql @drop_pk_sql;
  END;
END;
GO

DROP TABLE IF EXISTS [dbo].[finance_staging_azure_cost_details];
GO

CREATE TABLE [dbo].[finance_staging_azure_cost_details] (
  [recid] BIGINT IDENTITY(1,1) NOT NULL,
  [imports_recid] BIGINT NOT NULL,
  [element_invoiceId] NVARCHAR(256) NULL,
  [element_previousInvoiceId] NVARCHAR(256) NULL,
  [element_billingAccountId] NVARCHAR(256) NULL,
  [element_billingAccountName] NVARCHAR(512) NULL,
  [element_billingProfileId] NVARCHAR(256) NULL,
  [element_billingProfileName] NVARCHAR(512) NULL,
  [element_invoiceSectionId] NVARCHAR(256) NULL,
  [element_invoiceSectionName] NVARCHAR(512) NULL,
  [element_resellerName] NVARCHAR(512) NULL,
  [element_resellerMpnId] NVARCHAR(256) NULL,
  [element_costCenter] NVARCHAR(512) NULL,
  [element_billingPeriodEndDate] NVARCHAR(50) NULL,
  [element_billingPeriodStartDate] NVARCHAR(50) NULL,
  [element_servicePeriodEndDate] NVARCHAR(50) NULL,
  [element_servicePeriodStartDate] NVARCHAR(50) NULL,
  [element_date] NVARCHAR(50) NULL,
  [element_serviceFamily] NVARCHAR(512) NULL,
  [element_productOrderId] NVARCHAR(256) NULL,
  [element_productOrderName] NVARCHAR(512) NULL,
  [element_consumedService] NVARCHAR(512) NULL,
  [element_meterId] NVARCHAR(256) NULL,
  [element_meterName] NVARCHAR(512) NULL,
  [element_meterCategory] NVARCHAR(512) NULL,
  [element_meterSubCategory] NVARCHAR(512) NULL,
  [element_meterRegion] NVARCHAR(512) NULL,
  [element_ProductId] NVARCHAR(256) NULL,
  [element_ProductName] NVARCHAR(512) NULL,
  [element_SubscriptionId] NVARCHAR(256) NULL,
  [element_subscriptionName] NVARCHAR(512) NULL,
  [element_publisherType] NVARCHAR(512) NULL,
  [element_publisherId] NVARCHAR(256) NULL,
  [element_publisherName] NVARCHAR(512) NULL,
  [element_resourceGroupName] NVARCHAR(512) NULL,
  [element_ResourceId] NVARCHAR(256) NULL,
  [element_resourceLocation] NVARCHAR(512) NULL,
  [element_location] NVARCHAR(512) NULL,
  [element_effectivePrice] NVARCHAR(50) NULL,
  [element_quantity] NVARCHAR(50) NULL,
  [element_unitOfMeasure] NVARCHAR(512) NULL,
  [element_chargeType] NVARCHAR(512) NULL,
  [element_billingCurrency] NVARCHAR(50) NULL,
  [element_pricingCurrency] NVARCHAR(50) NULL,
  [element_costInBillingCurrency] NVARCHAR(50) NULL,
  [element_costInPricingCurrency] NVARCHAR(50) NULL,
  [element_costInUsd] NVARCHAR(50) NULL,
  [element_paygCostInBillingCurrency] NVARCHAR(50) NULL,
  [element_paygCostInUsd] NVARCHAR(50) NULL,
  [element_exchangeRatePricingToBilling] NVARCHAR(50) NULL,
  [element_exchangeRateDate] NVARCHAR(50) NULL,
  [element_isAzureCreditEligible] NVARCHAR(50) NULL,
  [element_serviceInfo1] NVARCHAR(MAX) NULL,
  [element_serviceInfo2] NVARCHAR(MAX) NULL,
  [element_additionalInfo] NVARCHAR(MAX) NULL,
  [element_tags] NVARCHAR(MAX) NULL,
  [element_PayGPrice] NVARCHAR(50) NULL,
  [element_frequency] NVARCHAR(50) NULL,
  [element_term] NVARCHAR(50) NULL,
  [element_reservationId] NVARCHAR(256) NULL,
  [element_reservationName] NVARCHAR(512) NULL,
  [element_pricingModel] NVARCHAR(512) NULL,
  [element_unitPrice] NVARCHAR(50) NULL,
  [element_costAllocationRuleName] NVARCHAR(512) NULL,
  [element_benefitId] NVARCHAR(256) NULL,
  [element_benefitName] NVARCHAR(512) NULL,
  [element_provider] NVARCHAR(50) NULL,
  [element_created_on] DATETIMEOFFSET(7) NOT NULL DEFAULT (SYSUTCDATETIME()),
  CONSTRAINT [PK_finance_staging_cost_details] PRIMARY KEY ([recid]),
  CONSTRAINT [FK_finance_staging_azure_cost_details_imports_recid] FOREIGN KEY ([imports_recid])
    REFERENCES [dbo].[finance_staging_imports] ([recid])
);
GO

CREATE INDEX [IX_finance_staging_cost_details_import]
  ON [dbo].[finance_staging_azure_cost_details] ([imports_recid]);
CREATE INDEX [IX_finance_staging_cost_details_date]
  ON [dbo].[finance_staging_azure_cost_details] ([element_date]);
CREATE INDEX [IX_finance_staging_cost_details_subscription]
  ON [dbo].[finance_staging_azure_cost_details] ([element_SubscriptionId], [element_date]);
GO

INSERT INTO system_schema_tables (element_name, element_schema)
SELECT 'finance_staging_azure_cost_details', 'dbo'
WHERE NOT EXISTS (
  SELECT 1
  FROM system_schema_tables
  WHERE element_name = 'finance_staging_azure_cost_details'
    AND element_schema = 'dbo'
);
GO

DECLARE @azure_cost_details_table_recid BIGINT;
SELECT @azure_cost_details_table_recid = recid
FROM system_schema_tables
WHERE element_name = 'finance_staging_azure_cost_details'
  AND element_schema = 'dbo';

DELETE c
FROM system_schema_columns AS c
WHERE c.tables_recid = @azure_cost_details_table_recid;

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
  (@azure_cost_details_table_recid, 3, 'recid', 1, 0, NULL, NULL, 1, 1),
  (@azure_cost_details_table_recid, 2, 'imports_recid', 2, 0, NULL, NULL, 0, 0),
  (@azure_cost_details_table_recid, 8, 'element_invoiceId', 3, 1, NULL, 256, 0, 0),
  (@azure_cost_details_table_recid, 8, 'element_previousInvoiceId', 4, 1, NULL, 256, 0, 0),
  (@azure_cost_details_table_recid, 8, 'element_billingAccountId', 5, 1, NULL, 256, 0, 0),
  (@azure_cost_details_table_recid, 8, 'element_billingAccountName', 6, 1, NULL, 512, 0, 0),
  (@azure_cost_details_table_recid, 8, 'element_billingProfileId', 7, 1, NULL, 256, 0, 0),
  (@azure_cost_details_table_recid, 8, 'element_billingProfileName', 8, 1, NULL, 512, 0, 0),
  (@azure_cost_details_table_recid, 8, 'element_invoiceSectionId', 9, 1, NULL, 256, 0, 0),
  (@azure_cost_details_table_recid, 8, 'element_invoiceSectionName', 10, 1, NULL, 512, 0, 0),
  (@azure_cost_details_table_recid, 8, 'element_resellerName', 11, 1, NULL, 512, 0, 0),
  (@azure_cost_details_table_recid, 8, 'element_resellerMpnId', 12, 1, NULL, 256, 0, 0),
  (@azure_cost_details_table_recid, 8, 'element_costCenter', 13, 1, NULL, 512, 0, 0),
  (@azure_cost_details_table_recid, 8, 'element_billingPeriodEndDate', 14, 1, NULL, 50, 0, 0),
  (@azure_cost_details_table_recid, 8, 'element_billingPeriodStartDate', 15, 1, NULL, 50, 0, 0),
  (@azure_cost_details_table_recid, 8, 'element_servicePeriodEndDate', 16, 1, NULL, 50, 0, 0),
  (@azure_cost_details_table_recid, 8, 'element_servicePeriodStartDate', 17, 1, NULL, 50, 0, 0),
  (@azure_cost_details_table_recid, 8, 'element_date', 18, 1, NULL, 50, 0, 0),
  (@azure_cost_details_table_recid, 8, 'element_serviceFamily', 19, 1, NULL, 512, 0, 0),
  (@azure_cost_details_table_recid, 8, 'element_productOrderId', 20, 1, NULL, 256, 0, 0),
  (@azure_cost_details_table_recid, 8, 'element_productOrderName', 21, 1, NULL, 512, 0, 0),
  (@azure_cost_details_table_recid, 8, 'element_consumedService', 22, 1, NULL, 512, 0, 0),
  (@azure_cost_details_table_recid, 8, 'element_meterId', 23, 1, NULL, 256, 0, 0),
  (@azure_cost_details_table_recid, 8, 'element_meterName', 24, 1, NULL, 512, 0, 0),
  (@azure_cost_details_table_recid, 8, 'element_meterCategory', 25, 1, NULL, 512, 0, 0),
  (@azure_cost_details_table_recid, 8, 'element_meterSubCategory', 26, 1, NULL, 512, 0, 0),
  (@azure_cost_details_table_recid, 8, 'element_meterRegion', 27, 1, NULL, 512, 0, 0),
  (@azure_cost_details_table_recid, 8, 'element_ProductId', 28, 1, NULL, 256, 0, 0),
  (@azure_cost_details_table_recid, 8, 'element_ProductName', 29, 1, NULL, 512, 0, 0),
  (@azure_cost_details_table_recid, 8, 'element_SubscriptionId', 30, 1, NULL, 256, 0, 0),
  (@azure_cost_details_table_recid, 8, 'element_subscriptionName', 31, 1, NULL, 512, 0, 0),
  (@azure_cost_details_table_recid, 8, 'element_publisherType', 32, 1, NULL, 512, 0, 0),
  (@azure_cost_details_table_recid, 8, 'element_publisherId', 33, 1, NULL, 256, 0, 0),
  (@azure_cost_details_table_recid, 8, 'element_publisherName', 34, 1, NULL, 512, 0, 0),
  (@azure_cost_details_table_recid, 8, 'element_resourceGroupName', 35, 1, NULL, 512, 0, 0),
  (@azure_cost_details_table_recid, 8, 'element_ResourceId', 36, 1, NULL, 256, 0, 0),
  (@azure_cost_details_table_recid, 8, 'element_resourceLocation', 37, 1, NULL, 512, 0, 0),
  (@azure_cost_details_table_recid, 8, 'element_location', 38, 1, NULL, 512, 0, 0),
  (@azure_cost_details_table_recid, 8, 'element_effectivePrice', 39, 1, NULL, 50, 0, 0),
  (@azure_cost_details_table_recid, 8, 'element_quantity', 40, 1, NULL, 50, 0, 0),
  (@azure_cost_details_table_recid, 8, 'element_unitOfMeasure', 41, 1, NULL, 512, 0, 0),
  (@azure_cost_details_table_recid, 8, 'element_chargeType', 42, 1, NULL, 512, 0, 0),
  (@azure_cost_details_table_recid, 8, 'element_billingCurrency', 43, 1, NULL, 50, 0, 0),
  (@azure_cost_details_table_recid, 8, 'element_pricingCurrency', 44, 1, NULL, 50, 0, 0),
  (@azure_cost_details_table_recid, 8, 'element_costInBillingCurrency', 45, 1, NULL, 50, 0, 0),
  (@azure_cost_details_table_recid, 8, 'element_costInPricingCurrency', 46, 1, NULL, 50, 0, 0),
  (@azure_cost_details_table_recid, 8, 'element_costInUsd', 47, 1, NULL, 50, 0, 0),
  (@azure_cost_details_table_recid, 8, 'element_paygCostInBillingCurrency', 48, 1, NULL, 50, 0, 0),
  (@azure_cost_details_table_recid, 8, 'element_paygCostInUsd', 49, 1, NULL, 50, 0, 0),
  (@azure_cost_details_table_recid, 8, 'element_exchangeRatePricingToBilling', 50, 1, NULL, 50, 0, 0),
  (@azure_cost_details_table_recid, 8, 'element_exchangeRateDate', 51, 1, NULL, 50, 0, 0),
  (@azure_cost_details_table_recid, 8, 'element_isAzureCreditEligible', 52, 1, NULL, 50, 0, 0),
  (@azure_cost_details_table_recid, 9, 'element_serviceInfo1', 53, 1, NULL, NULL, 0, 0),
  (@azure_cost_details_table_recid, 9, 'element_serviceInfo2', 54, 1, NULL, NULL, 0, 0),
  (@azure_cost_details_table_recid, 9, 'element_additionalInfo', 55, 1, NULL, NULL, 0, 0),
  (@azure_cost_details_table_recid, 9, 'element_tags', 56, 1, NULL, NULL, 0, 0),
  (@azure_cost_details_table_recid, 8, 'element_PayGPrice', 57, 1, NULL, 50, 0, 0),
  (@azure_cost_details_table_recid, 8, 'element_frequency', 58, 1, NULL, 50, 0, 0),
  (@azure_cost_details_table_recid, 8, 'element_term', 59, 1, NULL, 50, 0, 0),
  (@azure_cost_details_table_recid, 8, 'element_reservationId', 60, 1, NULL, 256, 0, 0),
  (@azure_cost_details_table_recid, 8, 'element_reservationName', 61, 1, NULL, 512, 0, 0),
  (@azure_cost_details_table_recid, 8, 'element_pricingModel', 62, 1, NULL, 512, 0, 0),
  (@azure_cost_details_table_recid, 8, 'element_unitPrice', 63, 1, NULL, 50, 0, 0),
  (@azure_cost_details_table_recid, 8, 'element_costAllocationRuleName', 64, 1, NULL, 512, 0, 0),
  (@azure_cost_details_table_recid, 8, 'element_benefitId', 65, 1, NULL, 256, 0, 0),
  (@azure_cost_details_table_recid, 8, 'element_benefitName', 66, 1, NULL, 512, 0, 0),
  (@azure_cost_details_table_recid, 8, 'element_provider', 67, 1, NULL, 50, 0, 0),
  (@azure_cost_details_table_recid, 7, 'element_created_on', 68, 0, '(sysutcdatetime())', NULL, 0, 0);
GO

DELETE i
FROM system_schema_indexes AS i
INNER JOIN system_schema_tables AS t ON t.recid = i.tables_recid
WHERE t.element_schema = 'dbo'
  AND t.element_name = 'finance_staging_azure_cost_details';

INSERT INTO system_schema_indexes (tables_recid, element_name, element_columns, element_is_unique)
VALUES
  ((SELECT recid FROM system_schema_tables WHERE element_name = 'finance_staging_azure_cost_details' AND element_schema = 'dbo'), 'PK_finance_staging_cost_details', 'recid', 1),
  ((SELECT recid FROM system_schema_tables WHERE element_name = 'finance_staging_azure_cost_details' AND element_schema = 'dbo'), 'IX_finance_staging_cost_details_import', 'imports_recid', 0),
  ((SELECT recid FROM system_schema_tables WHERE element_name = 'finance_staging_azure_cost_details' AND element_schema = 'dbo'), 'IX_finance_staging_cost_details_date', 'element_date', 0),
  ((SELECT recid FROM system_schema_tables WHERE element_name = 'finance_staging_azure_cost_details' AND element_schema = 'dbo'), 'IX_finance_staging_cost_details_subscription', 'element_SubscriptionId,element_date', 0);
GO

DELETE fk
FROM system_schema_foreign_keys AS fk
INNER JOIN system_schema_tables AS t ON t.recid = fk.tables_recid
WHERE t.element_schema = 'dbo'
  AND t.element_name = 'finance_staging_azure_cost_details';

INSERT INTO system_schema_foreign_keys (
  tables_recid,
  element_column_name,
  referenced_tables_recid,
  element_referenced_column
)
VALUES
  (
    (SELECT recid FROM system_schema_tables WHERE element_name = 'finance_staging_azure_cost_details' AND element_schema = 'dbo'),
    'imports_recid',
    (SELECT recid FROM system_schema_tables WHERE element_name = 'finance_staging_imports' AND element_schema = 'dbo'),
    'recid'
  );
GO
