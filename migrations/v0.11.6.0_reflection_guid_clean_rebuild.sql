/*
  Reflection table GUID stabilization clean rebuild.
  Drops and recreates reflection_rpc_* tables and restores workflow foreign keys.
*/

SET XACT_ABORT ON;
GO

BEGIN TRANSACTION;
GO

-- Phase 1: clear dependent automation data.
DELETE FROM dbo.system_workflow_run_actions;
DELETE FROM dbo.system_workflow_runs;
DELETE FROM dbo.system_scheduled_task_history;
DELETE FROM dbo.system_workflow_actions;
GO

-- Phase 2: drop workflow foreign keys to reflection tables.
IF EXISTS (SELECT 1 FROM sys.foreign_keys WHERE name = 'FK_system_workflow_actions_functions')
BEGIN
  ALTER TABLE dbo.system_workflow_actions DROP CONSTRAINT FK_system_workflow_actions_functions;
END;
GO

IF EXISTS (SELECT 1 FROM sys.foreign_keys WHERE name = 'FK_system_workflow_actions_rollback_functions')
BEGIN
  ALTER TABLE dbo.system_workflow_actions DROP CONSTRAINT FK_system_workflow_actions_rollback_functions;
END;
GO

IF EXISTS (SELECT 1 FROM sys.foreign_keys WHERE name = 'FK_system_workflow_actions_functions_recid')
BEGIN
  ALTER TABLE dbo.system_workflow_actions DROP CONSTRAINT FK_system_workflow_actions_functions_recid;
END;
GO

IF EXISTS (SELECT 1 FROM sys.foreign_keys WHERE name = 'FK_system_workflow_actions_rollback')
BEGIN
  ALTER TABLE dbo.system_workflow_actions DROP CONSTRAINT FK_system_workflow_actions_rollback;
END;
GO

-- Phase 3: normalize workflow FK columns to GUID types.
IF EXISTS (SELECT 1 FROM sys.columns WHERE object_id = OBJECT_ID('dbo.system_workflow_actions') AND name = 'functions_recid')
BEGIN
  ALTER TABLE dbo.system_workflow_actions DROP COLUMN functions_recid;
END;
GO

IF EXISTS (SELECT 1 FROM sys.columns WHERE object_id = OBJECT_ID('dbo.system_workflow_actions') AND name = 'element_rollback_functions_recid')
BEGIN
  ALTER TABLE dbo.system_workflow_actions DROP COLUMN element_rollback_functions_recid;
END;
GO

IF EXISTS (SELECT 1 FROM sys.columns WHERE object_id = OBJECT_ID('dbo.system_workflow_actions') AND name = 'functions_guid')
BEGIN
  ALTER TABLE dbo.system_workflow_actions DROP COLUMN functions_guid;
END;
GO

IF EXISTS (SELECT 1 FROM sys.columns WHERE object_id = OBJECT_ID('dbo.system_workflow_actions') AND name = 'element_rollback_functions_guid')
BEGIN
  ALTER TABLE dbo.system_workflow_actions DROP COLUMN element_rollback_functions_guid;
END;
GO

ALTER TABLE dbo.system_workflow_actions
ADD functions_guid UNIQUEIDENTIFIER NOT NULL CONSTRAINT DF_system_workflow_actions_functions_guid DEFAULT ('00000000-0000-0000-0000-000000000000');
GO

ALTER TABLE dbo.system_workflow_actions
ADD element_rollback_functions_guid UNIQUEIDENTIFIER NULL;
GO

-- Phase 4: drop existing reflection table constraints/indexes and tables.
DECLARE @sql NVARCHAR(MAX) = N'';
SELECT @sql = @sql + N'ALTER TABLE ' + QUOTENAME(OBJECT_SCHEMA_NAME(parent_object_id)) + N'.' + QUOTENAME(OBJECT_NAME(parent_object_id)) + N' DROP CONSTRAINT ' + QUOTENAME(name) + N'; '
FROM sys.foreign_keys
WHERE OBJECT_NAME(parent_object_id) LIKE 'reflection_rpc_%'
   OR OBJECT_NAME(referenced_object_id) LIKE 'reflection_rpc_%';
IF LEN(@sql) > 0
BEGIN
  EXEC sp_executesql @sql;
END;
GO

