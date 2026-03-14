SET ANSI_NULLS ON;
SET QUOTED_IDENTIFIER ON;
GO

-- ============================================================================
-- v0.8.3.3 Finance Staging Tables
-- Captures finance_staging_imports and finance_staging_cost_details which
-- exist in production but were never committed as migration scripts.
-- IF NOT EXISTS guards ensure idempotency against existing deployments.
-- ============================================================================

-- A1. finance_staging_imports
IF NOT EXISTS (SELECT 1 FROM sys.tables WHERE name = 'finance_staging_imports' AND schema_id = SCHEMA_ID('dbo'))
BEGIN
  CREATE TABLE [dbo].[finance_staging_imports] (
    [recid]                 BIGINT IDENTITY(1,1) NOT NULL,
    [element_guid]          UNIQUEIDENTIFIER NOT NULL DEFAULT NEWID(),
    [element_source]        NVARCHAR(50) NOT NULL DEFAULT N'azure_billing',
    [element_scope]         NVARCHAR(1024) NULL,
    [element_metric]        NVARCHAR(50) NOT NULL DEFAULT N'ActualCost',
    [element_period_start]  DATE NOT NULL,
    [element_period_end]    DATE NOT NULL,
    [element_row_count]     INT NOT NULL DEFAULT ((0)),
    [element_status]        TINYINT NOT NULL DEFAULT ((0)),
    [element_error]         NVARCHAR(MAX) NULL,
    [element_created_on]    DATETIMEOFFSET(7) NOT NULL DEFAULT (SYSUTCDATETIME()),
    [element_modified_on]   DATETIMEOFFSET(7) NOT NULL DEFAULT (SYSUTCDATETIME()),
    CONSTRAINT [PK_finance_staging_imports] PRIMARY KEY ([recid])
  );
END
GO

