INSERT INTO dbo.system_edt_mappings
  (
    element_name,
    element_mssql_type,
    element_postgresql_type,
    element_mysql_type,
    element_python_type,
    element_odbc_type_code,
    element_max_length,
    element_notes
  )
SELECT
  'DICT',
  'nvarchar(max)',
  'jsonb',
  'json',
  'dict',
  -10,
  NULL,
  'JSON object type. Python dict, TypeScript Record<string, any>. Stored as serialized JSON text in SQL.'
WHERE NOT EXISTS (
  SELECT 1 FROM dbo.system_edt_mappings WHERE element_name = 'DICT'
);
GO

DECLARE @edt_dict BIGINT = (
  SELECT recid FROM dbo.system_edt_mappings WHERE element_name = 'DICT'
);
GO

IF OBJECT_ID(N'dbo.system_schema_rpc_models', N'U') IS NULL
BEGIN
  CREATE TABLE [dbo].[system_schema_rpc_models] (
    [recid] BIGINT IDENTITY(1,1) NOT NULL,
    [element_name] NVARCHAR(256) NOT NULL,
    [element_domain] NVARCHAR(64) NOT NULL,
    [element_subdomain] NVARCHAR(64) NOT NULL,
    [element_version] INT NOT NULL CONSTRAINT [DF_system_schema_rpc_models_element_version] DEFAULT (1),
    [element_kind] NVARCHAR(16) NOT NULL,
    [element_parent_recid] BIGINT NULL,
    [element_security_roles] BIGINT NOT NULL CONSTRAINT [DF_system_schema_rpc_models_element_security_roles] DEFAULT (0),
    [element_entitlements] BIGINT NOT NULL CONSTRAINT [DF_system_schema_rpc_models_element_entitlements] DEFAULT (0),
    [element_app_version] NVARCHAR(32) NULL,
    [element_description] NVARCHAR(1024) NULL,
    [element_created_on] DATETIMEOFFSET(7) NOT NULL CONSTRAINT [DF_system_schema_rpc_models_element_created_on] DEFAULT (SYSUTCDATETIME()),
    [element_modified_on] DATETIMEOFFSET(7) NOT NULL CONSTRAINT [DF_system_schema_rpc_models_element_modified_on] DEFAULT (SYSUTCDATETIME()),
    CONSTRAINT [PK_system_schema_rpc_models] PRIMARY KEY ([recid]),
    CONSTRAINT [UQ_system_schema_rpc_models_fqn] UNIQUE ([element_domain], [element_subdomain], [element_name])
  );
END;
GO

IF NOT EXISTS (
  SELECT 1
  FROM sys.foreign_keys
  WHERE name = N'FK_system_schema_rpc_models_parent'
    AND parent_object_id = OBJECT_ID(N'dbo.system_schema_rpc_models')
)
BEGIN
  ALTER TABLE [dbo].[system_schema_rpc_models]
    ADD CONSTRAINT [FK_system_schema_rpc_models_parent]
    FOREIGN KEY ([element_parent_recid]) REFERENCES [dbo].[system_schema_rpc_models]([recid]);
END;
GO

IF OBJECT_ID(N'dbo.system_schema_rpc_model_fields', N'U') IS NULL
BEGIN
  CREATE TABLE [dbo].[system_schema_rpc_model_fields] (
    [recid] BIGINT IDENTITY(1,1) NOT NULL,
    [models_recid] BIGINT NOT NULL,
    [edt_recid] BIGINT NOT NULL,
    [element_name] NVARCHAR(128) NOT NULL,
    [element_ordinal] INT NOT NULL,
    [element_nullable] BIT NOT NULL CONSTRAINT [DF_system_schema_rpc_model_fields_element_nullable] DEFAULT (0),
    [element_default] NVARCHAR(512) NULL,
    [element_max_length] INT NULL,
    [element_is_list] BIT NOT NULL CONSTRAINT [DF_system_schema_rpc_model_fields_element_is_list] DEFAULT (0),
    [element_nested_model_recid] BIGINT NULL,
    [element_description] NVARCHAR(1024) NULL,
    [element_created_on] DATETIMEOFFSET(7) NOT NULL CONSTRAINT [DF_system_schema_rpc_model_fields_element_created_on] DEFAULT (SYSUTCDATETIME()),
    [element_modified_on] DATETIMEOFFSET(7) NOT NULL CONSTRAINT [DF_system_schema_rpc_model_fields_element_modified_on] DEFAULT (SYSUTCDATETIME()),
    CONSTRAINT [PK_system_schema_rpc_model_fields] PRIMARY KEY ([recid]),
    CONSTRAINT [UQ_system_schema_rpc_model_fields_model_name] UNIQUE ([models_recid], [element_name])
  );
END;
GO