DECLARE @sql NVARCHAR(MAX) = N'';
SELECT @sql = @sql + N'ALTER TABLE ' + QUOTENAME(OBJECT_SCHEMA_NAME(parent_object_id)) + N'.' + QUOTENAME(OBJECT_NAME(parent_object_id)) + N' DROP CONSTRAINT ' + QUOTENAME(name) + N'; '
FROM sys.key_constraints
WHERE OBJECT_NAME(parent_object_id) LIKE 'reflection_rpc_%'
  AND type = 'UQ';
IF LEN(@sql) > 0
BEGIN
  EXEC sp_executesql @sql;
END;
GO

DECLARE @sql NVARCHAR(MAX) = N'';
SELECT @sql = @sql + N'DROP INDEX ' + QUOTENAME(i.name) + N' ON ' + QUOTENAME(OBJECT_SCHEMA_NAME(i.object_id)) + N'.' + QUOTENAME(OBJECT_NAME(i.object_id)) + N'; '
FROM sys.indexes AS i
WHERE OBJECT_NAME(i.object_id) LIKE 'reflection_rpc_%'
  AND i.is_primary_key = 0
  AND i.is_unique_constraint = 0
  AND i.name IS NOT NULL;
IF LEN(@sql) > 0
BEGIN
  EXEC sp_executesql @sql;
END;
GO

DROP TABLE IF EXISTS dbo.reflection_rpc_model_fields;
DROP TABLE IF EXISTS dbo.reflection_rpc_functions;
DROP TABLE IF EXISTS dbo.reflection_rpc_models;
DROP TABLE IF EXISTS dbo.reflection_rpc_subdomains;
DROP TABLE IF EXISTS dbo.reflection_rpc_domains;
GO

-- Phase 5: rebuild reflection tables with GUID relationships.
CREATE TABLE dbo.reflection_rpc_domains (
  recid BIGINT IDENTITY(1,1) NOT NULL,
  element_guid UNIQUEIDENTIFIER NOT NULL CONSTRAINT DF_reflection_rpc_domains_element_guid DEFAULT NEWID(),
  element_name NVARCHAR(64) NOT NULL,
  element_required_role NVARCHAR(128) NULL,
  element_is_auth_exempt BIT NOT NULL CONSTRAINT DF_reflection_rpc_domains_auth_exempt DEFAULT 0,
  element_is_public BIT NOT NULL CONSTRAINT DF_reflection_rpc_domains_public DEFAULT 0,
  element_is_discord BIT NOT NULL CONSTRAINT DF_reflection_rpc_domains_discord DEFAULT 0,
  element_status INT NOT NULL CONSTRAINT DF_reflection_rpc_domains_status DEFAULT 1,
  element_app_version NVARCHAR(32) NULL,
  element_iteration INT NOT NULL CONSTRAINT DF_reflection_rpc_domains_iteration DEFAULT 1,
  element_created_on DATETIMEOFFSET(7) NOT NULL CONSTRAINT DF_reflection_rpc_domains_created_on DEFAULT SYSUTCDATETIME(),
  element_modified_on DATETIMEOFFSET(7) NOT NULL CONSTRAINT DF_reflection_rpc_domains_modified_on DEFAULT SYSUTCDATETIME(),
  CONSTRAINT PK_reflection_rpc_domains PRIMARY KEY (recid),
  CONSTRAINT UQ_reflection_rpc_domains_guid UNIQUE (element_guid),
  CONSTRAINT UQ_reflection_rpc_domains_name UNIQUE (element_name)
);
GO

