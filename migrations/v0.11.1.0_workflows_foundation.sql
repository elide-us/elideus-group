SET NOCOUNT ON;
GO

IF OBJECT_ID('dbo.system_workflows', 'U') IS NULL
BEGIN
  CREATE TABLE dbo.system_workflows (
    element_guid UNIQUEIDENTIFIER NOT NULL CONSTRAINT DF_system_workflows_guid DEFAULT NEWID(),
    element_name NVARCHAR(128) NOT NULL,
    element_description NVARCHAR(1024) NULL,
    element_version INT NOT NULL CONSTRAINT DF_system_workflows_version DEFAULT 1,
    element_status TINYINT NOT NULL CONSTRAINT DF_system_workflows_status DEFAULT 1,
    element_created_on DATETIMEOFFSET(7) NOT NULL CONSTRAINT DF_system_workflows_created_on DEFAULT SYSUTCDATETIME(),
    element_modified_on DATETIMEOFFSET(7) NOT NULL CONSTRAINT DF_system_workflows_modified_on DEFAULT SYSUTCDATETIME(),
    CONSTRAINT PK_system_workflows PRIMARY KEY CLUSTERED (element_guid),
    CONSTRAINT UQ_system_workflows_name_version UNIQUE (element_name, element_version)
  );
END;
GO

IF OBJECT_ID('dbo.system_workflow_steps', 'U') IS NULL
BEGIN
  CREATE TABLE dbo.system_workflow_steps (
    element_guid UNIQUEIDENTIFIER NOT NULL CONSTRAINT DF_system_workflow_steps_guid DEFAULT NEWID(),
    workflows_guid UNIQUEIDENTIFIER NOT NULL,
    element_name NVARCHAR(128) NOT NULL,
    element_description NVARCHAR(1024) NULL,
    element_step_type NVARCHAR(16) NOT NULL CONSTRAINT DF_system_workflow_steps_type DEFAULT 'pipe',
    element_disposition NVARCHAR(16) NOT NULL CONSTRAINT DF_system_workflow_steps_disposition DEFAULT 'harmless',
    element_class_path NVARCHAR(512) NOT NULL,
    element_sequence INT NOT NULL,
    element_is_optional BIT NOT NULL CONSTRAINT DF_system_workflow_steps_optional DEFAULT 0,
    element_timeout_seconds INT NULL,
    element_config NVARCHAR(MAX) NULL,
    element_created_on DATETIMEOFFSET(7) NOT NULL CONSTRAINT DF_system_workflow_steps_created_on DEFAULT SYSUTCDATETIME(),
    element_modified_on DATETIMEOFFSET(7) NOT NULL CONSTRAINT DF_system_workflow_steps_modified_on DEFAULT SYSUTCDATETIME(),
    CONSTRAINT PK_system_workflow_steps PRIMARY KEY CLUSTERED (element_guid),
    CONSTRAINT UQ_system_workflow_steps_workflow_sequence UNIQUE (workflows_guid, element_sequence),
    CONSTRAINT UQ_system_workflow_steps_workflow_name UNIQUE (workflows_guid, element_name),
    CONSTRAINT FK_system_workflow_steps_workflows FOREIGN KEY (workflows_guid) REFERENCES dbo.system_workflows (element_guid)
  );
END;
GO

IF OBJECT_ID('dbo.system_workflow_runs', 'U') IS NULL
BEGIN
  CREATE TABLE dbo.system_workflow_runs (
    recid BIGINT IDENTITY(1,1) NOT NULL,
    element_guid UNIQUEIDENTIFIER NOT NULL CONSTRAINT DF_system_workflow_runs_guid DEFAULT NEWID(),
    workflows_guid UNIQUEIDENTIFIER NOT NULL,
    element_status TINYINT NOT NULL CONSTRAINT DF_system_workflow_runs_status DEFAULT 0,
    element_payload NVARCHAR(MAX) NULL,
    element_context NVARCHAR(MAX) NULL,
    element_current_step NVARCHAR(128) NULL,
    element_step_index INT NOT NULL CONSTRAINT DF_system_workflow_runs_step_index DEFAULT 0,
    element_error NVARCHAR(MAX) NULL,
    element_source_type NVARCHAR(64) NULL,
    element_source_id NVARCHAR(256) NULL,
    element_created_by UNIQUEIDENTIFIER NULL,
    element_started_on DATETIMEOFFSET(7) NULL,
    element_ended_on DATETIMEOFFSET(7) NULL,
    element_timeout_at DATETIMEOFFSET(7) NULL,
    element_created_on DATETIMEOFFSET(7) NOT NULL CONSTRAINT DF_system_workflow_runs_created_on DEFAULT SYSUTCDATETIME(),
    element_modified_on DATETIMEOFFSET(7) NOT NULL CONSTRAINT DF_system_workflow_runs_modified_on DEFAULT SYSUTCDATETIME(),
    CONSTRAINT PK_system_workflow_runs PRIMARY KEY CLUSTERED (recid),
    CONSTRAINT UQ_system_workflow_runs_guid UNIQUE (element_guid),
    CONSTRAINT FK_system_workflow_runs_workflows FOREIGN KEY (workflows_guid) REFERENCES dbo.system_workflows (element_guid)
  );
