/*
  Stabilize reflection RPC relationships by introducing deterministic GUID keys.
*/

SET XACT_ABORT ON;
GO

TRUNCATE TABLE dbo.system_workflow_run_actions;
GO
TRUNCATE TABLE dbo.system_workflow_runs;
GO
TRUNCATE TABLE dbo.system_workflow_actions;
GO
TRUNCATE TABLE dbo.system_scheduled_task_history;
GO

IF EXISTS (SELECT 1 FROM sys.foreign_keys WHERE name = 'FK_system_workflow_actions_functions' AND parent_object_id = OBJECT_ID('dbo.system_workflow_actions'))
BEGIN
  ALTER TABLE dbo.system_workflow_actions DROP CONSTRAINT FK_system_workflow_actions_functions;
END;
GO
IF EXISTS (SELECT 1 FROM sys.foreign_keys WHERE name = 'FK_system_workflow_actions_rollback_functions' AND parent_object_id = OBJECT_ID('dbo.system_workflow_actions'))
BEGIN
  ALTER TABLE dbo.system_workflow_actions DROP CONSTRAINT FK_system_workflow_actions_rollback_functions;
END;
GO

IF EXISTS (SELECT 1 FROM sys.foreign_keys WHERE name = 'FK_reflection_rpc_functions_subdomains' AND parent_object_id = OBJECT_ID('dbo.reflection_rpc_functions'))
BEGIN
  ALTER TABLE dbo.reflection_rpc_functions DROP CONSTRAINT FK_reflection_rpc_functions_subdomains;
END;
GO
IF EXISTS (SELECT 1 FROM sys.foreign_keys WHERE name = 'FK_reflection_rpc_functions_req_model' AND parent_object_id = OBJECT_ID('dbo.reflection_rpc_functions'))
BEGIN
  ALTER TABLE dbo.reflection_rpc_functions DROP CONSTRAINT FK_reflection_rpc_functions_req_model;
END;
GO
IF EXISTS (SELECT 1 FROM sys.foreign_keys WHERE name = 'FK_reflection_rpc_functions_resp_model' AND parent_object_id = OBJECT_ID('dbo.reflection_rpc_functions'))
BEGIN
  ALTER TABLE dbo.reflection_rpc_functions DROP CONSTRAINT FK_reflection_rpc_functions_resp_model;
END;
GO
IF EXISTS (SELECT 1 FROM sys.foreign_keys WHERE name = 'FK_reflection_rpc_subdomains_domains' AND parent_object_id = OBJECT_ID('dbo.reflection_rpc_subdomains'))
BEGIN
  ALTER TABLE dbo.reflection_rpc_subdomains DROP CONSTRAINT FK_reflection_rpc_subdomains_domains;
END;
GO
IF EXISTS (SELECT 1 FROM sys.foreign_keys WHERE name = 'FK_reflection_rpc_model_fields_models' AND parent_object_id = OBJECT_ID('dbo.reflection_rpc_model_fields'))
BEGIN
  ALTER TABLE dbo.reflection_rpc_model_fields DROP CONSTRAINT FK_reflection_rpc_model_fields_models;
END;
GO
IF EXISTS (SELECT 1 FROM sys.foreign_keys WHERE name = 'FK_reflection_rpc_model_fields_ref' AND parent_object_id = OBJECT_ID('dbo.reflection_rpc_model_fields'))
BEGIN
  ALTER TABLE dbo.reflection_rpc_model_fields DROP CONSTRAINT FK_reflection_rpc_model_fields_ref;
END;
GO
IF EXISTS (SELECT 1 FROM sys.foreign_keys WHERE name = 'FK_reflection_rpc_models_parent' AND parent_object_id = OBJECT_ID('dbo.reflection_rpc_models'))
BEGIN
  ALTER TABLE dbo.reflection_rpc_models DROP CONSTRAINT FK_reflection_rpc_models_parent;
END;
GO

IF EXISTS (SELECT 1 FROM sys.key_constraints WHERE name = 'UQ_reflection_rpc_functions_op' AND parent_object_id = OBJECT_ID('dbo.reflection_rpc_functions'))
BEGIN
  ALTER TABLE dbo.reflection_rpc_functions DROP CONSTRAINT UQ_reflection_rpc_functions_op;
