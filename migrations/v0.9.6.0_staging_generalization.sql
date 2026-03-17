CREATE TABLE [dbo].[finance_vendors] (
  [recid] BIGINT IDENTITY(1,1) NOT NULL,
  [element_name] NVARCHAR(64) NOT NULL,
  [element_display] NVARCHAR(256) NULL,
  [element_description] NVARCHAR(512) NULL,
  [element_status] TINYINT NOT NULL DEFAULT (1),
  [element_created_on] DATETIMEOFFSET(7) NOT NULL DEFAULT (SYSUTCDATETIME()),
  [element_modified_on] DATETIMEOFFSET(7) NOT NULL DEFAULT (SYSUTCDATETIME()),
  CONSTRAINT [PK_finance_vendors] PRIMARY KEY ([recid]),
  CONSTRAINT [UQ_finance_vendors_element_name] UNIQUE ([element_name])
);
GO

IF OBJECT_ID(N'dbo.finance_staging_cost_details', N'U') IS NOT NULL
BEGIN
  EXEC sp_rename 'dbo.finance_staging_cost_details', 'finance_staging_azure_cost_details';
END;
GO

IF EXISTS (
  SELECT 1
  FROM sys.key_constraints
  WHERE [name] = N'PK_finance_staging_cost_details'
)
BEGIN
  EXEC sp_rename 'dbo.PK_finance_staging_cost_details', 'PK_finance_staging_azure_cost_details', 'OBJECT';
END;
GO

IF EXISTS (
  SELECT 1
  FROM sys.foreign_keys
  WHERE [name] = N'FK_finance_staging_cost_details_imports_recid'
)
BEGIN
  EXEC sp_rename 'dbo.FK_finance_staging_cost_details_imports_recid', 'FK_finance_staging_azure_cost_details_imports_recid', 'OBJECT';
END;
GO

CREATE TABLE [dbo].[finance_staging_line_items] (
  [recid] BIGINT IDENTITY(1,1) NOT NULL,
  [imports_recid] BIGINT NOT NULL,
  [vendors_recid] BIGINT NOT NULL,
  [element_date] DATE NULL,
  [element_service] NVARCHAR(256) NULL,
  [element_category] NVARCHAR(256) NULL,
  [element_description] NVARCHAR(512) NULL,
  [element_quantity] DECIMAL(19,5) NULL,
  [element_unit_price] DECIMAL(19,5) NULL,
  [element_amount] DECIMAL(19,5) NOT NULL DEFAULT (0),
  [element_currency] NVARCHAR(10) NULL,
  [element_raw_json] NVARCHAR(MAX) NULL,
  [element_created_on] DATETIMEOFFSET(7) NOT NULL DEFAULT (SYSUTCDATETIME()),
  CONSTRAINT [PK_finance_staging_line_items] PRIMARY KEY ([recid]),
  CONSTRAINT [FK_finance_staging_line_items_imports_recid] FOREIGN KEY ([imports_recid])
    REFERENCES [dbo].[finance_staging_imports] ([recid]),
  CONSTRAINT [FK_finance_staging_line_items_vendors_recid] FOREIGN KEY ([vendors_recid])
    REFERENCES [dbo].[finance_vendors] ([recid])
);
GO

CREATE INDEX [IX_finance_staging_line_items_imports_recid]
  ON [dbo].[finance_staging_line_items] ([imports_recid]);
CREATE INDEX [IX_finance_staging_line_items_vendors_date]
  ON [dbo].[finance_staging_line_items] ([vendors_recid], [element_date]);
CREATE INDEX [IX_finance_staging_line_items_service_category]
  ON [dbo].[finance_staging_line_items] ([element_service], [element_category]);
GO

ALTER TABLE [dbo].[finance_staging_account_map]
ADD [vendors_recid] BIGINT NULL;
GO

ALTER TABLE [dbo].[finance_staging_account_map]
ADD CONSTRAINT [FK_finance_staging_account_map_vendors_recid]
  FOREIGN KEY ([vendors_recid]) REFERENCES [dbo].[finance_vendors] ([recid]);
GO

DROP INDEX [UQ_finance_staging_account_map_service_meter]
ON [dbo].[finance_staging_account_map];
GO

CREATE UNIQUE INDEX [UQ_finance_staging_account_map_vendor_service_meter]
  ON [dbo].[finance_staging_account_map] ([vendors_recid], [element_service_pattern], [element_meter_pattern]);
GO

INSERT INTO finance_vendors (
  element_name,
  element_display,
  element_description,
  element_status,
  element_created_on,
  element_modified_on
)
SELECT 'Azure', 'Microsoft Azure', 'Microsoft Azure billing source', 1, SYSUTCDATETIME(), SYSUTCDATETIME()
WHERE NOT EXISTS (
  SELECT 1 FROM finance_vendors WHERE element_name = 'Azure'
);