END;
GO

IF OBJECT_ID('dbo.system_workflow_run_steps', 'U') IS NULL
BEGIN
  CREATE TABLE dbo.system_workflow_run_steps (
    recid BIGINT IDENTITY(1,1) NOT NULL,
    element_guid UNIQUEIDENTIFIER NOT NULL CONSTRAINT DF_system_workflow_run_steps_guid DEFAULT NEWID(),
    runs_recid BIGINT NOT NULL,
    steps_guid UNIQUEIDENTIFIER NOT NULL,
    element_status TINYINT NOT NULL CONSTRAINT DF_system_workflow_run_steps_status DEFAULT 0,
    element_disposition NVARCHAR(16) NOT NULL,
    element_input NVARCHAR(MAX) NULL,
    element_output NVARCHAR(MAX) NULL,
    element_error NVARCHAR(MAX) NULL,
    element_started_on DATETIMEOFFSET(7) NULL,
    element_ended_on DATETIMEOFFSET(7) NULL,
    element_created_on DATETIMEOFFSET(7) NOT NULL CONSTRAINT DF_system_workflow_run_steps_created_on DEFAULT SYSUTCDATETIME(),
    element_modified_on DATETIMEOFFSET(7) NOT NULL CONSTRAINT DF_system_workflow_run_steps_modified_on DEFAULT SYSUTCDATETIME(),
    CONSTRAINT PK_system_workflow_run_steps PRIMARY KEY CLUSTERED (recid),
    CONSTRAINT UQ_system_workflow_run_steps_guid UNIQUE (element_guid),
    CONSTRAINT FK_system_workflow_run_steps_runs FOREIGN KEY (runs_recid) REFERENCES dbo.system_workflow_runs (recid),
    CONSTRAINT FK_system_workflow_run_steps_steps FOREIGN KEY (steps_guid) REFERENCES dbo.system_workflow_steps (element_guid)
  );
END;
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE object_id = OBJECT_ID('dbo.system_workflow_runs') AND name = 'IX_system_workflow_runs_status')
BEGIN
  CREATE NONCLUSTERED INDEX IX_system_workflow_runs_status ON dbo.system_workflow_runs (element_status);
END;
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE object_id = OBJECT_ID('dbo.system_workflow_runs') AND name = 'IX_system_workflow_runs_workflow')
BEGIN
  CREATE NONCLUSTERED INDEX IX_system_workflow_runs_workflow ON dbo.system_workflow_runs (workflows_guid);
END;
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE object_id = OBJECT_ID('dbo.system_workflow_run_steps') AND name = 'IX_system_workflow_run_steps_run')
BEGIN
  CREATE NONCLUSTERED INDEX IX_system_workflow_run_steps_run ON dbo.system_workflow_run_steps (runs_recid, element_created_on);
END;
GO

INSERT INTO dbo.system_schema_tables (element_name, element_schema)
SELECT 'system_workflows', 'dbo'
WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_tables WHERE element_name = 'system_workflows' AND element_schema = 'dbo');
GO