END;
GO
IF EXISTS (SELECT 1 FROM sys.key_constraints WHERE name = 'UQ_reflection_rpc_model_fields_name' AND parent_object_id = OBJECT_ID('dbo.reflection_rpc_model_fields'))
BEGIN
  ALTER TABLE dbo.reflection_rpc_model_fields DROP CONSTRAINT UQ_reflection_rpc_model_fields_name;
END;
GO

ALTER TABLE dbo.reflection_rpc_domains ADD element_guid UNIQUEIDENTIFIER NOT NULL CONSTRAINT DF_reflection_rpc_domains_element_guid DEFAULT NEWID();
GO
ALTER TABLE dbo.reflection_rpc_subdomains ADD element_guid UNIQUEIDENTIFIER NOT NULL CONSTRAINT DF_reflection_rpc_subdomains_element_guid DEFAULT NEWID();
GO
ALTER TABLE dbo.reflection_rpc_functions ADD element_guid UNIQUEIDENTIFIER NOT NULL CONSTRAINT DF_reflection_rpc_functions_element_guid DEFAULT NEWID();
GO
ALTER TABLE dbo.reflection_rpc_models ADD element_guid UNIQUEIDENTIFIER NOT NULL CONSTRAINT DF_reflection_rpc_models_element_guid DEFAULT NEWID();
GO
ALTER TABLE dbo.reflection_rpc_model_fields ADD element_guid UNIQUEIDENTIFIER NOT NULL CONSTRAINT DF_reflection_rpc_model_fields_element_guid DEFAULT NEWID();
GO

EXEC sp_rename 'dbo.reflection_rpc_subdomains.domains_recid', 'domains_guid', 'COLUMN';
GO
ALTER TABLE dbo.reflection_rpc_subdomains ALTER COLUMN domains_guid UNIQUEIDENTIFIER NOT NULL;
GO

EXEC sp_rename 'dbo.reflection_rpc_functions.subdomains_recid', 'subdomains_guid', 'COLUMN';
GO
ALTER TABLE dbo.reflection_rpc_functions ALTER COLUMN subdomains_guid UNIQUEIDENTIFIER NOT NULL;
GO
EXEC sp_rename 'dbo.reflection_rpc_functions.element_request_model_recid', 'element_request_model_guid', 'COLUMN';
GO
ALTER TABLE dbo.reflection_rpc_functions ALTER COLUMN element_request_model_guid UNIQUEIDENTIFIER NULL;
GO
EXEC sp_rename 'dbo.reflection_rpc_functions.element_response_model_recid', 'element_response_model_guid', 'COLUMN';
GO
ALTER TABLE dbo.reflection_rpc_functions ALTER COLUMN element_response_model_guid UNIQUEIDENTIFIER NULL;
GO

EXEC sp_rename 'dbo.reflection_rpc_models.element_parent_recid', 'element_parent_guid', 'COLUMN';
GO
ALTER TABLE dbo.reflection_rpc_models ALTER COLUMN element_parent_guid UNIQUEIDENTIFIER NULL;
GO

EXEC sp_rename 'dbo.reflection_rpc_model_fields.models_recid', 'models_guid', 'COLUMN';
GO
ALTER TABLE dbo.reflection_rpc_model_fields ALTER COLUMN models_guid UNIQUEIDENTIFIER NOT NULL;
GO
EXEC sp_rename 'dbo.reflection_rpc_model_fields.element_ref_model_recid', 'element_ref_model_guid', 'COLUMN';
GO
ALTER TABLE dbo.reflection_rpc_model_fields ALTER COLUMN element_ref_model_guid UNIQUEIDENTIFIER NULL;
GO

EXEC sp_rename 'dbo.system_workflow_actions.functions_recid', 'functions_guid', 'COLUMN';
GO
ALTER TABLE dbo.system_workflow_actions ALTER COLUMN functions_guid UNIQUEIDENTIFIER NOT NULL;
GO
EXEC sp_rename 'dbo.system_workflow_actions.element_rollback_functions_recid', 'element_rollback_functions_guid', 'COLUMN';
GO
ALTER TABLE dbo.system_workflow_actions ALTER COLUMN element_rollback_functions_guid UNIQUEIDENTIFIER NULL;
GO

