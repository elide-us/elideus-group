IF OBJECT_ID(N'dbo.system_renewals', N'U') IS NULL
BEGIN
  CREATE TABLE [dbo].[system_renewals] (
    [recid] BIGINT IDENTITY(1,1) NOT NULL,
    [element_guid] UNIQUEIDENTIFIER NOT NULL DEFAULT (NEWID()),
    [element_name] NVARCHAR(256) NOT NULL,
    [element_category] NVARCHAR(64) NOT NULL,
    [element_vendor] NVARCHAR(128) NULL,
    [element_reference] NVARCHAR(512) NULL,
    [element_expires_on] DATE NULL,
    [element_renew_by] DATE NULL,
    [element_renewal_cost] DECIMAL(19,5) NULL,
    [element_currency] NVARCHAR(8) NULL,
    [element_auto_renew] BIT NOT NULL DEFAULT (0),
    [element_owner] NVARCHAR(128) NULL,
    [element_notes] NVARCHAR(MAX) NULL,
    [element_status] INT NOT NULL DEFAULT (1),
    [element_created_on] DATETIMEOFFSET(7) NOT NULL DEFAULT (SYSUTCDATETIME()),
    [element_modified_on] DATETIMEOFFSET(7) NOT NULL DEFAULT (SYSUTCDATETIME()),
    CONSTRAINT [PK_system_renewals] PRIMARY KEY ([recid]),
    CONSTRAINT [UQ_system_renewals_element_guid] UNIQUE ([element_guid])
  );
END;
GO

IF NOT EXISTS (
  SELECT 1 FROM sys.indexes
  WHERE [name] = N'IX_system_renewals_category'
    AND [object_id] = OBJECT_ID(N'dbo.system_renewals')
)
BEGIN
  CREATE INDEX [IX_system_renewals_category]
    ON [dbo].[system_renewals] ([element_category]);
END;
GO

IF NOT EXISTS (
  SELECT 1 FROM sys.indexes
  WHERE [name] = N'IX_system_renewals_expires_on'
    AND [object_id] = OBJECT_ID(N'dbo.system_renewals')
)
BEGIN
  CREATE INDEX [IX_system_renewals_expires_on]
    ON [dbo].[system_renewals] ([element_expires_on]);
END;
GO

IF NOT EXISTS (
  SELECT 1 FROM sys.indexes
  WHERE [name] = N'IX_system_renewals_status'
    AND [object_id] = OBJECT_ID(N'dbo.system_renewals')
)
BEGIN
  CREATE INDEX [IX_system_renewals_status]
    ON [dbo].[system_renewals] ([element_status]);
END;
GO

INSERT INTO system_schema_tables (element_name, element_schema)
SELECT v.element_name, v.element_schema
FROM (VALUES
  ('system_renewals', 'dbo')
) v(element_name, element_schema)
WHERE NOT EXISTS (
  SELECT 1
  FROM system_schema_tables t
  WHERE t.element_name = v.element_name
    AND t.element_schema = v.element_schema
);
GO

DECLARE @renewals_table_recid BIGINT;
SELECT @renewals_table_recid = recid
FROM system_schema_tables
WHERE element_name = 'system_renewals'
  AND element_schema = 'dbo';

DELETE c
FROM system_schema_columns c
WHERE c.tables_recid = @renewals_table_recid;

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
  (@renewals_table_recid, 3,  'recid',                1,  0, NULL,                 NULL, 1, 1),
  (@renewals_table_recid, 4,  'element_guid',         2,  0, '(newid())',          NULL, 0, 0),
  (@renewals_table_recid, 8,  'element_name',         3,  0, NULL,                 256,  0, 0),
  (@renewals_table_recid, 8,  'element_category',     4,  0, NULL,                 64,   0, 0),
  (@renewals_table_recid, 8,  'element_vendor',       5,  1, NULL,                 128,  0, 0),
  (@renewals_table_recid, 8,  'element_reference',    6,  1, NULL,                 512,  0, 0),
  (@renewals_table_recid, 12, 'element_expires_on',   7,  1, NULL,                 NULL, 0, 0),
  (@renewals_table_recid, 12, 'element_renew_by',     8,  1, NULL,                 NULL, 0, 0),
  (@renewals_table_recid, 13, 'element_renewal_cost', 9,  1, NULL,                 NULL, 0, 0),
  (@renewals_table_recid, 8,  'element_currency',     10, 1, NULL,                 8,    0, 0),
  (@renewals_table_recid, 5,  'element_auto_renew',   11, 0, '((0))',              NULL, 0, 0),
  (@renewals_table_recid, 8,  'element_owner',        12, 1, NULL,                 128,  0, 0),
  (@renewals_table_recid, 9,  'element_notes',        13, 1, NULL,                 NULL, 0, 0),
  (@renewals_table_recid, 1,  'element_status',       14, 0, '((1))',              NULL, 0, 0),
  (@renewals_table_recid, 7,  'element_created_on',   15, 0, '(sysutcdatetime())', NULL, 0, 0),
  (@renewals_table_recid, 7,  'element_modified_on',  16, 0, '(sysutcdatetime())', NULL, 0, 0);
GO