DECLARE @t_system_workflows BIGINT = (SELECT recid FROM dbo.system_schema_tables WHERE element_name = 'system_workflows' AND element_schema = 'dbo');
INSERT INTO dbo.system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_system_workflows, 4, 'element_guid', 1, 0, '(newid())', NULL, 1, 0 WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_columns WHERE tables_recid = @t_system_workflows AND element_name = 'element_guid');
INSERT INTO dbo.system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_system_workflows, 8, 'element_name', 2, 0, NULL, 128, 0, 0 WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_columns WHERE tables_recid = @t_system_workflows AND element_name = 'element_name');
INSERT INTO dbo.system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_system_workflows, 8, 'element_description', 3, 1, NULL, 1024, 0, 0 WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_columns WHERE tables_recid = @t_system_workflows AND element_name = 'element_description');
INSERT INTO dbo.system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_system_workflows, 1, 'element_version', 4, 0, '((1))', NULL, 0, 0 WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_columns WHERE tables_recid = @t_system_workflows AND element_name = 'element_version');
INSERT INTO dbo.system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_system_workflows, 11, 'element_status', 5, 0, '((1))', NULL, 0, 0 WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_columns WHERE tables_recid = @t_system_workflows AND element_name = 'element_status');
INSERT INTO dbo.system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_system_workflows, 7, 'element_created_on', 6, 0, '(sysutcdatetime())', NULL, 0, 0 WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_columns WHERE tables_recid = @t_system_workflows AND element_name = 'element_created_on');
INSERT INTO dbo.system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_system_workflows, 7, 'element_modified_on', 7, 0, '(sysutcdatetime())', NULL, 0, 0 WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_columns WHERE tables_recid = @t_system_workflows AND element_name = 'element_modified_on');
GO

INSERT INTO dbo.system_schema_tables (element_name, element_schema)
SELECT 'system_workflow_steps', 'dbo'
WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_tables WHERE element_name = 'system_workflow_steps' AND element_schema = 'dbo');
GO

DECLARE @t_system_workflow_steps BIGINT = (SELECT recid FROM dbo.system_schema_tables WHERE element_name = 'system_workflow_steps' AND element_schema = 'dbo');
INSERT INTO dbo.system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_system_workflow_steps, 4, 'element_guid', 1, 0, '(newid())', NULL, 1, 0 WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_columns WHERE tables_recid = @t_system_workflow_steps AND element_name = 'element_guid');
INSERT INTO dbo.system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_system_workflow_steps, 4, 'workflows_guid', 2, 0, NULL, NULL, 0, 0 WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_columns WHERE tables_recid = @t_system_workflow_steps AND element_name = 'workflows_guid');
INSERT INTO dbo.system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_system_workflow_steps, 8, 'element_name', 3, 0, NULL, 128, 0, 0 WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_columns WHERE tables_recid = @t_system_workflow_steps AND element_name = 'element_name');
INSERT INTO dbo.system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_system_workflow_steps, 8, 'element_description', 4, 1, NULL, 1024, 0, 0 WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_columns WHERE tables_recid = @t_system_workflow_steps AND element_name = 'element_description');
INSERT INTO dbo.system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_system_workflow_steps, 8, 'element_step_type', 5, 0, '''pipe''', 16, 0, 0 WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_columns WHERE tables_recid = @t_system_workflow_steps AND element_name = 'element_step_type');
INSERT INTO dbo.system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_system_workflow_steps, 8, 'element_disposition', 6, 0, '''harmless''', 16, 0, 0 WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_columns WHERE tables_recid = @t_system_workflow_steps AND element_name = 'element_disposition');
INSERT INTO dbo.system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_system_workflow_steps, 8, 'element_class_path', 7, 0, NULL, 512, 0, 0 WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_columns WHERE tables_recid = @t_system_workflow_steps AND element_name = 'element_class_path');
INSERT INTO dbo.system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_system_workflow_steps, 1, 'element_sequence', 8, 0, NULL, NULL, 0, 0 WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_columns WHERE tables_recid = @t_system_workflow_steps AND element_name = 'element_sequence');
INSERT INTO dbo.system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_system_workflow_steps, 5, 'element_is_optional', 9, 0, '((0))', NULL, 0, 0 WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_columns WHERE tables_recid = @t_system_workflow_steps AND element_name = 'element_is_optional');
INSERT INTO dbo.system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_system_workflow_steps, 1, 'element_timeout_seconds', 10, 1, NULL, NULL, 0, 0 WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_columns WHERE tables_recid = @t_system_workflow_steps AND element_name = 'element_timeout_seconds');
INSERT INTO dbo.system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_system_workflow_steps, 9, 'element_config', 11, 1, NULL, -1, 0, 0 WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_columns WHERE tables_recid = @t_system_workflow_steps AND element_name = 'element_config');
INSERT INTO dbo.system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_system_workflow_steps, 7, 'element_created_on', 12, 0, '(sysutcdatetime())', NULL, 0, 0 WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_columns WHERE tables_recid = @t_system_workflow_steps AND element_name = 'element_created_on');
INSERT INTO dbo.system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_system_workflow_steps, 7, 'element_modified_on', 13, 0, '(sysutcdatetime())', NULL, 0, 0 WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_columns WHERE tables_recid = @t_system_workflow_steps AND element_name = 'element_modified_on');
GO