-- A2. finance_staging_cost_details
IF NOT EXISTS (SELECT 1 FROM sys.tables WHERE name = 'finance_staging_cost_details' AND schema_id = SCHEMA_ID('dbo'))
BEGIN
  CREATE TABLE [dbo].[finance_staging_cost_details] (
    [recid]                                    BIGINT IDENTITY(1,1) NOT NULL,
    [imports_recid]                            BIGINT NOT NULL,
    [element_InvoiceId]                        NVARCHAR(256) NULL,
    [element_BillingAccountId]                 NVARCHAR(256) NULL,
    [element_BillingAccountName]               NVARCHAR(512) NULL,
    [element_BillingProfileId]                 NVARCHAR(256) NULL,
    [element_BillingProfileName]               NVARCHAR(512) NULL,
    [element_InvoiceSectionId]                 NVARCHAR(256) NULL,
    [element_InvoiceSectionName]               NVARCHAR(512) NULL,
    [element_SubscriptionId]                   NVARCHAR(256) NULL,
    [element_SubscriptionName]                 NVARCHAR(512) NULL,
    [element_BillingPeriod]                    NVARCHAR(50) NULL,
    [element_BillingPeriodStartDate]           NVARCHAR(50) NULL,
    [element_BillingPeriodEndDate]             NVARCHAR(50) NULL,
    [element_Date]                             NVARCHAR(50) NULL,
    [element_ResourceId]                       NVARCHAR(2048) NULL,
    [element_ResourceName]                     NVARCHAR(512) NULL,
    [element_ResourceGroup]                    NVARCHAR(512) NULL,
    [element_ResourceLocation]                 NVARCHAR(256) NULL,
    [element_ResourceLocationNormalized]       NVARCHAR(256) NULL,
    [element_ResourceType]                     NVARCHAR(512) NULL,
    [element_ConsumedService]                  NVARCHAR(512) NULL,
    [element_MeterId]                          NVARCHAR(256) NULL,
    [element_MeterName]                        NVARCHAR(512) NULL,
    [element_MeterCategory]                    NVARCHAR(512) NULL,
    [element_MeterSubCategory]                 NVARCHAR(512) NULL,
    [element_MeterRegion]                      NVARCHAR(256) NULL,
    [element_Quantity]                         NVARCHAR(50) NULL,
    [element_UnitOfMeasure]                    NVARCHAR(256) NULL,
    [element_UnitPrice]                        NVARCHAR(50) NULL,
    [element_EffectivePrice]                   NVARCHAR(50) NULL,
    [element_PayGPrice]                        NVARCHAR(50) NULL,
    [element_ResourceRate]                     NVARCHAR(50) NULL,
    [element_Cost]                             NVARCHAR(50) NULL,
    [element_CostInBillingCurrency]            NVARCHAR(50) NULL,
    [element_CostInPricingCurrency]            NVARCHAR(50) NULL,
    [element_CostInUsd]                        NVARCHAR(50) NULL,
    [element_PreTaxCost]                       NVARCHAR(50) NULL,
    [element_PaygCostInBillingCurrency]        NVARCHAR(50) NULL,
    [element_PaygCostInUsd]                    NVARCHAR(50) NULL,
    [element_BillingCurrency]                  NVARCHAR(10) NULL,
    [element_BillingCurrencyCode]              NVARCHAR(10) NULL,
    [element_PricingCurrency]                  NVARCHAR(10) NULL,
    [element_Currency]                         NVARCHAR(10) NULL,
    [element_ExchangeRateDate]                 NVARCHAR(50) NULL,
    [element_ExchangeRatePricingToBilling]     NVARCHAR(50) NULL,
    [element_ChargeType]                       NVARCHAR(50) NULL,
    [element_Frequency]                        NVARCHAR(50) NULL,
    [element_PricingModel]                     NVARCHAR(50) NULL,
    [element_PublisherType]                    NVARCHAR(50) NULL,
    [element_PublisherName]                    NVARCHAR(512) NULL,
    [element_PublisherId]                      NVARCHAR(256) NULL,
    [element_ProductName]                      NVARCHAR(512) NULL,
    [element_ProductId]                        NVARCHAR(256) NULL,
    [element_ProductOrderId]                   NVARCHAR(256) NULL,
    [element_ProductOrderName]                 NVARCHAR(512) NULL,
    [element_PlanName]                         NVARCHAR(512) NULL,
    [element_OfferId]                          NVARCHAR(256) NULL,
    [element_AccountId]                        NVARCHAR(256) NULL,
    [element_AccountName]                      NVARCHAR(512) NULL,
    [element_AccountOwnerId]                   NVARCHAR(512) NULL,
    [element_PartNumber]                       NVARCHAR(256) NULL,
    [element_ServiceFamily]                    NVARCHAR(256) NULL,
    [element_ServiceName]                      NVARCHAR(256) NULL,
    [element_ServiceTier]                      NVARCHAR(256) NULL,
    [element_ServiceInfo1]                     NVARCHAR(MAX) NULL,
    [element_ServiceInfo2]                     NVARCHAR(MAX) NULL,
    [element_ServicePeriodStartDate]           NVARCHAR(50) NULL,
    [element_ServicePeriodEndDate]             NVARCHAR(50) NULL,
    [element_ReservationId]                    NVARCHAR(256) NULL,
    [element_ReservationName]                  NVARCHAR(512) NULL,
    [element_BenefitId]                        NVARCHAR(256) NULL,
    [element_BenefitName]                      NVARCHAR(512) NULL,
    [element_Term]                             NVARCHAR(50) NULL,
    [element_Tags]                             NVARCHAR(MAX) NULL,
    [element_AdditionalInfo]                   NVARCHAR(MAX) NULL,
    [element_CostCenter]                       NVARCHAR(512) NULL,
    [element_IsAzureCreditEligible]            NVARCHAR(10) NULL,
    [element_CostAllocationRuleName]           NVARCHAR(512) NULL,
    [element_CustomerName]                     NVARCHAR(512) NULL,
    [element_CustomerTenantId]                 NVARCHAR(256) NULL,
    [element_ResellerName]                     NVARCHAR(512) NULL,
    [element_ResellerMpnId]                    NVARCHAR(256) NULL,
    [element_PartnerName]                      NVARCHAR(512) NULL,
    [element_PartnerTenantId]                  NVARCHAR(256) NULL,
    [element_PartnerEarnedCreditApplied]       NVARCHAR(10) NULL,
    [element_PartnerEarnedCreditRate]          NVARCHAR(50) NULL,
    [element_PreviousInvoiceId]                NVARCHAR(256) NULL,
    [element_AvailabilityZone]                 NVARCHAR(256) NULL,
    [element_created_on]                       DATETIMEOFFSET(7) NOT NULL DEFAULT (SYSUTCDATETIME()),
    [element_ResourceGroupName]                NVARCHAR(512) NULL,
    [element_Location]                         NVARCHAR(256) NULL,
    [element_Provider]                         NVARCHAR(256) NULL,
    CONSTRAINT [PK_finance_staging_cost_details] PRIMARY KEY ([recid]),
    CONSTRAINT [FK_finance_staging_cost_details_imports_recid_finance_staging_imports]
      FOREIGN KEY ([imports_recid]) REFERENCES [dbo].[finance_staging_imports] ([recid])
  );