IF NOT EXISTS (
  SELECT 1
  FROM sys.foreign_keys
  WHERE name = N'FK_system_schema_rpc_model_fields_model'
    AND parent_object_id = OBJECT_ID(N'dbo.system_schema_rpc_model_fields')
)
BEGIN
  ALTER TABLE [dbo].[system_schema_rpc_model_fields]
    ADD CONSTRAINT [FK_system_schema_rpc_model_fields_model]
    FOREIGN KEY ([models_recid]) REFERENCES [dbo].[system_schema_rpc_models]([recid]);
END;
GO

IF NOT EXISTS (
  SELECT 1
  FROM sys.foreign_keys
  WHERE name = N'FK_system_schema_rpc_model_fields_edt'
    AND parent_object_id = OBJECT_ID(N'dbo.system_schema_rpc_model_fields')
)
BEGIN
  ALTER TABLE [dbo].[system_schema_rpc_model_fields]
    ADD CONSTRAINT [FK_system_schema_rpc_model_fields_edt]
    FOREIGN KEY ([edt_recid]) REFERENCES [dbo].[system_edt_mappings]([recid]);
END;
GO

IF NOT EXISTS (
  SELECT 1
  FROM sys.foreign_keys
  WHERE name = N'FK_system_schema_rpc_model_fields_nested'
    AND parent_object_id = OBJECT_ID(N'dbo.system_schema_rpc_model_fields')
)
BEGIN
  ALTER TABLE [dbo].[system_schema_rpc_model_fields]
    ADD CONSTRAINT [FK_system_schema_rpc_model_fields_nested]
    FOREIGN KEY ([element_nested_model_recid]) REFERENCES [dbo].[system_schema_rpc_models]([recid]);
END;
GO

IF NOT EXISTS (
  SELECT 1
  FROM sys.indexes
  WHERE name = N'IX_system_schema_rpc_model_fields_model_ordinal'
    AND object_id = OBJECT_ID(N'dbo.system_schema_rpc_model_fields')
)
BEGIN
  CREATE NONCLUSTERED INDEX [IX_system_schema_rpc_model_fields_model_ordinal]
    ON [dbo].[system_schema_rpc_model_fields] ([models_recid], [element_ordinal]);
END;
GO

INSERT INTO dbo.system_schema_tables (element_name, element_schema)
SELECT 'system_schema_rpc_models', 'dbo'
WHERE NOT EXISTS (
  SELECT 1
  FROM dbo.system_schema_tables
  WHERE element_name = 'system_schema_rpc_models'
    AND element_schema = 'dbo'
);
GO

INSERT INTO dbo.system_schema_tables (element_name, element_schema)
SELECT 'system_schema_rpc_model_fields', 'dbo'
WHERE NOT EXISTS (
  SELECT 1
  FROM dbo.system_schema_tables
  WHERE element_name = 'system_schema_rpc_model_fields'
    AND element_schema = 'dbo'
);
GO

DECLARE @t_rpc_models BIGINT = (
  SELECT recid
  FROM dbo.system_schema_tables
  WHERE element_name = 'system_schema_rpc_models'
    AND element_schema = 'dbo'
);
DECLARE @t_rpc_model_fields BIGINT = (
  SELECT recid
  FROM dbo.system_schema_tables
  WHERE element_name = 'system_schema_rpc_model_fields'
    AND element_schema = 'dbo'
);

DELETE FROM dbo.system_schema_columns WHERE tables_recid IN (@t_rpc_models, @t_rpc_model_fields);