INSERT INTO dbo.system_schema_tables (element_name, element_schema)
SELECT 'system_workflow_runs', 'dbo'
WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_tables WHERE element_name = 'system_workflow_runs' AND element_schema = 'dbo');
GO

DECLARE @t_system_workflow_runs BIGINT = (SELECT recid FROM dbo.system_schema_tables WHERE element_name = 'system_workflow_runs' AND element_schema = 'dbo');
INSERT INTO dbo.system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_system_workflow_runs, 3, 'recid', 1, 0, NULL, NULL, 1, 1 WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_columns WHERE tables_recid = @t_system_workflow_runs AND element_name = 'recid');
INSERT INTO dbo.system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_system_workflow_runs, 4, 'element_guid', 2, 0, '(newid())', NULL, 0, 0 WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_columns WHERE tables_recid = @t_system_workflow_runs AND element_name = 'element_guid');
INSERT INTO dbo.system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_system_workflow_runs, 4, 'workflows_guid', 2, 0, NULL, NULL, 0, 0 WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_columns WHERE tables_recid = @t_system_workflow_runs AND element_name = 'workflows_guid');
INSERT INTO dbo.system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_system_workflow_runs, 11, 'element_status', 4, 0, '((0))', NULL, 0, 0 WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_columns WHERE tables_recid = @t_system_workflow_runs AND element_name = 'element_status');
INSERT INTO dbo.system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_system_workflow_runs, 9, 'element_payload', 5, 1, NULL, -1, 0, 0 WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_columns WHERE tables_recid = @t_system_workflow_runs AND element_name = 'element_payload');
INSERT INTO dbo.system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_system_workflow_runs, 9, 'element_context', 6, 1, NULL, -1, 0, 0 WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_columns WHERE tables_recid = @t_system_workflow_runs AND element_name = 'element_context');
INSERT INTO dbo.system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_system_workflow_runs, 8, 'element_current_step', 7, 1, NULL, 128, 0, 0 WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_columns WHERE tables_recid = @t_system_workflow_runs AND element_name = 'element_current_step');
INSERT INTO dbo.system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_system_workflow_runs, 1, 'element_step_index', 8, 0, '((0))', NULL, 0, 0 WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_columns WHERE tables_recid = @t_system_workflow_runs AND element_name = 'element_step_index');
INSERT INTO dbo.system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_system_workflow_runs, 9, 'element_error', 9, 1, NULL, -1, 0, 0 WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_columns WHERE tables_recid = @t_system_workflow_runs AND element_name = 'element_error');
INSERT INTO dbo.system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_system_workflow_runs, 8, 'element_source_type', 10, 1, NULL, 64, 0, 0 WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_columns WHERE tables_recid = @t_system_workflow_runs AND element_name = 'element_source_type');
INSERT INTO dbo.system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_system_workflow_runs, 8, 'element_source_id', 11, 1, NULL, 256, 0, 0 WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_columns WHERE tables_recid = @t_system_workflow_runs AND element_name = 'element_source_id');
INSERT INTO dbo.system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_system_workflow_runs, 4, 'element_created_by', 12, 1, NULL, NULL, 0, 0 WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_columns WHERE tables_recid = @t_system_workflow_runs AND element_name = 'element_created_by');
INSERT INTO dbo.system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_system_workflow_runs, 7, 'element_started_on', 13, 1, NULL, NULL, 0, 0 WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_columns WHERE tables_recid = @t_system_workflow_runs AND element_name = 'element_started_on');
INSERT INTO dbo.system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_system_workflow_runs, 7, 'element_ended_on', 14, 1, NULL, NULL, 0, 0 WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_columns WHERE tables_recid = @t_system_workflow_runs AND element_name = 'element_ended_on');
INSERT INTO dbo.system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_system_workflow_runs, 7, 'element_timeout_at', 15, 1, NULL, NULL, 0, 0 WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_columns WHERE tables_recid = @t_system_workflow_runs AND element_name = 'element_timeout_at');
INSERT INTO dbo.system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_system_workflow_runs, 7, 'element_created_on', 16, 0, '(sysutcdatetime())', NULL, 0, 0 WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_columns WHERE tables_recid = @t_system_workflow_runs AND element_name = 'element_created_on');
INSERT INTO dbo.system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_system_workflow_runs, 7, 'element_modified_on', 17, 0, '(sysutcdatetime())', NULL, 0, 0 WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_columns WHERE tables_recid = @t_system_workflow_runs AND element_name = 'element_modified_on');
GO