INSERT INTO finance_vendors (
  element_name,
  element_display,
  element_description,
  element_status,
  element_created_on,
  element_modified_on
)
SELECT 'OpenAI', 'OpenAI API', 'OpenAI API billing source', 1, SYSUTCDATETIME(), SYSUTCDATETIME()
WHERE NOT EXISTS (
  SELECT 1 FROM finance_vendors WHERE element_name = 'OpenAI'
);

INSERT INTO finance_vendors (
  element_name,
  element_display,
  element_description,
  element_status,
  element_created_on,
  element_modified_on
)
SELECT 'Luma', 'Luma Labs API', 'Luma Labs API billing source', 1, SYSUTCDATETIME(), SYSUTCDATETIME()
WHERE NOT EXISTS (
  SELECT 1 FROM finance_vendors WHERE element_name = 'Luma'
);
GO

UPDATE map
SET vendors_recid = vendor.recid
FROM finance_staging_account_map AS map
INNER JOIN finance_vendors AS vendor
  ON vendor.element_name = 'Azure'
WHERE map.vendors_recid IS NULL;
GO


INSERT INTO system_schema_tables (element_name, element_schema)
SELECT v.element_name, v.element_schema
FROM (VALUES
  ('finance_vendors', 'dbo'),
  ('finance_staging_line_items', 'dbo')
) v(element_name, element_schema)
WHERE NOT EXISTS (
  SELECT 1 FROM system_schema_tables t
  WHERE t.element_name = v.element_name AND t.element_schema = v.element_schema
);
GO

UPDATE system_schema_tables
SET element_name = 'finance_staging_azure_cost_details'
WHERE element_schema = 'dbo'
  AND element_name = 'finance_staging_cost_details';
GO

DECLARE @vendors_table_recid BIGINT;
SELECT @vendors_table_recid = recid
FROM system_schema_tables
WHERE element_name = 'finance_vendors'
  AND element_schema = 'dbo';

DELETE c FROM system_schema_columns c WHERE c.tables_recid = @vendors_table_recid;
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
  (@vendors_table_recid, 3, 'recid', 1, 0, NULL, NULL, 1, 1),
  (@vendors_table_recid, 8, 'element_name', 2, 0, NULL, 64, 0, 0),
  (@vendors_table_recid, 8, 'element_display', 3, 1, NULL, 256, 0, 0),
  (@vendors_table_recid, 8, 'element_description', 4, 1, NULL, 512, 0, 0),
  (@vendors_table_recid, 11, 'element_status', 5, 0, '(1)', NULL, 0, 0),
  (@vendors_table_recid, 7, 'element_created_on', 6, 0, '(sysutcdatetime())', NULL, 0, 0),
  (@vendors_table_recid, 7, 'element_modified_on', 7, 0, '(sysutcdatetime())', NULL, 0, 0);
GO

DECLARE @line_items_table_recid BIGINT;
SELECT @line_items_table_recid = recid
FROM system_schema_tables
WHERE element_name = 'finance_staging_line_items'
  AND element_schema = 'dbo';

DELETE c FROM system_schema_columns c WHERE c.tables_recid = @line_items_table_recid;
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
  (@line_items_table_recid, 3, 'recid', 1, 0, NULL, NULL, 1, 1),
  (@line_items_table_recid, 2, 'imports_recid', 2, 0, NULL, NULL, 0, 0),
  (@line_items_table_recid, 2, 'vendors_recid', 3, 0, NULL, NULL, 0, 0),
  (@line_items_table_recid, 12, 'element_date', 4, 1, NULL, NULL, 0, 0),
  (@line_items_table_recid, 8, 'element_service', 5, 1, NULL, 256, 0, 0),
  (@line_items_table_recid, 8, 'element_category', 6, 1, NULL, 256, 0, 0),
  (@line_items_table_recid, 8, 'element_description', 7, 1, NULL, 512, 0, 0),
  (@line_items_table_recid, 13, 'element_quantity', 8, 1, NULL, NULL, 0, 0),
  (@line_items_table_recid, 13, 'element_unit_price', 9, 1, NULL, NULL, 0, 0),
  (@line_items_table_recid, 13, 'element_amount', 10, 0, '(0)', NULL, 0, 0),
  (@line_items_table_recid, 8, 'element_currency', 11, 1, NULL, 10, 0, 0),
  (@line_items_table_recid, 9, 'element_raw_json', 12, 1, NULL, NULL, 0, 0),
  (@line_items_table_recid, 7, 'element_created_on', 13, 0, '(sysutcdatetime())', NULL, 0, 0);
GO

