INSERT INTO finance_vendors (
  element_name,
  element_display,
  element_description,
  element_status,
  element_created_on,
  element_modified_on
)
SELECT 'Anthropic', 'Anthropic (Claude)', 'Anthropic Claude AI billing source',
  1, SYSUTCDATETIME(), SYSUTCDATETIME()
WHERE NOT EXISTS (
  SELECT 1 FROM finance_vendors WHERE element_name = 'Anthropic'
);
GO

INSERT INTO finance_vendors (
  element_name,
  element_display,
  element_description,
  element_status,
  element_created_on,
  element_modified_on
)
SELECT 'NameCom', 'Name.com', 'Name.com domain registrar',
  1, SYSUTCDATETIME(), SYSUTCDATETIME()
WHERE NOT EXISTS (
  SELECT 1 FROM finance_vendors WHERE element_name = 'NameCom'
);
GO

INSERT INTO finance_vendors (
  element_name,
  element_display,
  element_description,
  element_status,
  element_created_on,
  element_modified_on
)
SELECT 'Microsoft', 'Microsoft 365', 'Microsoft 365 subscription billing source',
  1, SYSUTCDATETIME(), SYSUTCDATETIME()
WHERE NOT EXISTS (
  SELECT 1 FROM finance_vendors WHERE element_name = 'Microsoft'
);
GO

IF COL_LENGTH('dbo.finance_staging_imports', 'element_requested_by') IS NULL
BEGIN
  ALTER TABLE [dbo].[finance_staging_imports]
  ADD [element_requested_by] NVARCHAR(128) NULL;
END;
GO

IF COL_LENGTH('dbo.finance_staging_imports', 'element_approved_by') IS NULL
BEGIN
  ALTER TABLE [dbo].[finance_staging_imports]
  ADD [element_approved_by] NVARCHAR(128) NULL;
END;
GO

IF COL_LENGTH('dbo.finance_staging_imports', 'element_approved_on') IS NULL
BEGIN
  ALTER TABLE [dbo].[finance_staging_imports]
  ADD [element_approved_on] DATETIMEOFFSET(7) NULL;
END;
GO

DECLARE @imports_table_recid BIGINT;
SELECT @imports_table_recid = recid
FROM system_schema_tables
WHERE element_name = 'finance_staging_imports'
  AND element_schema = 'dbo';

IF NOT EXISTS (
  SELECT 1 FROM system_schema_columns
  WHERE tables_recid = @imports_table_recid
    AND element_name = 'element_requested_by'
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
  VALUES (@imports_table_recid, 8, 'element_requested_by', 13, 1, NULL, 128, 0, 0);
END;

IF NOT EXISTS (
  SELECT 1 FROM system_schema_columns
  WHERE tables_recid = @imports_table_recid
    AND element_name = 'element_approved_by'
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
  VALUES (@imports_table_recid, 8, 'element_approved_by', 14, 1, NULL, 128, 0, 0);
END;

IF NOT EXISTS (
  SELECT 1 FROM system_schema_columns
  WHERE tables_recid = @imports_table_recid
    AND element_name = 'element_approved_on'
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
  VALUES (@imports_table_recid, 7, 'element_approved_on', 15, 1, NULL, NULL, 0, 0);
END;
GO