INSERT INTO dbo.system_schema_tables (element_name, element_schema)
SELECT 'system_workflow_run_steps', 'dbo'
WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_tables WHERE element_name = 'system_workflow_run_steps' AND element_schema = 'dbo');
GO

DECLARE @t_system_workflow_run_steps BIGINT = (SELECT recid FROM dbo.system_schema_tables WHERE element_name = 'system_workflow_run_steps' AND element_schema = 'dbo');
INSERT INTO dbo.system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_system_workflow_run_steps, 3, 'recid', 1, 0, NULL, NULL, 1, 1 WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_columns WHERE tables_recid = @t_system_workflow_run_steps AND element_name = 'recid');
INSERT INTO dbo.system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_system_workflow_run_steps, 4, 'element_guid', 2, 0, '(newid())', NULL, 0, 0 WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_columns WHERE tables_recid = @t_system_workflow_run_steps AND element_name = 'element_guid');
INSERT INTO dbo.system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_system_workflow_run_steps, 2, 'runs_recid', 3, 0, NULL, NULL, 0, 0 WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_columns WHERE tables_recid = @t_system_workflow_run_steps AND element_name = 'runs_recid');
INSERT INTO dbo.system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_system_workflow_run_steps, 4, 'steps_guid', 4, 0, NULL, NULL, 0, 0 WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_columns WHERE tables_recid = @t_system_workflow_run_steps AND element_name = 'steps_guid');
INSERT INTO dbo.system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_system_workflow_run_steps, 11, 'element_status', 5, 0, '((0))', NULL, 0, 0 WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_columns WHERE tables_recid = @t_system_workflow_run_steps AND element_name = 'element_status');
INSERT INTO dbo.system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_system_workflow_run_steps, 8, 'element_disposition', 6, 0, NULL, 16, 0, 0 WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_columns WHERE tables_recid = @t_system_workflow_run_steps AND element_name = 'element_disposition');
INSERT INTO dbo.system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_system_workflow_run_steps, 9, 'element_input', 7, 1, NULL, -1, 0, 0 WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_columns WHERE tables_recid = @t_system_workflow_run_steps AND element_name = 'element_input');
INSERT INTO dbo.system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_system_workflow_run_steps, 9, 'element_output', 8, 1, NULL, -1, 0, 0 WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_columns WHERE tables_recid = @t_system_workflow_run_steps AND element_name = 'element_output');
INSERT INTO dbo.system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_system_workflow_run_steps, 9, 'element_error', 9, 1, NULL, -1, 0, 0 WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_columns WHERE tables_recid = @t_system_workflow_run_steps AND element_name = 'element_error');
INSERT INTO dbo.system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_system_workflow_run_steps, 7, 'element_started_on', 10, 1, NULL, NULL, 0, 0 WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_columns WHERE tables_recid = @t_system_workflow_run_steps AND element_name = 'element_started_on');
INSERT INTO dbo.system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_system_workflow_run_steps, 7, 'element_ended_on', 11, 1, NULL, NULL, 0, 0 WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_columns WHERE tables_recid = @t_system_workflow_run_steps AND element_name = 'element_ended_on');
INSERT INTO dbo.system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_system_workflow_run_steps, 7, 'element_created_on', 12, 0, '(sysutcdatetime())', NULL, 0, 0 WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_columns WHERE tables_recid = @t_system_workflow_run_steps AND element_name = 'element_created_on');
INSERT INTO dbo.system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_system_workflow_run_steps, 7, 'element_modified_on', 13, 0, '(sysutcdatetime())', NULL, 0, 0 WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_columns WHERE tables_recid = @t_system_workflow_run_steps AND element_name = 'element_modified_on');
GO

INSERT INTO dbo.system_schema_indexes (tables_recid, element_name, element_columns, element_is_unique)
SELECT t.recid, 'PK_system_workflows', 'element_guid', 1
FROM dbo.system_schema_tables t
WHERE t.element_name = 'system_workflows' AND t.element_schema = 'dbo'
  AND NOT EXISTS (SELECT 1 FROM dbo.system_schema_indexes i WHERE i.tables_recid = t.recid AND i.element_name = 'PK_system_workflows');