CREATE TABLE dbo.reflection_rpc_subdomains (
  recid BIGINT IDENTITY(1,1) NOT NULL,
  element_guid UNIQUEIDENTIFIER NOT NULL CONSTRAINT DF_reflection_rpc_subdomains_element_guid DEFAULT NEWID(),
  domains_guid UNIQUEIDENTIFIER NOT NULL,
  element_name NVARCHAR(64) NOT NULL,
  element_entitlement_mask BIGINT NOT NULL CONSTRAINT DF_reflection_rpc_subdomains_entitlement DEFAULT 0,
  element_status INT NOT NULL CONSTRAINT DF_reflection_rpc_subdomains_status DEFAULT 1,
  element_app_version NVARCHAR(32) NULL,
  element_iteration INT NOT NULL CONSTRAINT DF_reflection_rpc_subdomains_iteration DEFAULT 1,
  element_created_on DATETIMEOFFSET(7) NOT NULL CONSTRAINT DF_reflection_rpc_subdomains_created_on DEFAULT SYSUTCDATETIME(),
  element_modified_on DATETIMEOFFSET(7) NOT NULL CONSTRAINT DF_reflection_rpc_subdomains_modified_on DEFAULT SYSUTCDATETIME(),
  CONSTRAINT PK_reflection_rpc_subdomains PRIMARY KEY (recid),
  CONSTRAINT UQ_reflection_rpc_subdomains_guid UNIQUE (element_guid),
  CONSTRAINT UQ_reflection_rpc_subdomains_name UNIQUE (domains_guid, element_name),
  CONSTRAINT FK_reflection_rpc_subdomains_domains FOREIGN KEY (domains_guid) REFERENCES dbo.reflection_rpc_domains (element_guid)
);
GO

CREATE TABLE dbo.reflection_rpc_models (
  recid BIGINT IDENTITY(1,1) NOT NULL,
  element_guid UNIQUEIDENTIFIER NOT NULL CONSTRAINT DF_reflection_rpc_models_element_guid DEFAULT NEWID(),
  element_name NVARCHAR(128) NOT NULL,
  element_domain NVARCHAR(64) NOT NULL,
  element_subdomain NVARCHAR(64) NOT NULL,
  element_version INT NOT NULL CONSTRAINT DF_reflection_rpc_models_version DEFAULT 1,
  element_parent_guid UNIQUEIDENTIFIER NULL,
  element_status INT NOT NULL CONSTRAINT DF_reflection_rpc_models_status DEFAULT 1,
  element_app_version NVARCHAR(32) NULL,
  element_iteration INT NOT NULL CONSTRAINT DF_reflection_rpc_models_iteration DEFAULT 1,
  element_created_on DATETIMEOFFSET(7) NOT NULL CONSTRAINT DF_reflection_rpc_models_created_on DEFAULT SYSUTCDATETIME(),
  element_modified_on DATETIMEOFFSET(7) NOT NULL CONSTRAINT DF_reflection_rpc_models_modified_on DEFAULT SYSUTCDATETIME(),
  CONSTRAINT PK_reflection_rpc_models PRIMARY KEY (recid),
  CONSTRAINT UQ_reflection_rpc_models_guid UNIQUE (element_guid),
  CONSTRAINT UQ_reflection_rpc_models_name UNIQUE (element_name),
  CONSTRAINT FK_reflection_rpc_models_parent FOREIGN KEY (element_parent_guid) REFERENCES dbo.reflection_rpc_models (element_guid)
);
GO

CREATE TABLE dbo.reflection_rpc_functions (
  recid BIGINT IDENTITY(1,1) NOT NULL,
  element_guid UNIQUEIDENTIFIER NOT NULL CONSTRAINT DF_reflection_rpc_functions_element_guid DEFAULT NEWID(),
  subdomains_guid UNIQUEIDENTIFIER NOT NULL,
  element_name NVARCHAR(128) NOT NULL,
  element_version INT NOT NULL CONSTRAINT DF_reflection_rpc_functions_version DEFAULT 1,
  element_module_attr NVARCHAR(128) NOT NULL,
  element_method_name NVARCHAR(128) NOT NULL,
  element_request_model_guid UNIQUEIDENTIFIER NULL,
  element_response_model_guid UNIQUEIDENTIFIER NULL,
  element_status INT NOT NULL CONSTRAINT DF_reflection_rpc_functions_status DEFAULT 1,
  element_app_version NVARCHAR(32) NULL,
  element_iteration INT NOT NULL CONSTRAINT DF_reflection_rpc_functions_iteration DEFAULT 1,
  element_created_on DATETIMEOFFSET(7) NOT NULL CONSTRAINT DF_reflection_rpc_functions_created_on DEFAULT SYSUTCDATETIME(),
  element_modified_on DATETIMEOFFSET(7) NOT NULL CONSTRAINT DF_reflection_rpc_functions_modified_on DEFAULT SYSUTCDATETIME(),
  CONSTRAINT PK_reflection_rpc_functions PRIMARY KEY (recid),
  CONSTRAINT UQ_reflection_rpc_functions_guid UNIQUE (element_guid),
  CONSTRAINT UQ_reflection_rpc_functions_op UNIQUE (subdomains_guid, element_name, element_version),
  CONSTRAINT FK_reflection_rpc_functions_subdomains FOREIGN KEY (subdomains_guid) REFERENCES dbo.reflection_rpc_subdomains (element_guid),
  CONSTRAINT FK_reflection_rpc_functions_req_model FOREIGN KEY (element_request_model_guid) REFERENCES dbo.reflection_rpc_models (element_guid),
  CONSTRAINT FK_reflection_rpc_functions_resp_model FOREIGN KEY (element_response_model_guid) REFERENCES dbo.reflection_rpc_models (element_guid)
);
GO