ALTER TABLE dbo.reflection_rpc_domains ADD CONSTRAINT UQ_reflection_rpc_domains_guid UNIQUE (element_guid);
GO
ALTER TABLE dbo.reflection_rpc_subdomains ADD CONSTRAINT UQ_reflection_rpc_subdomains_guid UNIQUE (element_guid);
GO
ALTER TABLE dbo.reflection_rpc_functions ADD CONSTRAINT UQ_reflection_rpc_functions_guid UNIQUE (element_guid);
GO
ALTER TABLE dbo.reflection_rpc_models ADD CONSTRAINT UQ_reflection_rpc_models_guid UNIQUE (element_guid);
GO
ALTER TABLE dbo.reflection_rpc_model_fields ADD CONSTRAINT UQ_reflection_rpc_model_fields_guid UNIQUE (element_guid);
GO

ALTER TABLE dbo.reflection_rpc_functions ADD CONSTRAINT UQ_reflection_rpc_functions_op UNIQUE (subdomains_guid, element_name, element_version);
GO
ALTER TABLE dbo.reflection_rpc_model_fields ADD CONSTRAINT UQ_reflection_rpc_model_fields_name UNIQUE (models_guid, element_name);
GO

ALTER TABLE dbo.reflection_rpc_subdomains ADD CONSTRAINT FK_reflection_rpc_subdomains_domains FOREIGN KEY (domains_guid) REFERENCES dbo.reflection_rpc_domains(element_guid);
GO
ALTER TABLE dbo.reflection_rpc_functions ADD CONSTRAINT FK_reflection_rpc_functions_subdomains FOREIGN KEY (subdomains_guid) REFERENCES dbo.reflection_rpc_subdomains(element_guid);
GO
ALTER TABLE dbo.reflection_rpc_functions ADD CONSTRAINT FK_reflection_rpc_functions_req_model FOREIGN KEY (element_request_model_guid) REFERENCES dbo.reflection_rpc_models(element_guid);
GO
ALTER TABLE dbo.reflection_rpc_functions ADD CONSTRAINT FK_reflection_rpc_functions_resp_model FOREIGN KEY (element_response_model_guid) REFERENCES dbo.reflection_rpc_models(element_guid);
GO
ALTER TABLE dbo.reflection_rpc_models ADD CONSTRAINT FK_reflection_rpc_models_parent FOREIGN KEY (element_parent_guid) REFERENCES dbo.reflection_rpc_models(element_guid);
GO
ALTER TABLE dbo.reflection_rpc_model_fields ADD CONSTRAINT FK_reflection_rpc_model_fields_models FOREIGN KEY (models_guid) REFERENCES dbo.reflection_rpc_models(element_guid);
GO
ALTER TABLE dbo.reflection_rpc_model_fields ADD CONSTRAINT FK_reflection_rpc_model_fields_ref FOREIGN KEY (element_ref_model_guid) REFERENCES dbo.reflection_rpc_models(element_guid);
GO
ALTER TABLE dbo.system_workflow_actions ADD CONSTRAINT FK_system_workflow_actions_functions FOREIGN KEY (functions_guid) REFERENCES dbo.reflection_rpc_functions(element_guid);
GO
ALTER TABLE dbo.system_workflow_actions ADD CONSTRAINT FK_system_workflow_actions_rollback_functions FOREIGN KEY (element_rollback_functions_guid) REFERENCES dbo.reflection_rpc_functions(element_guid);
GO