INSERT INTO dbo.system_schema_indexes (tables_recid, element_name, element_columns, element_is_unique)
SELECT t.recid, 'UQ_system_workflows_name_version', 'element_name,element_version', 1
FROM dbo.system_schema_tables t
WHERE t.element_name = 'system_workflows' AND t.element_schema = 'dbo'
  AND NOT EXISTS (SELECT 1 FROM dbo.system_schema_indexes i WHERE i.tables_recid = t.recid AND i.element_name = 'UQ_system_workflows_name_version');
GO

INSERT INTO dbo.system_schema_indexes (tables_recid, element_name, element_columns, element_is_unique)
SELECT t.recid, 'PK_system_workflow_steps', 'element_guid', 1
FROM dbo.system_schema_tables t
WHERE t.element_name = 'system_workflow_steps' AND t.element_schema = 'dbo'
  AND NOT EXISTS (SELECT 1 FROM dbo.system_schema_indexes i WHERE i.tables_recid = t.recid AND i.element_name = 'PK_system_workflow_steps');
INSERT INTO dbo.system_schema_indexes (tables_recid, element_name, element_columns, element_is_unique)
SELECT t.recid, 'UQ_system_workflow_steps_workflow_sequence', 'workflows_guid,element_sequence', 1
FROM dbo.system_schema_tables t
WHERE t.element_name = 'system_workflow_steps' AND t.element_schema = 'dbo'
  AND NOT EXISTS (SELECT 1 FROM dbo.system_schema_indexes i WHERE i.tables_recid = t.recid AND i.element_name = 'UQ_system_workflow_steps_workflow_sequence');
INSERT INTO dbo.system_schema_indexes (tables_recid, element_name, element_columns, element_is_unique)
SELECT t.recid, 'UQ_system_workflow_steps_workflow_name', 'workflows_guid,element_name', 1
FROM dbo.system_schema_tables t
WHERE t.element_name = 'system_workflow_steps' AND t.element_schema = 'dbo'
  AND NOT EXISTS (SELECT 1 FROM dbo.system_schema_indexes i WHERE i.tables_recid = t.recid AND i.element_name = 'UQ_system_workflow_steps_workflow_name');
GO

INSERT INTO dbo.system_schema_indexes (tables_recid, element_name, element_columns, element_is_unique)
SELECT t.recid, 'PK_system_workflow_runs', 'recid', 1
FROM dbo.system_schema_tables t
WHERE t.element_name = 'system_workflow_runs' AND t.element_schema = 'dbo'
  AND NOT EXISTS (SELECT 1 FROM dbo.system_schema_indexes i WHERE i.tables_recid = t.recid AND i.element_name = 'PK_system_workflow_runs');
INSERT INTO dbo.system_schema_indexes (tables_recid, element_name, element_columns, element_is_unique)
SELECT t.recid, 'UQ_system_workflow_runs_guid', 'element_guid', 1
FROM dbo.system_schema_tables t
WHERE t.element_name = 'system_workflow_runs' AND t.element_schema = 'dbo'
  AND NOT EXISTS (SELECT 1 FROM dbo.system_schema_indexes i WHERE i.tables_recid = t.recid AND i.element_name = 'UQ_system_workflow_runs_guid');
INSERT INTO dbo.system_schema_indexes (tables_recid, element_name, element_columns, element_is_unique)
SELECT t.recid, 'IX_system_workflow_runs_status', 'element_status', 0
FROM dbo.system_schema_tables t
WHERE t.element_name = 'system_workflow_runs' AND t.element_schema = 'dbo'
  AND NOT EXISTS (SELECT 1 FROM dbo.system_schema_indexes i WHERE i.tables_recid = t.recid AND i.element_name = 'IX_system_workflow_runs_status');
INSERT INTO dbo.system_schema_indexes (tables_recid, element_name, element_columns, element_is_unique)
SELECT t.recid, 'IX_system_workflow_runs_workflow', 'workflows_guid', 0
FROM dbo.system_schema_tables t
WHERE t.element_name = 'system_workflow_runs' AND t.element_schema = 'dbo'
  AND NOT EXISTS (SELECT 1 FROM dbo.system_schema_indexes i WHERE i.tables_recid = t.recid AND i.element_name = 'IX_system_workflow_runs_workflow');
