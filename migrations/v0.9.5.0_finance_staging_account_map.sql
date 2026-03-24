CREATE TABLE [dbo].[finance_staging_account_map] (
  [recid] BIGINT IDENTITY(1,1) NOT NULL,
  [element_service_pattern] NVARCHAR(256) NOT NULL,
  [element_meter_pattern] NVARCHAR(256) NULL,
  [accounts_guid] UNIQUEIDENTIFIER NOT NULL,
  [element_priority] INT NOT NULL DEFAULT (0),
  [element_description] NVARCHAR(512) NULL,
  [element_status] TINYINT NOT NULL DEFAULT (1),
  [element_created_on] DATETIMEOFFSET(7) NOT NULL DEFAULT (SYSUTCDATETIME()),
  [element_modified_on] DATETIMEOFFSET(7) NOT NULL DEFAULT (SYSUTCDATETIME()),
  CONSTRAINT [PK_finance_staging_account_map] PRIMARY KEY ([recid]),
  CONSTRAINT [FK_finance_staging_account_map_accounts_guid] FOREIGN KEY ([accounts_guid])
    REFERENCES [dbo].[finance_accounts] ([element_guid])
);

CREATE UNIQUE INDEX [UQ_finance_staging_account_map_service_meter]
  ON [dbo].[finance_staging_account_map] ([element_service_pattern], [element_meter_pattern]);
GO

-- Reflection metadata registration (table + column + index + foreign key)
INSERT INTO system_schema_tables (element_name, element_schema)
SELECT v.element_name, v.element_schema
FROM (VALUES
  ('finance_staging_account_map', 'dbo')
) v(element_name, element_schema)
WHERE NOT EXISTS (
  SELECT 1 FROM system_schema_tables t
  WHERE t.element_name = v.element_name AND t.element_schema = v.element_schema
);

DECLARE @table_recid BIGINT;
SELECT @table_recid = recid
FROM system_schema_tables
WHERE element_name = 'finance_staging_account_map'
  AND element_schema = 'dbo';

DELETE c
FROM system_schema_columns c
WHERE c.tables_recid = @table_recid;

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
  (@table_recid, 3, 'recid', 1, 0, NULL, NULL, 1, 1),
  (@table_recid, 8, 'element_service_pattern', 2, 0, NULL, 256, 0, 0),
  (@table_recid, 8, 'element_meter_pattern', 3, 1, NULL, 256, 0, 0),
  (@table_recid, 4, 'accounts_guid', 4, 0, NULL, NULL, 0, 0),
  (@table_recid, 1, 'element_priority', 5, 0, '(0)', NULL, 0, 0),
  (@table_recid, 8, 'element_description', 6, 1, NULL, 512, 0, 0),
  (@table_recid, 11, 'element_status', 7, 0, '(1)', NULL, 0, 0),
  (@table_recid, 7, 'element_created_on', 8, 0, '(sysutcdatetime())', NULL, 0, 0),
  (@table_recid, 7, 'element_modified_on', 9, 0, '(sysutcdatetime())', NULL, 0, 0);

DELETE i
FROM system_schema_indexes i
INNER JOIN system_schema_tables t ON t.recid = i.tables_recid
WHERE t.element_schema = 'dbo'
  AND t.element_name IN ('finance_staging_account_map');

INSERT INTO system_schema_indexes (tables_recid, element_name, element_columns, element_is_unique)
VALUES
  ((SELECT recid FROM system_schema_tables WHERE element_name = 'finance_staging_account_map' AND element_schema = 'dbo'), 'UQ_finance_staging_account_map_service_meter', 'element_service_pattern,element_meter_pattern', 1);

DELETE fk
FROM system_schema_foreign_keys fk
INNER JOIN system_schema_tables t ON t.recid = fk.tables_recid
WHERE t.element_schema = 'dbo'
  AND t.element_name = 'finance_staging_account_map';

INSERT INTO system_schema_foreign_keys (
  tables_recid,
  element_column_name,
  referenced_tables_recid,
  element_referenced_column
)
VALUES (
  (SELECT recid FROM system_schema_tables WHERE element_name = 'finance_staging_account_map' AND element_schema = 'dbo'),
  'accounts_guid',
  (SELECT recid FROM system_schema_tables WHERE element_name = 'finance_accounts' AND element_schema = 'dbo'),
  'element_guid'
);
GO

-- Seed service-to-account defaults
INSERT INTO finance_staging_account_map (
  element_service_pattern,
  element_meter_pattern,
  accounts_guid,
  element_priority,
  element_description,
  element_status,
  element_created_on,
  element_modified_on
)
SELECT
  seed.element_service_pattern,
  seed.element_meter_pattern,
  account.element_guid,
  seed.element_priority,
  seed.element_description,
  1,
  SYSUTCDATETIME(),
  SYSUTCDATETIME()
FROM (
  VALUES
    ('Microsoft.Web', NULL, '5110', 10, 'Azure App Service'),
    ('Microsoft.Sql', NULL, '5120', 10, 'Azure SQL Database'),
    ('Microsoft.Storage', NULL, '5130', 10, 'Azure Storage'),
    ('Microsoft.ContainerRegistry', NULL, '5140', 10, 'Azure Container Registry'),
    ('Microsoft.Network', NULL, '5150', 10, 'Azure Networking'),
    ('*', NULL, '5100', 0, 'Catch-all for unmapped services')
) seed(element_service_pattern, element_meter_pattern, element_number, element_priority, element_description)
INNER JOIN finance_accounts AS account
  ON account.element_number = seed.element_number
WHERE NOT EXISTS (
  SELECT 1
  FROM finance_staging_account_map existing
  WHERE existing.element_service_pattern = seed.element_service_pattern
    AND (
      (existing.element_meter_pattern IS NULL AND seed.element_meter_pattern IS NULL)
      OR existing.element_meter_pattern = seed.element_meter_pattern
    )
);
GO