INSERT INTO dbo.system_schema_columns
  (
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
  (@t_rpc_models, 3, 'recid', 1, 0, NULL, NULL, 1, 1),
  (@t_rpc_models, 8, 'element_name', 2, 0, NULL, 256, 0, 0),
  (@t_rpc_models, 8, 'element_domain', 3, 0, NULL, 64, 0, 0),
  (@t_rpc_models, 8, 'element_subdomain', 4, 0, NULL, 64, 0, 0),
  (@t_rpc_models, 1, 'element_version', 5, 0, '1', NULL, 0, 0),
  (@t_rpc_models, 8, 'element_kind', 6, 0, NULL, 16, 0, 0),
  (@t_rpc_models, 2, 'element_parent_recid', 7, 1, NULL, NULL, 0, 0),
  (@t_rpc_models, 2, 'element_security_roles', 8, 0, '0', NULL, 0, 0),
  (@t_rpc_models, 2, 'element_entitlements', 9, 0, '0', NULL, 0, 0),
  (@t_rpc_models, 8, 'element_app_version', 10, 1, NULL, 32, 0, 0),
  (@t_rpc_models, 8, 'element_description', 11, 1, NULL, 1024, 0, 0),
  (@t_rpc_models, 7, 'element_created_on', 12, 0, '(sysutcdatetime())', NULL, 0, 0),
  (@t_rpc_models, 7, 'element_modified_on', 13, 0, '(sysutcdatetime())', NULL, 0, 0),
  (@t_rpc_model_fields, 3, 'recid', 1, 0, NULL, NULL, 1, 1),
  (@t_rpc_model_fields, 2, 'models_recid', 2, 0, NULL, NULL, 0, 0),
  (@t_rpc_model_fields, 2, 'edt_recid', 3, 0, NULL, NULL, 0, 0),
  (@t_rpc_model_fields, 8, 'element_name', 4, 0, NULL, 128, 0, 0),
  (@t_rpc_model_fields, 1, 'element_ordinal', 5, 0, NULL, NULL, 0, 0),
  (@t_rpc_model_fields, 5, 'element_nullable', 6, 0, '(0)', NULL, 0, 0),
  (@t_rpc_model_fields, 8, 'element_default', 7, 1, NULL, 512, 0, 0),
  (@t_rpc_model_fields, 1, 'element_max_length', 8, 1, NULL, NULL, 0, 0),
  (@t_rpc_model_fields, 5, 'element_is_list', 9, 0, '(0)', NULL, 0, 0),
  (@t_rpc_model_fields, 2, 'element_nested_model_recid', 10, 1, NULL, NULL, 0, 0),
  (@t_rpc_model_fields, 8, 'element_description', 11, 1, NULL, 1024, 0, 0),
  (@t_rpc_model_fields, 7, 'element_created_on', 12, 0, '(sysutcdatetime())', NULL, 0, 0),
  (@t_rpc_model_fields, 7, 'element_modified_on', 13, 0, '(sysutcdatetime())', NULL, 0, 0);
GO

DELETE i
FROM dbo.system_schema_indexes i
WHERE i.tables_recid IN (
  SELECT recid FROM dbo.system_schema_tables
  WHERE element_schema = 'dbo'
    AND element_name IN ('system_schema_rpc_models', 'system_schema_rpc_model_fields')
)
AND i.element_name IN (
  'UQ_system_schema_rpc_models_fqn',
  'UQ_system_schema_rpc_model_fields_model_name',
  'IX_system_schema_rpc_model_fields_model_ordinal'
);

INSERT INTO dbo.system_schema_indexes
  (tables_recid, element_name, element_columns, element_is_unique)
VALUES
  (
    (SELECT recid FROM dbo.system_schema_tables WHERE element_name = 'system_schema_rpc_models' AND element_schema = 'dbo'),
    'UQ_system_schema_rpc_models_fqn',
    'element_domain,element_subdomain,element_name',
    1
  ),
  (
    (SELECT recid FROM dbo.system_schema_tables WHERE element_name = 'system_schema_rpc_model_fields' AND element_schema = 'dbo'),
    'UQ_system_schema_rpc_model_fields_model_name',
    'models_recid,element_name',
    1
  ),
  (
    (SELECT recid FROM dbo.system_schema_tables WHERE element_name = 'system_schema_rpc_model_fields' AND element_schema = 'dbo'),
    'IX_system_schema_rpc_model_fields_model_ordinal',
    'models_recid,element_ordinal',
    0
  );
GO

DELETE fk
FROM dbo.system_schema_foreign_keys fk
WHERE fk.tables_recid IN (
  SELECT recid FROM dbo.system_schema_tables
  WHERE element_schema = 'dbo'
    AND element_name IN ('system_schema_rpc_models', 'system_schema_rpc_model_fields')
)
AND fk.element_column_name IN (
  'element_parent_recid',
  'models_recid',
  'edt_recid',
  'element_nested_model_recid'
);

INSERT INTO dbo.system_schema_foreign_keys
  (tables_recid, element_column_name, referenced_tables_recid, element_referenced_column)
VALUES
  (
    (SELECT recid FROM dbo.system_schema_tables WHERE element_name = 'system_schema_rpc_models' AND element_schema = 'dbo'),
    'element_parent_recid',
    (SELECT recid FROM dbo.system_schema_tables WHERE element_name = 'system_schema_rpc_models' AND element_schema = 'dbo'),
    'recid'
  ),
  (
    (SELECT recid FROM dbo.system_schema_tables WHERE element_name = 'system_schema_rpc_model_fields' AND element_schema = 'dbo'),
    'models_recid',
    (SELECT recid FROM dbo.system_schema_tables WHERE element_name = 'system_schema_rpc_models' AND element_schema = 'dbo'),
    'recid'
  ),
  (
    (SELECT recid FROM dbo.system_schema_tables WHERE element_name = 'system_schema_rpc_model_fields' AND element_schema = 'dbo'),
    'edt_recid',
    (SELECT recid FROM dbo.system_schema_tables WHERE element_name = 'system_edt_mappings' AND element_schema = 'dbo'),
    'recid'
  ),
  (
    (SELECT recid FROM dbo.system_schema_tables WHERE element_name = 'system_schema_rpc_model_fields' AND element_schema = 'dbo'),
    'element_nested_model_recid',
    (SELECT recid FROM dbo.system_schema_tables WHERE element_name = 'system_schema_rpc_models' AND element_schema = 'dbo'),
    'recid'
  );
GO