DELETE i
FROM system_schema_indexes i
INNER JOIN system_schema_tables t ON t.recid = i.tables_recid
WHERE t.element_schema = 'dbo'
  AND t.element_name = 'system_renewals';

INSERT INTO system_schema_indexes (
  tables_recid,
  element_name,
  element_columns,
  element_is_unique
)
VALUES
  ((SELECT recid FROM system_schema_tables WHERE element_name = 'system_renewals' AND element_schema = 'dbo'), 'UQ_system_renewals_element_guid', 'element_guid', 1),
  ((SELECT recid FROM system_schema_tables WHERE element_name = 'system_renewals' AND element_schema = 'dbo'), 'IX_system_renewals_category', 'element_category', 0),
  ((SELECT recid FROM system_schema_tables WHERE element_name = 'system_renewals' AND element_schema = 'dbo'), 'IX_system_renewals_expires_on', 'element_expires_on', 0),
  ((SELECT recid FROM system_schema_tables WHERE element_name = 'system_renewals' AND element_schema = 'dbo'), 'IX_system_renewals_status', 'element_status', 0);
GO

INSERT INTO system_renewals (
  element_name,
  element_category,
  element_vendor,
  element_reference,
  element_auto_renew,
  element_owner,
  element_notes,
  element_status
)
SELECT
  'elideusgroup.com',
  'domain',
  'Name.com',
  'elideusgroup.com',
  0,
  'ROLE_SERVICE_ADMIN',
  'Primary business domain',
  1
WHERE NOT EXISTS (
  SELECT 1 FROM system_renewals WHERE element_name = 'elideusgroup.com' AND element_category = 'domain'
);
GO

INSERT INTO system_renewals (
  element_name,
  element_category,
  element_vendor,
  element_reference,
  element_auto_renew,
  element_owner,
  element_notes,
  element_status
)
SELECT
  'elideus.net',
  'domain',
  'Name.com',
  'elideus.net',
  0,
  'ROLE_SERVICE_ADMIN',
  'Internal domain',
  1
WHERE NOT EXISTS (
  SELECT 1 FROM system_renewals WHERE element_name = 'elideus.net' AND element_category = 'domain'
);
GO

INSERT INTO system_renewals (
  element_name,
  element_category,
  element_vendor,
  element_reference,
  element_auto_renew,
  element_owner,
  element_notes,
  element_status
)
SELECT
  'Azure Billing Client Secret',
  'secret',
  'Azure',
  'TheOracleRPC-Billing app registration',
  0,
  'ROLE_SERVICE_ADMIN',
  'Service principal client secret for billing API access',
  1
WHERE NOT EXISTS (
  SELECT 1 FROM system_renewals WHERE element_name = 'Azure Billing Client Secret' AND element_category = 'secret'
);
GO

INSERT INTO system_renewals (
  element_name,
  element_category,
  element_vendor,
  element_reference,
  element_renewal_cost,
  element_currency,
  element_auto_renew,
  element_owner,
  element_notes,
  element_status
)
SELECT
  'Claude.ai Max Plan',
  'subscription',
  'Anthropic',
  'claude.ai',
  100.00,
  'USD',
  1,
  'ROLE_SERVICE_ADMIN',
  'Monthly subscription ~$100/mo',
  1
WHERE NOT EXISTS (
  SELECT 1 FROM system_renewals WHERE element_name = 'Claude.ai Max Plan' AND element_category = 'subscription'
);
GO

INSERT INTO system_renewals (
  element_name,
  element_category,
  element_vendor,
  element_reference,
  element_renewal_cost,
  element_currency,
  element_auto_renew,
  element_owner,
  element_notes,
  element_status
)
SELECT
  'ChatGPT Plus',
  'subscription',
  'OpenAI',
  'chatgpt.com',
  20.00,
  'USD',
  1,
  'ROLE_SERVICE_ADMIN',
  'Personal ChatGPT subscription ~$20/mo',
  1
WHERE NOT EXISTS (
  SELECT 1 FROM system_renewals WHERE element_name = 'ChatGPT Plus' AND element_category = 'subscription'
);
GO

INSERT INTO system_renewals (
  element_name,
  element_category,
  element_vendor,
  element_reference,
  element_renewal_cost,
  element_currency,
  element_auto_renew,
  element_owner,
  element_notes,
  element_status
)
SELECT
  'Exchange Online - Elideus Group',
  'subscription',
  'Microsoft',
  'Elideus Group billing account',
  8.00,
  'USD',
  1,
  'ROLE_SERVICE_ADMIN',
  '2x $4 mailbox-only licenses',
  1
WHERE NOT EXISTS (
  SELECT 1 FROM system_renewals WHERE element_name = 'Exchange Online - Elideus Group' AND element_category = 'subscription'
);
GO

INSERT INTO frontend_routes (
  element_enablement,
  element_roles,
  element_sequence,
  element_path,
  element_name,
  element_icon
)
SELECT
  '0',
  4611686018427387904,
  2020,
  '/service-renewals',
  'Renewals',
  'key'
WHERE NOT EXISTS (
  SELECT 1 FROM frontend_routes WHERE element_path = '/service-renewals'
);
GO