END
GO

-- ============================================================================
-- REFLECTION TABLE UPDATES
-- Uses IF NOT EXISTS / WHERE NOT EXISTS guards for idempotency.
-- ============================================================================

-- Register tables
IF NOT EXISTS (SELECT 1 FROM system_schema_tables WHERE element_name = 'finance_staging_imports' AND element_schema = 'dbo')
  INSERT INTO system_schema_tables (element_name, element_schema) VALUES ('finance_staging_imports', 'dbo');
GO

IF NOT EXISTS (SELECT 1 FROM system_schema_tables WHERE element_name = 'finance_staging_cost_details' AND element_schema = 'dbo')
  INSERT INTO system_schema_tables (element_name, element_schema) VALUES ('finance_staging_cost_details', 'dbo');
GO

-- Columns for finance_staging_imports (12 columns)
INSERT INTO system_schema_columns (
  tables_recid, edt_recid, element_name, element_ordinal, element_nullable,
  element_default, element_max_length, element_is_primary_key, element_is_identity
)
SELECT t.recid, e.recid, v.element_name, v.element_ordinal, v.element_nullable,
       v.element_default, v.element_max_length, v.element_is_primary_key, v.element_is_identity
FROM (VALUES
  ('INT64_IDENTITY', 'recid',                1, 0, NULL,                  NULL, 1, 1),
  ('UUID',           'element_guid',          2, 0, '(newid())',           NULL, 0, 0),
  ('STRING',         'element_source',        3, 0, '(N''azure_billing'')', 50, 0, 0),
  ('STRING',         'element_scope',         4, 1, NULL,                 1024, 0, 0),
  ('STRING',         'element_metric',        5, 0, '(N''ActualCost'')',    50, 0, 0),
  ('DATE',           'element_period_start',  6, 0, NULL,                  NULL, 0, 0),
  ('DATE',           'element_period_end',    7, 0, NULL,                  NULL, 0, 0),
  ('INT32',          'element_row_count',     8, 0, '((0))',               NULL, 0, 0),
  ('INT8',           'element_status',        9, 0, '((0))',               NULL, 0, 0),
  ('TEXT',           'element_error',        10, 1, NULL,                  NULL, 0, 0),
  ('DATETIME_TZ',   'element_created_on',   11, 0, '(sysutcdatetime())',  NULL, 0, 0),
  ('DATETIME_TZ',   'element_modified_on',  12, 0, '(sysutcdatetime())',  NULL, 0, 0)
) AS v(edt_name, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
CROSS JOIN (SELECT recid FROM system_schema_tables WHERE element_name = 'finance_staging_imports' AND element_schema = 'dbo') AS t
JOIN system_edt_mappings AS e ON e.element_name = v.edt_name
WHERE NOT EXISTS (
  SELECT 1 FROM system_schema_columns c
  WHERE c.tables_recid = t.recid AND c.element_name = v.element_name
);
GO

-- Columns for finance_staging_cost_details (92 columns)
-- Due to the width of this table, only the non-obvious columns are annotated.
-- The bulk of the columns are NVARCHAR fields imported from Azure Cost Management CSV.
INSERT INTO system_schema_columns (
  tables_recid, edt_recid, element_name, element_ordinal, element_nullable,
  element_default, element_max_length, element_is_primary_key, element_is_identity
)
SELECT t.recid, e.recid, v.element_name, v.element_ordinal, v.element_nullable,
       v.element_default, v.element_max_length, v.element_is_primary_key, v.element_is_identity
FROM (VALUES
  ('INT64_IDENTITY', 'recid',                                     1, 0, NULL,                 NULL, 1, 1),
  ('INT64',          'imports_recid',                              2, 0, NULL,                 NULL, 0, 0),
  ('STRING',         'element_InvoiceId',                          3, 1, NULL,                  256, 0, 0),
  ('STRING',         'element_BillingAccountId',                   4, 1, NULL,                  256, 0, 0),
  ('STRING',         'element_BillingAccountName',                 5, 1, NULL,                  512, 0, 0),
  ('STRING',         'element_BillingProfileId',                   6, 1, NULL,                  256, 0, 0),
  ('STRING',         'element_BillingProfileName',                 7, 1, NULL,                  512, 0, 0),
  ('STRING',         'element_InvoiceSectionId',                   8, 1, NULL,                  256, 0, 0),
  ('STRING',         'element_InvoiceSectionName',                 9, 1, NULL,                  512, 0, 0),
  ('STRING',         'element_SubscriptionId',                    10, 1, NULL,                  256, 0, 0),
  ('STRING',         'element_SubscriptionName',                  11, 1, NULL,                  512, 0, 0),
  ('STRING',         'element_BillingPeriod',                     12, 1, NULL,                   50, 0, 0),
  ('STRING',         'element_BillingPeriodStartDate',            13, 1, NULL,                   50, 0, 0),
  ('STRING',         'element_BillingPeriodEndDate',              14, 1, NULL,                   50, 0, 0),
  ('STRING',         'element_Date',                              15, 1, NULL,                   50, 0, 0),
  ('STRING',         'element_ResourceId',                        16, 1, NULL,                 2048, 0, 0),
  ('STRING',         'element_ResourceName',                      17, 1, NULL,                  512, 0, 0),
  ('STRING',         'element_ResourceGroup',                     18, 1, NULL,                  512, 0, 0),
  ('STRING',         'element_ResourceLocation',                  19, 1, NULL,                  256, 0, 0),
  ('STRING',         'element_ResourceLocationNormalized',        20, 1, NULL,                  256, 0, 0),
  ('STRING',         'element_ResourceType',                      21, 1, NULL,                  512, 0, 0),
  ('STRING',         'element_ConsumedService',                   22, 1, NULL,                  512, 0, 0),
  ('STRING',         'element_MeterId',                           23, 1, NULL,                  256, 0, 0),
  ('STRING',         'element_MeterName',                         24, 1, NULL,                  512, 0, 0),
  ('STRING',         'element_MeterCategory',                     25, 1, NULL,                  512, 0, 0),
  ('STRING',         'element_MeterSubCategory',                  26, 1, NULL,                  512, 0, 0),
  ('STRING',         'element_MeterRegion',                       27, 1, NULL,                  256, 0, 0),
  ('STRING',         'element_Quantity',                          28, 1, NULL,                   50, 0, 0),
  ('STRING',         'element_UnitOfMeasure',                     29, 1, NULL,                  256, 0, 0),
  ('STRING',         'element_UnitPrice',                         30, 1, NULL,                   50, 0, 0),
  ('STRING',         'element_EffectivePrice',                    31, 1, NULL,                   50, 0, 0),
  ('STRING',         'element_PayGPrice',                         32, 1, NULL,                   50, 0, 0),
  ('STRING',         'element_ResourceRate',                      33, 1, NULL,                   50, 0, 0),
  ('STRING',         'element_Cost',                              34, 1, NULL,                   50, 0, 0),
  ('STRING',         'element_CostInBillingCurrency',             35, 1, NULL,                   50, 0, 0),
  ('STRING',         'element_CostInPricingCurrency',             36, 1, NULL,                   50, 0, 0),
  ('STRING',         'element_CostInUsd',                         37, 1, NULL,                   50, 0, 0),
  ('STRING',         'element_PreTaxCost',                        38, 1, NULL,                   50, 0, 0),
  ('STRING',         'element_PaygCostInBillingCurrency',         39, 1, NULL,                   50, 0, 0),
  ('STRING',         'element_PaygCostInUsd',                     40, 1, NULL,                   50, 0, 0),
  ('STRING',         'element_BillingCurrency',                   41, 1, NULL,                   10, 0, 0),
  ('STRING',         'element_BillingCurrencyCode',               42, 1, NULL,                   10, 0, 0),
  ('STRING',         'element_PricingCurrency',                   43, 1, NULL,                   10, 0, 0),
  ('STRING',         'element_Currency',                          44, 1, NULL,                   10, 0, 0),
  ('STRING',         'element_ExchangeRateDate',                  45, 1, NULL,                   50, 0, 0),
  ('STRING',         'element_ExchangeRatePricingToBilling',      46, 1, NULL,                   50, 0, 0),
  ('STRING',         'element_ChargeType',                        47, 1, NULL,                   50, 0, 0),
  ('STRING',         'element_Frequency',                         48, 1, NULL,                   50, 0, 0),
  ('STRING',         'element_PricingModel',                      49, 1, NULL,                   50, 0, 0),
  ('STRING',         'element_PublisherType',                     50, 1, NULL,                   50, 0, 0),
  ('STRING',         'element_PublisherName',                     51, 1, NULL,                  512, 0, 0),
  ('STRING',         'element_PublisherId',                       52, 1, NULL,                  256, 0, 0),
  ('STRING',         'element_ProductName',                       53, 1, NULL,                  512, 0, 0),
  ('STRING',         'element_ProductId',                         54, 1, NULL,                  256, 0, 0),
  ('STRING',         'element_ProductOrderId',                    55, 1, NULL,                  256, 0, 0),
  ('STRING',         'element_ProductOrderName',                  56, 1, NULL,                  512, 0, 0),
  ('STRING',         'element_PlanName',                          57, 1, NULL,                  512, 0, 0),
  ('STRING',         'element_OfferId',                           58, 1, NULL,                  256, 0, 0),
  ('STRING',         'element_AccountId',                         59, 1, NULL,                  256, 0, 0),
  ('STRING',         'element_AccountName',                       60, 1, NULL,                  512, 0, 0),
  ('STRING',         'element_AccountOwnerId',                    61, 1, NULL,                  512, 0, 0),
  ('STRING',         'element_PartNumber',                        62, 1, NULL,                  256, 0, 0),
  ('STRING',         'element_ServiceFamily',                     63, 1, NULL,                  256, 0, 0),
  ('STRING',         'element_ServiceName',                       64, 1, NULL,                  256, 0, 0),
  ('STRING',         'element_ServiceTier',                       65, 1, NULL,                  256, 0, 0),
  ('TEXT',           'element_ServiceInfo1',                      66, 1, NULL,                 NULL, 0, 0),
  ('TEXT',           'element_ServiceInfo2',                      67, 1, NULL,                 NULL, 0, 0),
  ('STRING',         'element_ServicePeriodStartDate',            68, 1, NULL,                   50, 0, 0),
  ('STRING',         'element_ServicePeriodEndDate',              69, 1, NULL,                   50, 0, 0),
  ('STRING',         'element_ReservationId',                     70, 1, NULL,                  256, 0, 0),
  ('STRING',         'element_ReservationName',                   71, 1, NULL,                  512, 0, 0),
  ('STRING',         'element_BenefitId',                         72, 1, NULL,                  256, 0, 0),
  ('STRING',         'element_BenefitName',                       73, 1, NULL,                  512, 0, 0),
  ('STRING',         'element_Term',                              74, 1, NULL,                   50, 0, 0),
  ('TEXT',           'element_Tags',                              75, 1, NULL,                 NULL, 0, 0),
  ('TEXT',           'element_AdditionalInfo',                    76, 1, NULL,                 NULL, 0, 0),
  ('STRING',         'element_CostCenter',                        77, 1, NULL,                  512, 0, 0),
  ('STRING',         'element_IsAzureCreditEligible',             78, 1, NULL,                   10, 0, 0),
  ('STRING',         'element_CostAllocationRuleName',            79, 1, NULL,                  512, 0, 0),
  ('STRING',         'element_CustomerName',                      80, 1, NULL,                  512, 0, 0),
  ('STRING',         'element_CustomerTenantId',                  81, 1, NULL,                  256, 0, 0),
  ('STRING',         'element_ResellerName',                      82, 1, NULL,                  512, 0, 0),
  ('STRING',         'element_ResellerMpnId',                     83, 1, NULL,                  256, 0, 0),
  ('STRING',         'element_PartnerName',                       84, 1, NULL,                  512, 0, 0),
  ('STRING',         'element_PartnerTenantId',                   85, 1, NULL,                  256, 0, 0),
  ('STRING',         'element_PartnerEarnedCreditApplied',        86, 1, NULL,                   10, 0, 0),
  ('STRING',         'element_PartnerEarnedCreditRate',           87, 1, NULL,                   50, 0, 0),
  ('STRING',         'element_PreviousInvoiceId',                 88, 1, NULL,                  256, 0, 0),
  ('STRING',         'element_AvailabilityZone',                  89, 1, NULL,                  256, 0, 0),
  ('DATETIME_TZ',   'element_created_on',                        90, 0, '(sysutcdatetime())', NULL, 0, 0),
  ('STRING',         'element_ResourceGroupName',                 91, 1, NULL,                  512, 0, 0),
  ('STRING',         'element_Location',                          92, 1, NULL,                  256, 0, 0),
  ('STRING',         'element_Provider',                          93, 1, NULL,                  256, 0, 0)
) AS v(edt_name, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
CROSS JOIN (SELECT recid FROM system_schema_tables WHERE element_name = 'finance_staging_cost_details' AND element_schema = 'dbo') AS t
JOIN system_edt_mappings AS e ON e.element_name = v.edt_name
WHERE NOT EXISTS (
  SELECT 1 FROM system_schema_columns c
  WHERE c.tables_recid = t.recid AND c.element_name = v.element_name
);
GO

-- Foreign key
INSERT INTO system_schema_foreign_keys (
  tables_recid, element_column_name, referenced_tables_recid, element_referenced_column
)
SELECT
  (SELECT recid FROM system_schema_tables WHERE element_name = 'finance_staging_cost_details' AND element_schema = 'dbo'),
  'imports_recid',
  (SELECT recid FROM system_schema_tables WHERE element_name = 'finance_staging_imports' AND element_schema = 'dbo'),
  'recid'
WHERE NOT EXISTS (
  SELECT 1 FROM system_schema_foreign_keys fk
  JOIN system_schema_tables t ON t.recid = fk.tables_recid
  WHERE t.element_name = 'finance_staging_cost_details' AND fk.element_column_name = 'imports_recid'
);
GO
