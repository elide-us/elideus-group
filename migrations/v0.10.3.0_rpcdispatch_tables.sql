SET NOCOUNT ON;
GO
IF NOT EXISTS (SELECT 1 FROM system_edt_mappings WHERE recid = 15)
BEGIN
  SET IDENTITY_INSERT system_edt_mappings ON;
  INSERT INTO system_edt_mappings (recid, element_name, element_mssql_type, element_postgresql_type, element_mysql_type, element_python_type, element_odbc_type_code, element_max_length, element_notes, element_created_on, element_modified_on)
  VALUES (15, 'JSON', 'nvarchar(max)', 'jsonb', 'json', 'dict', -10, NULL, 'JSON document stored as text. MSSQL nvarchar(max), PostgreSQL jsonb, MySQL json.', SYSUTCDATETIME(), SYSUTCDATETIME());
  SET IDENTITY_INSERT system_edt_mappings OFF;
END;
GO
IF OBJECT_ID('dbo.reflection_rpc_domains','U') IS NULL
BEGIN
  CREATE TABLE reflection_rpc_domains (
    recid bigint IDENTITY(1,1) NOT NULL,
    element_name nvarchar(64) NOT NULL,
    element_required_role nvarchar(128) NULL,
    element_is_auth_exempt bit NOT NULL DEFAULT 0,
    element_is_public bit NOT NULL DEFAULT 0,
    element_is_discord bit NOT NULL DEFAULT 0,
    element_status int NOT NULL DEFAULT 1,
    element_app_version nvarchar(32) NULL,
    element_iteration int NOT NULL DEFAULT 1,
    element_created_on datetimeoffset(7) NOT NULL DEFAULT SYSUTCDATETIME(),
    element_modified_on datetimeoffset(7) NOT NULL DEFAULT SYSUTCDATETIME(),
    CONSTRAINT PK_reflection_rpc_domains PRIMARY KEY CLUSTERED (recid),
    CONSTRAINT UQ_reflection_rpc_domains_name UNIQUE (element_name)
  );
END;
GO
IF OBJECT_ID('dbo.reflection_rpc_subdomains','U') IS NULL
BEGIN
  CREATE TABLE reflection_rpc_subdomains (
    recid bigint IDENTITY(1,1) NOT NULL,
    domains_recid bigint NOT NULL,
    element_name nvarchar(64) NOT NULL,
    element_entitlement_mask bigint NOT NULL DEFAULT 0,
    element_status int NOT NULL DEFAULT 1,
    element_app_version nvarchar(32) NULL,
    element_iteration int NOT NULL DEFAULT 1,
    element_created_on datetimeoffset(7) NOT NULL DEFAULT SYSUTCDATETIME(),
    element_modified_on datetimeoffset(7) NOT NULL DEFAULT SYSUTCDATETIME(),
    CONSTRAINT PK_reflection_rpc_subdomains PRIMARY KEY CLUSTERED (recid),
    CONSTRAINT FK_reflection_rpc_subdomains_domains FOREIGN KEY (domains_recid) REFERENCES reflection_rpc_domains(recid),
    CONSTRAINT UQ_reflection_rpc_subdomains_name UNIQUE (domains_recid, element_name)
  );
END;
GO
IF OBJECT_ID('dbo.reflection_rpc_models','U') IS NULL
BEGIN
  CREATE TABLE reflection_rpc_models (
    recid bigint IDENTITY(1,1) NOT NULL,
    element_name nvarchar(128) NOT NULL,
    element_domain nvarchar(64) NOT NULL,
    element_subdomain nvarchar(64) NOT NULL,
    element_version int NOT NULL DEFAULT 1,
    element_parent_recid bigint NULL,
    element_status int NOT NULL DEFAULT 1,
    element_app_version nvarchar(32) NULL,
    element_iteration int NOT NULL DEFAULT 1,
    element_created_on datetimeoffset(7) NOT NULL DEFAULT SYSUTCDATETIME(),
    element_modified_on datetimeoffset(7) NOT NULL DEFAULT SYSUTCDATETIME(),
    CONSTRAINT PK_reflection_rpc_models PRIMARY KEY CLUSTERED (recid),
    CONSTRAINT FK_reflection_rpc_models_parent FOREIGN KEY (element_parent_recid) REFERENCES reflection_rpc_models(recid),
    CONSTRAINT UQ_reflection_rpc_models_name UNIQUE (element_name)
  );