CREATE TABLE dbo.reflection_rpc_model_fields (
  recid BIGINT IDENTITY(1,1) NOT NULL,
  element_guid UNIQUEIDENTIFIER NOT NULL CONSTRAINT DF_reflection_rpc_model_fields_element_guid DEFAULT NEWID(),
  models_guid UNIQUEIDENTIFIER NOT NULL,
  element_name NVARCHAR(128) NOT NULL,
  element_edt_recid BIGINT NULL,
  element_is_nullable BIT NOT NULL CONSTRAINT DF_reflection_rpc_model_fields_nullable DEFAULT 0,
  element_is_list BIT NOT NULL CONSTRAINT DF_reflection_rpc_model_fields_is_list DEFAULT 0,
  element_is_dict BIT NOT NULL CONSTRAINT DF_reflection_rpc_model_fields_is_dict DEFAULT 0,
  element_ref_model_guid UNIQUEIDENTIFIER NULL,
  element_default_value NVARCHAR(256) NULL,
  element_max_length INT NULL,
  element_sort_order INT NOT NULL CONSTRAINT DF_reflection_rpc_model_fields_sort_order DEFAULT 0,
  element_status INT NOT NULL CONSTRAINT DF_reflection_rpc_model_fields_status DEFAULT 1,
  element_created_on DATETIMEOFFSET(7) NOT NULL CONSTRAINT DF_reflection_rpc_model_fields_created_on DEFAULT SYSUTCDATETIME(),
  element_modified_on DATETIMEOFFSET(7) NOT NULL CONSTRAINT DF_reflection_rpc_model_fields_modified_on DEFAULT SYSUTCDATETIME(),
  CONSTRAINT PK_reflection_rpc_model_fields PRIMARY KEY (recid),
  CONSTRAINT UQ_reflection_rpc_model_fields_guid UNIQUE (element_guid),
  CONSTRAINT UQ_reflection_rpc_model_fields_name UNIQUE (models_guid, element_name),
  CONSTRAINT FK_reflection_rpc_model_fields_models FOREIGN KEY (models_guid) REFERENCES dbo.reflection_rpc_models (element_guid),
  CONSTRAINT FK_reflection_rpc_model_fields_ref FOREIGN KEY (element_ref_model_guid) REFERENCES dbo.reflection_rpc_models (element_guid),
  CONSTRAINT FK_reflection_rpc_model_fields_edt FOREIGN KEY (element_edt_recid) REFERENCES dbo.system_edt_mappings (recid)
);
GO

-- Phase 6: restore workflow foreign keys.
ALTER TABLE dbo.system_workflow_actions
ADD CONSTRAINT FK_system_workflow_actions_functions
FOREIGN KEY (functions_guid) REFERENCES dbo.reflection_rpc_functions (element_guid);
GO

ALTER TABLE dbo.system_workflow_actions
ADD CONSTRAINT FK_system_workflow_actions_rollback_functions
FOREIGN KEY (element_rollback_functions_guid) REFERENCES dbo.reflection_rpc_functions (element_guid);
GO

COMMIT TRANSACTION;
GO

PRINT 'Migration complete. Reflection tables rebuilt with GUID-based FK columns.';
PRINT 'system_workflow_actions.functions_guid and element_rollback_functions_guid are UNIQUEIDENTIFIER.';
PRINT 'Next steps:';
PRINT '  1. Run seed_rpcdispatch.py --force';
PRINT '  2. Re-seed system_workflow_actions with correct functions_guid references';
GO