DECLARE @t_domains BIGINT = (SELECT recid FROM dbo.system_schema_tables WHERE element_schema = 'dbo' AND element_name = 'reflection_rpc_domains');
DECLARE @t_subdomains BIGINT = (SELECT recid FROM dbo.system_schema_tables WHERE element_schema = 'dbo' AND element_name = 'reflection_rpc_subdomains');
DECLARE @t_functions BIGINT = (SELECT recid FROM dbo.system_schema_tables WHERE element_schema = 'dbo' AND element_name = 'reflection_rpc_functions');
DECLARE @t_models BIGINT = (SELECT recid FROM dbo.system_schema_tables WHERE element_schema = 'dbo' AND element_name = 'reflection_rpc_models');
DECLARE @t_fields BIGINT = (SELECT recid FROM dbo.system_schema_tables WHERE element_schema = 'dbo' AND element_name = 'reflection_rpc_model_fields');
DECLARE @t_actions BIGINT = (SELECT recid FROM dbo.system_schema_tables WHERE element_schema = 'dbo' AND element_name = 'system_workflow_actions');

DELETE FROM dbo.system_schema_columns
WHERE (tables_recid = @t_subdomains AND element_name = 'domains_recid')
   OR (tables_recid = @t_functions AND element_name IN ('subdomains_recid', 'element_request_model_recid', 'element_response_model_recid'))
   OR (tables_recid = @t_models AND element_name = 'element_parent_recid')
   OR (tables_recid = @t_fields AND element_name IN ('models_recid', 'element_ref_model_recid'))
   OR (tables_recid = @t_actions AND element_name IN ('functions_recid', 'element_rollback_functions_recid'));
GO

INSERT INTO dbo.system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_domains, 4, 'element_guid', 2, 0, '(newid())', NULL, 0, 0
WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_columns WHERE tables_recid = @t_domains AND element_name = 'element_guid');
INSERT INTO dbo.system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_subdomains, 4, 'element_guid', 2, 0, '(newid())', NULL, 0, 0
WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_columns WHERE tables_recid = @t_subdomains AND element_name = 'element_guid');
INSERT INTO dbo.system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_subdomains, 4, 'domains_guid', 3, 0, NULL, NULL, 0, 0
WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_columns WHERE tables_recid = @t_subdomains AND element_name = 'domains_guid');
INSERT INTO dbo.system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_functions, 4, 'element_guid', 2, 0, '(newid())', NULL, 0, 0
WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_columns WHERE tables_recid = @t_functions AND element_name = 'element_guid');
INSERT INTO dbo.system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_functions, 4, 'subdomains_guid', 3, 0, NULL, NULL, 0, 0
WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_columns WHERE tables_recid = @t_functions AND element_name = 'subdomains_guid');
INSERT INTO dbo.system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_functions, 4, 'element_request_model_guid', 8, 1, NULL, NULL, 0, 0
WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_columns WHERE tables_recid = @t_functions AND element_name = 'element_request_model_guid');
INSERT INTO dbo.system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_functions, 4, 'element_response_model_guid', 9, 1, NULL, NULL, 0, 0
WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_columns WHERE tables_recid = @t_functions AND element_name = 'element_response_model_guid');
INSERT INTO dbo.system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_models, 4, 'element_guid', 2, 0, '(newid())', NULL, 0, 0
WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_columns WHERE tables_recid = @t_models AND element_name = 'element_guid');
INSERT INTO dbo.system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_models, 4, 'element_parent_guid', 7, 1, NULL, NULL, 0, 0
WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_columns WHERE tables_recid = @t_models AND element_name = 'element_parent_guid');
INSERT INTO dbo.system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_fields, 4, 'element_guid', 2, 0, '(newid())', NULL, 0, 0
WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_columns WHERE tables_recid = @t_fields AND element_name = 'element_guid');
INSERT INTO dbo.system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_fields, 4, 'models_guid', 3, 0, NULL, NULL, 0, 0
WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_columns WHERE tables_recid = @t_fields AND element_name = 'models_guid');
INSERT INTO dbo.system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_fields, 4, 'element_ref_model_guid', 9, 1, NULL, NULL, 0, 0
WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_columns WHERE tables_recid = @t_fields AND element_name = 'element_ref_model_guid');
INSERT INTO dbo.system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_actions, 4, 'functions_guid', 5, 0, NULL, NULL, 0, 0
WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_columns WHERE tables_recid = @t_actions AND element_name = 'functions_guid');
INSERT INTO dbo.system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_actions, 4, 'element_rollback_functions_guid', 11, 1, NULL, NULL, 0, 0
WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_columns WHERE tables_recid = @t_actions AND element_name = 'element_rollback_functions_guid');
GO