END;
GO
IF OBJECT_ID('dbo.reflection_rpc_model_fields','U') IS NULL
BEGIN
  CREATE TABLE reflection_rpc_model_fields (
    recid bigint IDENTITY(1,1) NOT NULL,
    models_recid bigint NOT NULL,
    element_name nvarchar(128) NOT NULL,
    element_edt_recid bigint NULL,
    element_is_nullable bit NOT NULL DEFAULT 0,
    element_is_list bit NOT NULL DEFAULT 0,
    element_is_dict bit NOT NULL DEFAULT 0,
    element_ref_model_recid bigint NULL,
    element_default_value nvarchar(256) NULL,
    element_max_length int NULL,
    element_sort_order int NOT NULL DEFAULT 0,
    element_status int NOT NULL DEFAULT 1,
    element_created_on datetimeoffset(7) NOT NULL DEFAULT SYSUTCDATETIME(),
    element_modified_on datetimeoffset(7) NOT NULL DEFAULT SYSUTCDATETIME(),
    CONSTRAINT PK_reflection_rpc_model_fields PRIMARY KEY CLUSTERED (recid),
    CONSTRAINT FK_reflection_rpc_model_fields_models FOREIGN KEY (models_recid) REFERENCES reflection_rpc_models(recid),
    CONSTRAINT FK_reflection_rpc_model_fields_edt FOREIGN KEY (element_edt_recid) REFERENCES system_edt_mappings(recid),
    CONSTRAINT FK_reflection_rpc_model_fields_ref FOREIGN KEY (element_ref_model_recid) REFERENCES reflection_rpc_models(recid),
    CONSTRAINT UQ_reflection_rpc_model_fields_name UNIQUE (models_recid, element_name)
  );
END;
GO
IF OBJECT_ID('dbo.reflection_rpc_functions','U') IS NULL
BEGIN
  CREATE TABLE reflection_rpc_functions (
    recid bigint IDENTITY(1,1) NOT NULL,
    subdomains_recid bigint NOT NULL,
    element_name nvarchar(128) NOT NULL,
    element_version int NOT NULL DEFAULT 1,
    element_module_attr nvarchar(128) NOT NULL,
    element_method_name nvarchar(128) NOT NULL,
    element_request_model_recid bigint NULL,
    element_response_model_recid bigint NULL,
    element_status int NOT NULL DEFAULT 1,
    element_app_version nvarchar(32) NULL,
    element_iteration int NOT NULL DEFAULT 1,
    element_created_on datetimeoffset(7) NOT NULL DEFAULT SYSUTCDATETIME(),
    element_modified_on datetimeoffset(7) NOT NULL DEFAULT SYSUTCDATETIME(),
    CONSTRAINT PK_reflection_rpc_functions PRIMARY KEY CLUSTERED (recid),
    CONSTRAINT FK_reflection_rpc_functions_subdomains FOREIGN KEY (subdomains_recid) REFERENCES reflection_rpc_subdomains(recid),
    CONSTRAINT FK_reflection_rpc_functions_req_model FOREIGN KEY (element_request_model_recid) REFERENCES reflection_rpc_models(recid),
    CONSTRAINT FK_reflection_rpc_functions_resp_model FOREIGN KEY (element_response_model_recid) REFERENCES reflection_rpc_models(recid),
    CONSTRAINT UQ_reflection_rpc_functions_op UNIQUE (subdomains_recid, element_name, element_version)
  );