DECLARE @account_map_table_recid BIGINT;
SELECT @account_map_table_recid = recid
FROM system_schema_tables
WHERE element_name = 'finance_staging_account_map'
  AND element_schema = 'dbo';

DELETE c FROM system_schema_columns c WHERE c.tables_recid = @account_map_table_recid;
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
  (@account_map_table_recid, 3, 'recid', 1, 0, NULL, NULL, 1, 1),
  (@account_map_table_recid, 2, 'vendors_recid', 2, 1, NULL, NULL, 0, 0),
  (@account_map_table_recid, 8, 'element_service_pattern', 3, 0, NULL, 256, 0, 0),
  (@account_map_table_recid, 8, 'element_meter_pattern', 4, 1, NULL, 256, 0, 0),
  (@account_map_table_recid, 4, 'accounts_guid', 5, 0, NULL, NULL, 0, 0),
  (@account_map_table_recid, 1, 'element_priority', 6, 0, '(0)', NULL, 0, 0),
  (@account_map_table_recid, 8, 'element_description', 7, 1, NULL, 512, 0, 0),
  (@account_map_table_recid, 11, 'element_status', 8, 0, '(1)', NULL, 0, 0),
  (@account_map_table_recid, 7, 'element_created_on', 9, 0, '(sysutcdatetime())', NULL, 0, 0),
  (@account_map_table_recid, 7, 'element_modified_on', 10, 0, '(sysutcdatetime())', NULL, 0, 0);
GO

DELETE i
FROM system_schema_indexes i
INNER JOIN system_schema_tables t ON t.recid = i.tables_recid
WHERE t.element_schema = 'dbo'
  AND t.element_name IN (
    'finance_vendors',
    'finance_staging_line_items',
    'finance_staging_account_map'
  );

INSERT INTO system_schema_indexes (tables_recid, element_name, element_columns, element_is_unique)
VALUES
  ((SELECT recid FROM system_schema_tables WHERE element_name = 'finance_vendors' AND element_schema = 'dbo'), 'UQ_finance_vendors_element_name', 'element_name', 1),
  ((SELECT recid FROM system_schema_tables WHERE element_name = 'finance_staging_line_items' AND element_schema = 'dbo'), 'IX_finance_staging_line_items_imports_recid', 'imports_recid', 0),
  ((SELECT recid FROM system_schema_tables WHERE element_name = 'finance_staging_line_items' AND element_schema = 'dbo'), 'IX_finance_staging_line_items_vendors_date', 'vendors_recid,element_date', 0),
  ((SELECT recid FROM system_schema_tables WHERE element_name = 'finance_staging_line_items' AND element_schema = 'dbo'), 'IX_finance_staging_line_items_service_category', 'element_service,element_category', 0),
  ((SELECT recid FROM system_schema_tables WHERE element_name = 'finance_staging_account_map' AND element_schema = 'dbo'), 'UQ_finance_staging_account_map_vendor_service_meter', 'vendors_recid,element_service_pattern,element_meter_pattern', 1);
GO

DELETE fk
FROM system_schema_foreign_keys fk
INNER JOIN system_schema_tables t ON t.recid = fk.tables_recid
WHERE t.element_schema = 'dbo'
  AND t.element_name IN (
    'finance_staging_line_items',
    'finance_staging_account_map'
  );

INSERT INTO system_schema_foreign_keys (
  tables_recid,
  element_column_name,
  referenced_tables_recid,
  element_referenced_column
)
VALUES
  (
    (SELECT recid FROM system_schema_tables WHERE element_name = 'finance_staging_line_items' AND element_schema = 'dbo'),
    'imports_recid',
    (SELECT recid FROM system_schema_tables WHERE element_name = 'finance_staging_imports' AND element_schema = 'dbo'),
    'recid'
  ),
  (
    (SELECT recid FROM system_schema_tables WHERE element_name = 'finance_staging_line_items' AND element_schema = 'dbo'),
    'vendors_recid',
    (SELECT recid FROM system_schema_tables WHERE element_name = 'finance_vendors' AND element_schema = 'dbo'),
    'recid'
  ),
  (
    (SELECT recid FROM system_schema_tables WHERE element_name = 'finance_staging_account_map' AND element_schema = 'dbo'),
    'accounts_guid',
    (SELECT recid FROM system_schema_tables WHERE element_name = 'finance_accounts' AND element_schema = 'dbo'),
    'element_guid'
  ),
  (
    (SELECT recid FROM system_schema_tables WHERE element_name = 'finance_staging_account_map' AND element_schema = 'dbo'),
    'vendors_recid',
    (SELECT recid FROM system_schema_tables WHERE element_name = 'finance_vendors' AND element_schema = 'dbo'),
    'recid'
  );
GO