DECLARE @t_domains BIGINT = (SELECT recid FROM dbo.system_schema_tables WHERE element_schema = 'dbo' AND element_name = 'reflection_rpc_domains');
DECLARE @t_subdomains BIGINT = (SELECT recid FROM dbo.system_schema_tables WHERE element_schema = 'dbo' AND element_name = 'reflection_rpc_subdomains');
DECLARE @t_functions BIGINT = (SELECT recid FROM dbo.system_schema_tables WHERE element_schema = 'dbo' AND element_name = 'reflection_rpc_functions');
DECLARE @t_models BIGINT = (SELECT recid FROM dbo.system_schema_tables WHERE element_schema = 'dbo' AND element_name = 'reflection_rpc_models');
DECLARE @t_fields BIGINT = (SELECT recid FROM dbo.system_schema_tables WHERE element_schema = 'dbo' AND element_name = 'reflection_rpc_model_fields');

DELETE FROM dbo.system_schema_indexes
WHERE (tables_recid = @t_domains AND element_name = 'UQ_reflection_rpc_domains_guid')
   OR (tables_recid = @t_subdomains AND element_name = 'UQ_reflection_rpc_subdomains_guid')
   OR (tables_recid = @t_functions AND element_name IN ('UQ_reflection_rpc_functions_guid', 'UQ_reflection_rpc_functions_op'))
   OR (tables_recid = @t_models AND element_name = 'UQ_reflection_rpc_models_guid')
   OR (tables_recid = @t_fields AND element_name IN ('UQ_reflection_rpc_model_fields_guid', 'UQ_reflection_rpc_model_fields_name'));

INSERT INTO dbo.system_schema_indexes (tables_recid, element_name, element_columns, element_is_unique)
SELECT @t_domains, 'UQ_reflection_rpc_domains_guid', 'element_guid', 1;
INSERT INTO dbo.system_schema_indexes (tables_recid, element_name, element_columns, element_is_unique)
SELECT @t_subdomains, 'UQ_reflection_rpc_subdomains_guid', 'element_guid', 1;
INSERT INTO dbo.system_schema_indexes (tables_recid, element_name, element_columns, element_is_unique)
SELECT @t_functions, 'UQ_reflection_rpc_functions_guid', 'element_guid', 1;
INSERT INTO dbo.system_schema_indexes (tables_recid, element_name, element_columns, element_is_unique)
SELECT @t_models, 'UQ_reflection_rpc_models_guid', 'element_guid', 1;
INSERT INTO dbo.system_schema_indexes (tables_recid, element_name, element_columns, element_is_unique)
SELECT @t_fields, 'UQ_reflection_rpc_model_fields_guid', 'element_guid', 1;
INSERT INTO dbo.system_schema_indexes (tables_recid, element_name, element_columns, element_is_unique)
SELECT @t_functions, 'UQ_reflection_rpc_functions_op', 'subdomains_guid,element_name,element_version', 1;
INSERT INTO dbo.system_schema_indexes (tables_recid, element_name, element_columns, element_is_unique)
SELECT @t_fields, 'UQ_reflection_rpc_model_fields_name', 'models_guid,element_name', 1;
GO

DECLARE @t_subdomains BIGINT = (SELECT recid FROM dbo.system_schema_tables WHERE element_schema = 'dbo' AND element_name = 'reflection_rpc_subdomains');
DECLARE @t_functions BIGINT = (SELECT recid FROM dbo.system_schema_tables WHERE element_schema = 'dbo' AND element_name = 'reflection_rpc_functions');
DECLARE @t_models BIGINT = (SELECT recid FROM dbo.system_schema_tables WHERE element_schema = 'dbo' AND element_name = 'reflection_rpc_models');
DECLARE @t_fields BIGINT = (SELECT recid FROM dbo.system_schema_tables WHERE element_schema = 'dbo' AND element_name = 'reflection_rpc_model_fields');
DECLARE @t_actions BIGINT = (SELECT recid FROM dbo.system_schema_tables WHERE element_schema = 'dbo' AND element_name = 'system_workflow_actions');