END;
GO
INSERT INTO system_schema_tables (element_schema, element_name)
SELECT 'dbo', 'reflection_rpc_domains'
WHERE NOT EXISTS (SELECT 1 FROM system_schema_tables WHERE element_schema='dbo' AND element_name='reflection_rpc_domains');
GO
INSERT INTO system_schema_tables (element_schema, element_name)
SELECT 'dbo', 'reflection_rpc_subdomains'
WHERE NOT EXISTS (SELECT 1 FROM system_schema_tables WHERE element_schema='dbo' AND element_name='reflection_rpc_subdomains');
GO
INSERT INTO system_schema_tables (element_schema, element_name)
SELECT 'dbo', 'reflection_rpc_models'
WHERE NOT EXISTS (SELECT 1 FROM system_schema_tables WHERE element_schema='dbo' AND element_name='reflection_rpc_models');
GO
INSERT INTO system_schema_tables (element_schema, element_name)
SELECT 'dbo', 'reflection_rpc_model_fields'
WHERE NOT EXISTS (SELECT 1 FROM system_schema_tables WHERE element_schema='dbo' AND element_name='reflection_rpc_model_fields');
GO
INSERT INTO system_schema_tables (element_schema, element_name)
SELECT 'dbo', 'reflection_rpc_functions'
WHERE NOT EXISTS (SELECT 1 FROM system_schema_tables WHERE element_schema='dbo' AND element_name='reflection_rpc_functions');
GO
DECLARE @t_reflection_rpc_domains BIGINT = (SELECT recid FROM system_schema_tables WHERE element_schema='dbo' AND element_name='reflection_rpc_domains');
INSERT INTO system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_reflection_rpc_domains, 3, 'recid', 1, 0, NULL, NULL, 1, 1
WHERE NOT EXISTS (SELECT 1 FROM system_schema_columns WHERE tables_recid=@t_reflection_rpc_domains AND element_name='recid');
INSERT INTO system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_reflection_rpc_domains, 8, 'element_name', 2, 0, NULL, 64, 0, 0
WHERE NOT EXISTS (SELECT 1 FROM system_schema_columns WHERE tables_recid=@t_reflection_rpc_domains AND element_name='element_name');
INSERT INTO system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_reflection_rpc_domains, 8, 'element_required_role', 3, 1, NULL, 128, 0, 0
WHERE NOT EXISTS (SELECT 1 FROM system_schema_columns WHERE tables_recid=@t_reflection_rpc_domains AND element_name='element_required_role');
INSERT INTO system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_reflection_rpc_domains, 5, 'element_is_auth_exempt', 4, 0, '((0))', NULL, 0, 0
WHERE NOT EXISTS (SELECT 1 FROM system_schema_columns WHERE tables_recid=@t_reflection_rpc_domains AND element_name='element_is_auth_exempt');
INSERT INTO system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_reflection_rpc_domains, 5, 'element_is_public', 5, 0, '((0))', NULL, 0, 0
WHERE NOT EXISTS (SELECT 1 FROM system_schema_columns WHERE tables_recid=@t_reflection_rpc_domains AND element_name='element_is_public');
INSERT INTO system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_reflection_rpc_domains, 5, 'element_is_discord', 6, 0, '((0))', NULL, 0, 0
WHERE NOT EXISTS (SELECT 1 FROM system_schema_columns WHERE tables_recid=@t_reflection_rpc_domains AND element_name='element_is_discord');
INSERT INTO system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_reflection_rpc_domains, 1, 'element_status', 7, 0, '((1))', NULL, 0, 0
WHERE NOT EXISTS (SELECT 1 FROM system_schema_columns WHERE tables_recid=@t_reflection_rpc_domains AND element_name='element_status');
INSERT INTO system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_reflection_rpc_domains, 8, 'element_app_version', 8, 1, NULL, 32, 0, 0
WHERE NOT EXISTS (SELECT 1 FROM system_schema_columns WHERE tables_recid=@t_reflection_rpc_domains AND element_name='element_app_version');
INSERT INTO system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_reflection_rpc_domains, 1, 'element_iteration', 9, 0, '((1))', NULL, 0, 0
WHERE NOT EXISTS (SELECT 1 FROM system_schema_columns WHERE tables_recid=@t_reflection_rpc_domains AND element_name='element_iteration');
INSERT INTO system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_reflection_rpc_domains, 7, 'element_created_on', 10, 0, '(sysutcdatetime())', NULL, 0, 0
WHERE NOT EXISTS (SELECT 1 FROM system_schema_columns WHERE tables_recid=@t_reflection_rpc_domains AND element_name='element_created_on');
INSERT INTO system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_reflection_rpc_domains, 7, 'element_modified_on', 11, 0, '(sysutcdatetime())', NULL, 0, 0
WHERE NOT EXISTS (SELECT 1 FROM system_schema_columns WHERE tables_recid=@t_reflection_rpc_domains AND element_name='element_modified_on');
GO
DECLARE @t_reflection_rpc_subdomains BIGINT = (SELECT recid FROM system_schema_tables WHERE element_schema='dbo' AND element_name='reflection_rpc_subdomains');
INSERT INTO system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_reflection_rpc_subdomains, 3, 'recid', 1, 0, NULL, NULL, 1, 1
WHERE NOT EXISTS (SELECT 1 FROM system_schema_columns WHERE tables_recid=@t_reflection_rpc_subdomains AND element_name='recid');
INSERT INTO system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_reflection_rpc_subdomains, 2, 'domains_recid', 2, 0, NULL, NULL, 0, 0
WHERE NOT EXISTS (SELECT 1 FROM system_schema_columns WHERE tables_recid=@t_reflection_rpc_subdomains AND element_name='domains_recid');
INSERT INTO system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_reflection_rpc_subdomains, 8, 'element_name', 3, 0, NULL, 64, 0, 0
WHERE NOT EXISTS (SELECT 1 FROM system_schema_columns WHERE tables_recid=@t_reflection_rpc_subdomains AND element_name='element_name');
INSERT INTO system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_reflection_rpc_subdomains, 2, 'element_entitlement_mask', 4, 0, '((0))', NULL, 0, 0
WHERE NOT EXISTS (SELECT 1 FROM system_schema_columns WHERE tables_recid=@t_reflection_rpc_subdomains AND element_name='element_entitlement_mask');
INSERT INTO system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_reflection_rpc_subdomains, 1, 'element_status', 5, 0, '((1))', NULL, 0, 0
WHERE NOT EXISTS (SELECT 1 FROM system_schema_columns WHERE tables_recid=@t_reflection_rpc_subdomains AND element_name='element_status');
INSERT INTO system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_reflection_rpc_subdomains, 8, 'element_app_version', 6, 1, NULL, 32, 0, 0
WHERE NOT EXISTS (SELECT 1 FROM system_schema_columns WHERE tables_recid=@t_reflection_rpc_subdomains AND element_name='element_app_version');
INSERT INTO system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_reflection_rpc_subdomains, 1, 'element_iteration', 7, 0, '((1))', NULL, 0, 0
WHERE NOT EXISTS (SELECT 1 FROM system_schema_columns WHERE tables_recid=@t_reflection_rpc_subdomains AND element_name='element_iteration');
INSERT INTO system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_reflection_rpc_subdomains, 7, 'element_created_on', 8, 0, '(sysutcdatetime())', NULL, 0, 0
WHERE NOT EXISTS (SELECT 1 FROM system_schema_columns WHERE tables_recid=@t_reflection_rpc_subdomains AND element_name='element_created_on');
INSERT INTO system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_reflection_rpc_subdomains, 7, 'element_modified_on', 9, 0, '(sysutcdatetime())', NULL, 0, 0
WHERE NOT EXISTS (SELECT 1 FROM system_schema_columns WHERE tables_recid=@t_reflection_rpc_subdomains AND element_name='element_modified_on');
GO
DECLARE @t_reflection_rpc_models BIGINT = (SELECT recid FROM system_schema_tables WHERE element_schema='dbo' AND element_name='reflection_rpc_models');
INSERT INTO system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_reflection_rpc_models, 3, 'recid', 1, 0, NULL, NULL, 1, 1
WHERE NOT EXISTS (SELECT 1 FROM system_schema_columns WHERE tables_recid=@t_reflection_rpc_models AND element_name='recid');
INSERT INTO system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_reflection_rpc_models, 8, 'element_name', 2, 0, NULL, 128, 0, 0
WHERE NOT EXISTS (SELECT 1 FROM system_schema_columns WHERE tables_recid=@t_reflection_rpc_models AND element_name='element_name');
INSERT INTO system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_reflection_rpc_models, 8, 'element_domain', 3, 0, NULL, 64, 0, 0
WHERE NOT EXISTS (SELECT 1 FROM system_schema_columns WHERE tables_recid=@t_reflection_rpc_models AND element_name='element_domain');
INSERT INTO system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_reflection_rpc_models, 8, 'element_subdomain', 4, 0, NULL, 64, 0, 0
WHERE NOT EXISTS (SELECT 1 FROM system_schema_columns WHERE tables_recid=@t_reflection_rpc_models AND element_name='element_subdomain');
INSERT INTO system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_reflection_rpc_models, 1, 'element_version', 5, 0, '((1))', NULL, 0, 0
WHERE NOT EXISTS (SELECT 1 FROM system_schema_columns WHERE tables_recid=@t_reflection_rpc_models AND element_name='element_version');
INSERT INTO system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_reflection_rpc_models, 2, 'element_parent_recid', 6, 1, NULL, NULL, 0, 0
WHERE NOT EXISTS (SELECT 1 FROM system_schema_columns WHERE tables_recid=@t_reflection_rpc_models AND element_name='element_parent_recid');
INSERT INTO system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_reflection_rpc_models, 1, 'element_status', 7, 0, '((1))', NULL, 0, 0
WHERE NOT EXISTS (SELECT 1 FROM system_schema_columns WHERE tables_recid=@t_reflection_rpc_models AND element_name='element_status');
INSERT INTO system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_reflection_rpc_models, 8, 'element_app_version', 8, 1, NULL, 32, 0, 0
WHERE NOT EXISTS (SELECT 1 FROM system_schema_columns WHERE tables_recid=@t_reflection_rpc_models AND element_name='element_app_version');
INSERT INTO system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_reflection_rpc_models, 1, 'element_iteration', 9, 0, '((1))', NULL, 0, 0
WHERE NOT EXISTS (SELECT 1 FROM system_schema_columns WHERE tables_recid=@t_reflection_rpc_models AND element_name='element_iteration');
INSERT INTO system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_reflection_rpc_models, 7, 'element_created_on', 10, 0, '(sysutcdatetime())', NULL, 0, 0
WHERE NOT EXISTS (SELECT 1 FROM system_schema_columns WHERE tables_recid=@t_reflection_rpc_models AND element_name='element_created_on');
INSERT INTO system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_reflection_rpc_models, 7, 'element_modified_on', 11, 0, '(sysutcdatetime())', NULL, 0, 0
WHERE NOT EXISTS (SELECT 1 FROM system_schema_columns WHERE tables_recid=@t_reflection_rpc_models AND element_name='element_modified_on');
GO
DECLARE @t_reflection_rpc_model_fields BIGINT = (SELECT recid FROM system_schema_tables WHERE element_schema='dbo' AND element_name='reflection_rpc_model_fields');
INSERT INTO system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_reflection_rpc_model_fields, 3, 'recid', 1, 0, NULL, NULL, 1, 1
WHERE NOT EXISTS (SELECT 1 FROM system_schema_columns WHERE tables_recid=@t_reflection_rpc_model_fields AND element_name='recid');
INSERT INTO system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_reflection_rpc_model_fields, 2, 'models_recid', 2, 0, NULL, NULL, 0, 0
WHERE NOT EXISTS (SELECT 1 FROM system_schema_columns WHERE tables_recid=@t_reflection_rpc_model_fields AND element_name='models_recid');
INSERT INTO system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_reflection_rpc_model_fields, 8, 'element_name', 3, 0, NULL, 128, 0, 0
WHERE NOT EXISTS (SELECT 1 FROM system_schema_columns WHERE tables_recid=@t_reflection_rpc_model_fields AND element_name='element_name');
INSERT INTO system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_reflection_rpc_model_fields, 2, 'element_edt_recid', 4, 1, NULL, NULL, 0, 0
WHERE NOT EXISTS (SELECT 1 FROM system_schema_columns WHERE tables_recid=@t_reflection_rpc_model_fields AND element_name='element_edt_recid');
INSERT INTO system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_reflection_rpc_model_fields, 5, 'element_is_nullable', 5, 0, '((0))', NULL, 0, 0
WHERE NOT EXISTS (SELECT 1 FROM system_schema_columns WHERE tables_recid=@t_reflection_rpc_model_fields AND element_name='element_is_nullable');
INSERT INTO system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_reflection_rpc_model_fields, 5, 'element_is_list', 6, 0, '((0))', NULL, 0, 0
WHERE NOT EXISTS (SELECT 1 FROM system_schema_columns WHERE tables_recid=@t_reflection_rpc_model_fields AND element_name='element_is_list');
INSERT INTO system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_reflection_rpc_model_fields, 5, 'element_is_dict', 7, 0, '((0))', NULL, 0, 0
WHERE NOT EXISTS (SELECT 1 FROM system_schema_columns WHERE tables_recid=@t_reflection_rpc_model_fields AND element_name='element_is_dict');
INSERT INTO system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_reflection_rpc_model_fields, 2, 'element_ref_model_recid', 8, 1, NULL, NULL, 0, 0
WHERE NOT EXISTS (SELECT 1 FROM system_schema_columns WHERE tables_recid=@t_reflection_rpc_model_fields AND element_name='element_ref_model_recid');
INSERT INTO system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_reflection_rpc_model_fields, 8, 'element_default_value', 9, 1, NULL, 256, 0, 0
WHERE NOT EXISTS (SELECT 1 FROM system_schema_columns WHERE tables_recid=@t_reflection_rpc_model_fields AND element_name='element_default_value');
INSERT INTO system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_reflection_rpc_model_fields, 1, 'element_max_length', 10, 1, NULL, NULL, 0, 0
WHERE NOT EXISTS (SELECT 1 FROM system_schema_columns WHERE tables_recid=@t_reflection_rpc_model_fields AND element_name='element_max_length');
INSERT INTO system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_reflection_rpc_model_fields, 1, 'element_sort_order', 11, 0, '((0))', NULL, 0, 0
WHERE NOT EXISTS (SELECT 1 FROM system_schema_columns WHERE tables_recid=@t_reflection_rpc_model_fields AND element_name='element_sort_order');
INSERT INTO system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_reflection_rpc_model_fields, 1, 'element_status', 12, 0, '((1))', NULL, 0, 0
WHERE NOT EXISTS (SELECT 1 FROM system_schema_columns WHERE tables_recid=@t_reflection_rpc_model_fields AND element_name='element_status');
INSERT INTO system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_reflection_rpc_model_fields, 7, 'element_created_on', 13, 0, '(sysutcdatetime())', NULL, 0, 0
WHERE NOT EXISTS (SELECT 1 FROM system_schema_columns WHERE tables_recid=@t_reflection_rpc_model_fields AND element_name='element_created_on');
INSERT INTO system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_reflection_rpc_model_fields, 7, 'element_modified_on', 14, 0, '(sysutcdatetime())', NULL, 0, 0
WHERE NOT EXISTS (SELECT 1 FROM system_schema_columns WHERE tables_recid=@t_reflection_rpc_model_fields AND element_name='element_modified_on');
GO
DECLARE @t_reflection_rpc_functions BIGINT = (SELECT recid FROM system_schema_tables WHERE element_schema='dbo' AND element_name='reflection_rpc_functions');
INSERT INTO system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_reflection_rpc_functions, 3, 'recid', 1, 0, NULL, NULL, 1, 1
WHERE NOT EXISTS (SELECT 1 FROM system_schema_columns WHERE tables_recid=@t_reflection_rpc_functions AND element_name='recid');
INSERT INTO system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_reflection_rpc_functions, 2, 'subdomains_recid', 2, 0, NULL, NULL, 0, 0
WHERE NOT EXISTS (SELECT 1 FROM system_schema_columns WHERE tables_recid=@t_reflection_rpc_functions AND element_name='subdomains_recid');
INSERT INTO system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_reflection_rpc_functions, 8, 'element_name', 3, 0, NULL, 128, 0, 0
WHERE NOT EXISTS (SELECT 1 FROM system_schema_columns WHERE tables_recid=@t_reflection_rpc_functions AND element_name='element_name');
INSERT INTO system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_reflection_rpc_functions, 1, 'element_version', 4, 0, '((1))', NULL, 0, 0
WHERE NOT EXISTS (SELECT 1 FROM system_schema_columns WHERE tables_recid=@t_reflection_rpc_functions AND element_name='element_version');
INSERT INTO system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_reflection_rpc_functions, 8, 'element_module_attr', 5, 0, NULL, 128, 0, 0
WHERE NOT EXISTS (SELECT 1 FROM system_schema_columns WHERE tables_recid=@t_reflection_rpc_functions AND element_name='element_module_attr');
INSERT INTO system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_reflection_rpc_functions, 8, 'element_method_name', 6, 0, NULL, 128, 0, 0
WHERE NOT EXISTS (SELECT 1 FROM system_schema_columns WHERE tables_recid=@t_reflection_rpc_functions AND element_name='element_method_name');
INSERT INTO system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_reflection_rpc_functions, 2, 'element_request_model_recid', 7, 1, NULL, NULL, 0, 0
WHERE NOT EXISTS (SELECT 1 FROM system_schema_columns WHERE tables_recid=@t_reflection_rpc_functions AND element_name='element_request_model_recid');
INSERT INTO system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_reflection_rpc_functions, 2, 'element_response_model_recid', 8, 1, NULL, NULL, 0, 0
WHERE NOT EXISTS (SELECT 1 FROM system_schema_columns WHERE tables_recid=@t_reflection_rpc_functions AND element_name='element_response_model_recid');
INSERT INTO system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_reflection_rpc_functions, 1, 'element_status', 9, 0, '((1))', NULL, 0, 0
WHERE NOT EXISTS (SELECT 1 FROM system_schema_columns WHERE tables_recid=@t_reflection_rpc_functions AND element_name='element_status');
INSERT INTO system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_reflection_rpc_functions, 8, 'element_app_version', 10, 1, NULL, 32, 0, 0
WHERE NOT EXISTS (SELECT 1 FROM system_schema_columns WHERE tables_recid=@t_reflection_rpc_functions AND element_name='element_app_version');
INSERT INTO system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_reflection_rpc_functions, 1, 'element_iteration', 11, 0, '((1))', NULL, 0, 0
WHERE NOT EXISTS (SELECT 1 FROM system_schema_columns WHERE tables_recid=@t_reflection_rpc_functions AND element_name='element_iteration');
INSERT INTO system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_reflection_rpc_functions, 7, 'element_created_on', 12, 0, '(sysutcdatetime())', NULL, 0, 0
WHERE NOT EXISTS (SELECT 1 FROM system_schema_columns WHERE tables_recid=@t_reflection_rpc_functions AND element_name='element_created_on');
INSERT INTO system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_reflection_rpc_functions, 7, 'element_modified_on', 13, 0, '(sysutcdatetime())', NULL, 0, 0
WHERE NOT EXISTS (SELECT 1 FROM system_schema_columns WHERE tables_recid=@t_reflection_rpc_functions AND element_name='element_modified_on');
GO
INSERT INTO system_schema_indexes (tables_recid, element_name, element_columns, element_is_unique)
SELECT t.recid, 'UQ_reflection_rpc_domains_name', 'element_name', 1 FROM system_schema_tables t
WHERE t.element_schema='dbo' AND t.element_name='reflection_rpc_domains'
AND NOT EXISTS (SELECT 1 FROM system_schema_indexes i WHERE i.tables_recid=t.recid AND i.element_name='UQ_reflection_rpc_domains_name');
GO
INSERT INTO system_schema_indexes (tables_recid, element_name, element_columns, element_is_unique)
SELECT t.recid, 'UQ_reflection_rpc_subdomains_name', 'domains_recid,element_name', 1 FROM system_schema_tables t
WHERE t.element_schema='dbo' AND t.element_name='reflection_rpc_subdomains'
AND NOT EXISTS (SELECT 1 FROM system_schema_indexes i WHERE i.tables_recid=t.recid AND i.element_name='UQ_reflection_rpc_subdomains_name');
GO
INSERT INTO system_schema_indexes (tables_recid, element_name, element_columns, element_is_unique)
SELECT t.recid, 'UQ_reflection_rpc_models_name', 'element_name', 1 FROM system_schema_tables t
WHERE t.element_schema='dbo' AND t.element_name='reflection_rpc_models'
AND NOT EXISTS (SELECT 1 FROM system_schema_indexes i WHERE i.tables_recid=t.recid AND i.element_name='UQ_reflection_rpc_models_name');
GO
INSERT INTO system_schema_indexes (tables_recid, element_name, element_columns, element_is_unique)
SELECT t.recid, 'UQ_reflection_rpc_model_fields_name', 'models_recid,element_name', 1 FROM system_schema_tables t
WHERE t.element_schema='dbo' AND t.element_name='reflection_rpc_model_fields'
AND NOT EXISTS (SELECT 1 FROM system_schema_indexes i WHERE i.tables_recid=t.recid AND i.element_name='UQ_reflection_rpc_model_fields_name');
GO
INSERT INTO system_schema_indexes (tables_recid, element_name, element_columns, element_is_unique)
SELECT t.recid, 'UQ_reflection_rpc_functions_op', 'subdomains_recid,element_name,element_version', 1 FROM system_schema_tables t
WHERE t.element_schema='dbo' AND t.element_name='reflection_rpc_functions'
AND NOT EXISTS (SELECT 1 FROM system_schema_indexes i WHERE i.tables_recid=t.recid AND i.element_name='UQ_reflection_rpc_functions_op');
GO
INSERT INTO system_schema_foreign_keys (tables_recid, element_column_name, referenced_tables_recid, element_referenced_column)
SELECT s.recid, 'domains_recid', r.recid, 'recid'
FROM system_schema_tables s CROSS JOIN system_schema_tables r
WHERE s.element_schema='dbo' AND s.element_name='reflection_rpc_subdomains' AND r.element_schema='dbo' AND r.element_name='reflection_rpc_domains'
AND NOT EXISTS (SELECT 1 FROM system_schema_foreign_keys fk WHERE fk.tables_recid=s.recid AND fk.element_column_name='domains_recid');
GO
INSERT INTO system_schema_foreign_keys (tables_recid, element_column_name, referenced_tables_recid, element_referenced_column)
SELECT s.recid, 'element_parent_recid', r.recid, 'recid'
FROM system_schema_tables s CROSS JOIN system_schema_tables r
WHERE s.element_schema='dbo' AND s.element_name='reflection_rpc_models' AND r.element_schema='dbo' AND r.element_name='reflection_rpc_models'
AND NOT EXISTS (SELECT 1 FROM system_schema_foreign_keys fk WHERE fk.tables_recid=s.recid AND fk.element_column_name='element_parent_recid');
GO
INSERT INTO system_schema_foreign_keys (tables_recid, element_column_name, referenced_tables_recid, element_referenced_column)
SELECT s.recid, 'models_recid', r.recid, 'recid'
FROM system_schema_tables s CROSS JOIN system_schema_tables r
WHERE s.element_schema='dbo' AND s.element_name='reflection_rpc_model_fields' AND r.element_schema='dbo' AND r.element_name='reflection_rpc_models'
AND NOT EXISTS (SELECT 1 FROM system_schema_foreign_keys fk WHERE fk.tables_recid=s.recid AND fk.element_column_name='models_recid');
GO
INSERT INTO system_schema_foreign_keys (tables_recid, element_column_name, referenced_tables_recid, element_referenced_column)
SELECT s.recid, 'element_edt_recid', r.recid, 'recid'
FROM system_schema_tables s CROSS JOIN system_schema_tables r
WHERE s.element_schema='dbo' AND s.element_name='reflection_rpc_model_fields' AND r.element_schema='dbo' AND r.element_name='system_edt_mappings'
AND NOT EXISTS (SELECT 1 FROM system_schema_foreign_keys fk WHERE fk.tables_recid=s.recid AND fk.element_column_name='element_edt_recid');
GO
INSERT INTO system_schema_foreign_keys (tables_recid, element_column_name, referenced_tables_recid, element_referenced_column)
SELECT s.recid, 'element_ref_model_recid', r.recid, 'recid'
FROM system_schema_tables s CROSS JOIN system_schema_tables r
WHERE s.element_schema='dbo' AND s.element_name='reflection_rpc_model_fields' AND r.element_schema='dbo' AND r.element_name='reflection_rpc_models'
AND NOT EXISTS (SELECT 1 FROM system_schema_foreign_keys fk WHERE fk.tables_recid=s.recid AND fk.element_column_name='element_ref_model_recid');
GO
INSERT INTO system_schema_foreign_keys (tables_recid, element_column_name, referenced_tables_recid, element_referenced_column)
SELECT s.recid, 'subdomains_recid', r.recid, 'recid'
FROM system_schema_tables s CROSS JOIN system_schema_tables r
WHERE s.element_schema='dbo' AND s.element_name='reflection_rpc_functions' AND r.element_schema='dbo' AND r.element_name='reflection_rpc_subdomains'
AND NOT EXISTS (SELECT 1 FROM system_schema_foreign_keys fk WHERE fk.tables_recid=s.recid AND fk.element_column_name='subdomains_recid');
GO
INSERT INTO system_schema_foreign_keys (tables_recid, element_column_name, referenced_tables_recid, element_referenced_column)
SELECT s.recid, 'element_request_model_recid', r.recid, 'recid'
FROM system_schema_tables s CROSS JOIN system_schema_tables r
WHERE s.element_schema='dbo' AND s.element_name='reflection_rpc_functions' AND r.element_schema='dbo' AND r.element_name='reflection_rpc_models'
AND NOT EXISTS (SELECT 1 FROM system_schema_foreign_keys fk WHERE fk.tables_recid=s.recid AND fk.element_column_name='element_request_model_recid');
GO
INSERT INTO system_schema_foreign_keys (tables_recid, element_column_name, referenced_tables_recid, element_referenced_column)
SELECT s.recid, 'element_response_model_recid', r.recid, 'recid'
FROM system_schema_tables s CROSS JOIN system_schema_tables r
WHERE s.element_schema='dbo' AND s.element_name='reflection_rpc_functions' AND r.element_schema='dbo' AND r.element_name='reflection_rpc_models'
AND NOT EXISTS (SELECT 1 FROM system_schema_foreign_keys fk WHERE fk.tables_recid=s.recid AND fk.element_column_name='element_response_model_recid');
GO
UPDATE system_config SET element_value = '0.10.3.0' WHERE element_key = 'SchemaVersion';
GO