GO

INSERT INTO dbo.system_schema_indexes (tables_recid, element_name, element_columns, element_is_unique)
SELECT t.recid, 'PK_system_workflow_run_steps', 'recid', 1
FROM dbo.system_schema_tables t
WHERE t.element_name = 'system_workflow_run_steps' AND t.element_schema = 'dbo'
  AND NOT EXISTS (SELECT 1 FROM dbo.system_schema_indexes i WHERE i.tables_recid = t.recid AND i.element_name = 'PK_system_workflow_run_steps');
INSERT INTO dbo.system_schema_indexes (tables_recid, element_name, element_columns, element_is_unique)
SELECT t.recid, 'UQ_system_workflow_run_steps_guid', 'element_guid', 1
FROM dbo.system_schema_tables t
WHERE t.element_name = 'system_workflow_run_steps' AND t.element_schema = 'dbo'
  AND NOT EXISTS (SELECT 1 FROM dbo.system_schema_indexes i WHERE i.tables_recid = t.recid AND i.element_name = 'UQ_system_workflow_run_steps_guid');
INSERT INTO dbo.system_schema_indexes (tables_recid, element_name, element_columns, element_is_unique)
SELECT t.recid, 'IX_system_workflow_run_steps_run', 'runs_recid,element_created_on', 0
FROM dbo.system_schema_tables t
WHERE t.element_name = 'system_workflow_run_steps' AND t.element_schema = 'dbo'
  AND NOT EXISTS (SELECT 1 FROM dbo.system_schema_indexes i WHERE i.tables_recid = t.recid AND i.element_name = 'IX_system_workflow_run_steps_run');
GO

INSERT INTO dbo.system_schema_foreign_keys (tables_recid, element_column_name, referenced_tables_recid, element_referenced_column)
SELECT s.recid, 'workflows_guid', r.recid, 'element_guid'
FROM dbo.system_schema_tables s CROSS JOIN dbo.system_schema_tables r
WHERE s.element_name = 'system_workflow_steps' AND s.element_schema = 'dbo'
  AND r.element_name = 'system_workflows' AND r.element_schema = 'dbo'
  AND NOT EXISTS (SELECT 1 FROM dbo.system_schema_foreign_keys fk WHERE fk.tables_recid = s.recid AND fk.element_column_name = 'workflows_guid');
INSERT INTO dbo.system_schema_foreign_keys (tables_recid, element_column_name, referenced_tables_recid, element_referenced_column)
SELECT s.recid, 'workflows_guid', r.recid, 'element_guid'
FROM dbo.system_schema_tables s CROSS JOIN dbo.system_schema_tables r
WHERE s.element_name = 'system_workflow_runs' AND s.element_schema = 'dbo'
  AND r.element_name = 'system_workflows' AND r.element_schema = 'dbo'
  AND NOT EXISTS (SELECT 1 FROM dbo.system_schema_foreign_keys fk WHERE fk.tables_recid = s.recid AND fk.element_column_name = 'workflows_guid');
INSERT INTO dbo.system_schema_foreign_keys (tables_recid, element_column_name, referenced_tables_recid, element_referenced_column)
SELECT s.recid, 'runs_recid', r.recid, 'recid'
FROM dbo.system_schema_tables s CROSS JOIN dbo.system_schema_tables r
WHERE s.element_name = 'system_workflow_run_steps' AND s.element_schema = 'dbo'
  AND r.element_name = 'system_workflow_runs' AND r.element_schema = 'dbo'
  AND NOT EXISTS (SELECT 1 FROM dbo.system_schema_foreign_keys fk WHERE fk.tables_recid = s.recid AND fk.element_column_name = 'runs_recid');
INSERT INTO dbo.system_schema_foreign_keys (tables_recid, element_column_name, referenced_tables_recid, element_referenced_column)
SELECT s.recid, 'steps_guid', r.recid, 'element_guid'
FROM dbo.system_schema_tables s CROSS JOIN dbo.system_schema_tables r
WHERE s.element_name = 'system_workflow_run_steps' AND s.element_schema = 'dbo'
  AND r.element_name = 'system_workflow_steps' AND r.element_schema = 'dbo'
  AND NOT EXISTS (SELECT 1 FROM dbo.system_schema_foreign_keys fk WHERE fk.tables_recid = s.recid AND fk.element_column_name = 'steps_guid');
GO