DELETE FROM dbo.system_schema_foreign_keys
WHERE (tables_recid = @t_subdomains AND element_column_name IN ('domains_recid', 'domains_guid'))
   OR (tables_recid = @t_functions AND element_column_name IN ('subdomains_recid', 'subdomains_guid', 'element_request_model_recid', 'element_request_model_guid', 'element_response_model_recid', 'element_response_model_guid'))
   OR (tables_recid = @t_models AND element_column_name IN ('element_parent_recid', 'element_parent_guid'))
   OR (tables_recid = @t_fields AND element_column_name IN ('models_recid', 'models_guid', 'element_ref_model_recid', 'element_ref_model_guid'))
   OR (tables_recid = @t_actions AND element_column_name IN ('functions_recid', 'functions_guid', 'element_rollback_functions_recid', 'element_rollback_functions_guid'));
GO

DECLARE @t_domains BIGINT = (SELECT recid FROM dbo.system_schema_tables WHERE element_schema = 'dbo' AND element_name = 'reflection_rpc_domains');
DECLARE @t_subdomains BIGINT = (SELECT recid FROM dbo.system_schema_tables WHERE element_schema = 'dbo' AND element_name = 'reflection_rpc_subdomains');
DECLARE @t_functions BIGINT = (SELECT recid FROM dbo.system_schema_tables WHERE element_schema = 'dbo' AND element_name = 'reflection_rpc_functions');
DECLARE @t_models BIGINT = (SELECT recid FROM dbo.system_schema_tables WHERE element_schema = 'dbo' AND element_name = 'reflection_rpc_models');
DECLARE @t_fields BIGINT = (SELECT recid FROM dbo.system_schema_tables WHERE element_schema = 'dbo' AND element_name = 'reflection_rpc_model_fields');
DECLARE @t_actions BIGINT = (SELECT recid FROM dbo.system_schema_tables WHERE element_schema = 'dbo' AND element_name = 'system_workflow_actions');

INSERT INTO dbo.system_schema_foreign_keys (tables_recid, element_column_name, referenced_tables_recid, element_referenced_column)
SELECT @t_subdomains, 'domains_guid', @t_domains, 'element_guid';
INSERT INTO dbo.system_schema_foreign_keys (tables_recid, element_column_name, referenced_tables_recid, element_referenced_column)
SELECT @t_functions, 'subdomains_guid', @t_subdomains, 'element_guid';
INSERT INTO dbo.system_schema_foreign_keys (tables_recid, element_column_name, referenced_tables_recid, element_referenced_column)
SELECT @t_functions, 'element_request_model_guid', @t_models, 'element_guid';
INSERT INTO dbo.system_schema_foreign_keys (tables_recid, element_column_name, referenced_tables_recid, element_referenced_column)
SELECT @t_functions, 'element_response_model_guid', @t_models, 'element_guid';
INSERT INTO dbo.system_schema_foreign_keys (tables_recid, element_column_name, referenced_tables_recid, element_referenced_column)
SELECT @t_models, 'element_parent_guid', @t_models, 'element_guid';
INSERT INTO dbo.system_schema_foreign_keys (tables_recid, element_column_name, referenced_tables_recid, element_referenced_column)
SELECT @t_fields, 'models_guid', @t_models, 'element_guid';
INSERT INTO dbo.system_schema_foreign_keys (tables_recid, element_column_name, referenced_tables_recid, element_referenced_column)
SELECT @t_fields, 'element_ref_model_guid', @t_models, 'element_guid';
INSERT INTO dbo.system_schema_foreign_keys (tables_recid, element_column_name, referenced_tables_recid, element_referenced_column)
SELECT @t_actions, 'functions_guid', @t_functions, 'element_guid';
INSERT INTO dbo.system_schema_foreign_keys (tables_recid, element_column_name, referenced_tables_recid, element_referenced_column)
SELECT @t_actions, 'element_rollback_functions_guid', @t_functions, 'element_guid';
GO
