SET NOCOUNT ON;
GO

/*
  Step 1: Create lookup tables and register reflection metadata.
*/

IF OBJECT_ID('dbo.system_automation_statuses', 'U') IS NULL
BEGIN
  CREATE TABLE dbo.system_automation_statuses (
    recid TINYINT NOT NULL,
    element_slug NVARCHAR(32) NOT NULL,
    element_name NVARCHAR(64) NOT NULL,
    element_description NVARCHAR(256) NULL,
    element_is_terminal BIT NOT NULL,
    element_allows_retry BIT NOT NULL,
    element_allows_resume BIT NOT NULL,
    element_created_on DATETIMEOFFSET(7) NOT NULL CONSTRAINT DF_system_automation_statuses_created_on DEFAULT SYSUTCDATETIME(),
    element_modified_on DATETIMEOFFSET(7) NOT NULL CONSTRAINT DF_system_automation_statuses_modified_on DEFAULT SYSUTCDATETIME(),
    CONSTRAINT PK_system_automation_statuses PRIMARY KEY (recid),
    CONSTRAINT UQ_system_automation_statuses_slug UNIQUE (element_slug)
  );
END;
GO

INSERT INTO dbo.system_automation_statuses (recid, element_slug, element_name, element_description, element_is_terminal, element_allows_retry, element_allows_resume)
SELECT v.recid, v.element_slug, v.element_name, v.element_description, v.element_is_terminal, v.element_allows_retry, v.element_allows_resume
FROM (VALUES
  (0, 'pending', 'Pending', 'Created, not yet started', 0, 0, 0),
  (1, 'running', 'Running', 'Currently executing', 0, 0, 0),
  (2, 'completed', 'Completed', 'Finished successfully', 1, 0, 0),
  (3, 'failed', 'Failed', 'Terminated due to error', 0, 1, 1),
  (4, 'cancelled', 'Cancelled', 'Terminated by external request', 1, 0, 0),
  (5, 'waiting', 'Waiting', 'Awaiting external operation completion', 0, 0, 0),
  (6, 'paused', 'Paused', 'Explicitly paused by human or system', 0, 0, 1),
  (7, 'rolling_back', 'Rolling Back', 'Executing rollback of completed actions', 0, 0, 0),
  (8, 'rolled_back', 'Rolled Back', 'Rollback completed', 1, 0, 0),
  (9, 'rollback_failed', 'Rollback Failed', 'Rollback itself failed, requires manual intervention', 0, 1, 0),
  (10, 'stalled', 'Stalled', 'Detected as running/waiting longer than expected', 0, 1, 1)
) v(recid, element_slug, element_name, element_description, element_is_terminal, element_allows_retry, element_allows_resume)
WHERE NOT EXISTS (SELECT 1 FROM dbo.system_automation_statuses s WHERE s.recid = v.recid);
GO

IF OBJECT_ID('dbo.system_trigger_types', 'U') IS NULL
BEGIN
  CREATE TABLE dbo.system_trigger_types (
    recid TINYINT NOT NULL,
    element_slug NVARCHAR(32) NOT NULL,
    element_name NVARCHAR(64) NOT NULL,
    element_description NVARCHAR(256) NULL,
    element_created_on DATETIMEOFFSET(7) NOT NULL CONSTRAINT DF_system_trigger_types_created_on DEFAULT SYSUTCDATETIME(),
    element_modified_on DATETIMEOFFSET(7) NOT NULL CONSTRAINT DF_system_trigger_types_modified_on DEFAULT SYSUTCDATETIME(),
    CONSTRAINT PK_system_trigger_types PRIMARY KEY (recid),
    CONSTRAINT UQ_system_trigger_types_slug UNIQUE (element_slug)
  );
END;
GO

INSERT INTO dbo.system_trigger_types (recid, element_slug, element_name, element_description)
SELECT v.recid, v.element_slug, v.element_name, v.element_description
FROM (VALUES
  (0, 'manual', 'Manual', 'Triggered by an operator through management UI or direct API call'),
  (1, 'schedule', 'Schedule', 'Fired by a Scheduled Task on its cron timer'),
  (2, 'rpc', 'RPC', 'Invoked via an authenticated RPC call from a client'),
  (3, 'mcp', 'MCP', 'Invoked via an MCP tool call'),
  (4, 'discord', 'Discord', 'Initiated by a Discord bot command'),
  (5, 'workflow', 'Workflow', 'Spawned by another Workflow Run action (child workflow)'),
  (6, 'webhook', 'Webhook', 'Initiated by an inbound webhook from an external system'),
  (7, 'poll', 'Poll', 'Initiated by an internal poll loop detecting a state change')
) v(recid, element_slug, element_name, element_description)
WHERE NOT EXISTS (SELECT 1 FROM dbo.system_trigger_types t WHERE t.recid = v.recid);
GO

IF OBJECT_ID('dbo.system_dispositions', 'U') IS NULL
BEGIN
  CREATE TABLE dbo.system_dispositions (
    recid TINYINT NOT NULL,
    element_slug NVARCHAR(32) NOT NULL,
    element_name NVARCHAR(64) NOT NULL,
    element_description NVARCHAR(256) NULL,
    element_allows_rollback BIT NOT NULL,
    element_allows_retry BIT NOT NULL,
    element_created_on DATETIMEOFFSET(7) NOT NULL CONSTRAINT DF_system_dispositions_created_on DEFAULT SYSUTCDATETIME(),
    element_modified_on DATETIMEOFFSET(7) NOT NULL CONSTRAINT DF_system_dispositions_modified_on DEFAULT SYSUTCDATETIME(),
    CONSTRAINT PK_system_dispositions PRIMARY KEY (recid),
    CONSTRAINT UQ_system_dispositions_slug UNIQUE (element_slug)
  );
END;
GO

INSERT INTO dbo.system_dispositions (recid, element_slug, element_name, element_description, element_allows_rollback, element_allows_retry)
SELECT v.recid, v.element_slug, v.element_name, v.element_description, v.element_allows_rollback, v.element_allows_retry
FROM (VALUES
  (0, 'pure', 'Pure', 'No side effects. Reads data, computes, transforms.', 0, 1),
  (1, 'reversible', 'Reversible', 'Writes data that can be mechanically undone via a rollback function.', 1, 1),
  (2, 'irreversible', 'Irreversible', 'Writes data or triggers external effects that cannot be undone.', 0, 0),
  (3, 'idempotent', 'Idempotent', 'Writes data but can be safely called again without duplicating effects.', 0, 1)
) v(recid, element_slug, element_name, element_description, element_allows_rollback, element_allows_retry)
WHERE NOT EXISTS (SELECT 1 FROM dbo.system_dispositions d WHERE d.recid = v.recid);
GO

IF OBJECT_ID('dbo.system_workflow_statuses', 'U') IS NULL
BEGIN
  CREATE TABLE dbo.system_workflow_statuses (
    recid TINYINT NOT NULL,
    element_slug NVARCHAR(32) NOT NULL,
    element_name NVARCHAR(64) NOT NULL,
    element_created_on DATETIMEOFFSET(7) NOT NULL CONSTRAINT DF_system_workflow_statuses_created_on DEFAULT SYSUTCDATETIME(),
    element_modified_on DATETIMEOFFSET(7) NOT NULL CONSTRAINT DF_system_workflow_statuses_modified_on DEFAULT SYSUTCDATETIME(),
    CONSTRAINT PK_system_workflow_statuses PRIMARY KEY (recid),
    CONSTRAINT UQ_system_workflow_statuses_slug UNIQUE (element_slug)
  );
END;
GO

INSERT INTO dbo.system_workflow_statuses (recid, element_slug, element_name)
SELECT v.recid, v.element_slug, v.element_name
FROM (VALUES
  (0, 'draft', 'Draft'),
  (1, 'published', 'Published'),
  (2, 'retired', 'Retired')
) v(recid, element_slug, element_name)
WHERE NOT EXISTS (SELECT 1 FROM dbo.system_workflow_statuses s WHERE s.recid = v.recid);
GO

IF OBJECT_ID('dbo.system_scheduled_task_statuses', 'U') IS NULL
BEGIN
  CREATE TABLE dbo.system_scheduled_task_statuses (
    recid TINYINT NOT NULL,
    element_slug NVARCHAR(32) NOT NULL,
    element_name NVARCHAR(64) NOT NULL,
    element_created_on DATETIMEOFFSET(7) NOT NULL CONSTRAINT DF_system_scheduled_task_statuses_created_on DEFAULT SYSUTCDATETIME(),
    element_modified_on DATETIMEOFFSET(7) NOT NULL CONSTRAINT DF_system_scheduled_task_statuses_modified_on DEFAULT SYSUTCDATETIME(),
    CONSTRAINT PK_system_scheduled_task_statuses PRIMARY KEY (recid),
    CONSTRAINT UQ_system_scheduled_task_statuses_slug UNIQUE (element_slug)
  );
END;
GO

INSERT INTO dbo.system_scheduled_task_statuses (recid, element_slug, element_name)
SELECT v.recid, v.element_slug, v.element_name
FROM (VALUES
  (0, 'disabled', 'Disabled'),
  (1, 'enabled', 'Enabled'),
  (2, 'suspended', 'Suspended')
) v(recid, element_slug, element_name)
WHERE NOT EXISTS (SELECT 1 FROM dbo.system_scheduled_task_statuses s WHERE s.recid = v.recid);
GO

INSERT INTO dbo.system_schema_tables (element_name, element_schema)
SELECT 'system_automation_statuses', 'dbo'
WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_tables WHERE element_name = 'system_automation_statuses' AND element_schema = 'dbo');
INSERT INTO dbo.system_schema_tables (element_name, element_schema)
SELECT 'system_trigger_types', 'dbo'
WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_tables WHERE element_name = 'system_trigger_types' AND element_schema = 'dbo');
INSERT INTO dbo.system_schema_tables (element_name, element_schema)
SELECT 'system_dispositions', 'dbo'
WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_tables WHERE element_name = 'system_dispositions' AND element_schema = 'dbo');
INSERT INTO dbo.system_schema_tables (element_name, element_schema)
SELECT 'system_workflow_statuses', 'dbo'
WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_tables WHERE element_name = 'system_workflow_statuses' AND element_schema = 'dbo');
INSERT INTO dbo.system_schema_tables (element_name, element_schema)
SELECT 'system_scheduled_task_statuses', 'dbo'
WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_tables WHERE element_name = 'system_scheduled_task_statuses' AND element_schema = 'dbo');
GO

DECLARE @t_system_automation_statuses BIGINT = (SELECT recid FROM dbo.system_schema_tables WHERE element_name = 'system_automation_statuses' AND element_schema = 'dbo');
INSERT INTO dbo.system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_system_automation_statuses, 11, 'recid', 1, 0, NULL, NULL, 1, 0 WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_columns WHERE tables_recid = @t_system_automation_statuses AND element_name = 'recid');
INSERT INTO dbo.system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_system_automation_statuses, 8, 'element_slug', 2, 0, NULL, 32, 0, 0 WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_columns WHERE tables_recid = @t_system_automation_statuses AND element_name = 'element_slug');
INSERT INTO dbo.system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_system_automation_statuses, 8, 'element_name', 3, 0, NULL, 64, 0, 0 WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_columns WHERE tables_recid = @t_system_automation_statuses AND element_name = 'element_name');
INSERT INTO dbo.system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_system_automation_statuses, 8, 'element_description', 4, 1, NULL, 256, 0, 0 WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_columns WHERE tables_recid = @t_system_automation_statuses AND element_name = 'element_description');
INSERT INTO dbo.system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_system_automation_statuses, 5, 'element_is_terminal', 5, 0, NULL, NULL, 0, 0 WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_columns WHERE tables_recid = @t_system_automation_statuses AND element_name = 'element_is_terminal');
INSERT INTO dbo.system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_system_automation_statuses, 5, 'element_allows_retry', 6, 0, NULL, NULL, 0, 0 WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_columns WHERE tables_recid = @t_system_automation_statuses AND element_name = 'element_allows_retry');
INSERT INTO dbo.system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_system_automation_statuses, 5, 'element_allows_resume', 7, 0, NULL, NULL, 0, 0 WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_columns WHERE tables_recid = @t_system_automation_statuses AND element_name = 'element_allows_resume');
INSERT INTO dbo.system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_system_automation_statuses, 7, 'element_created_on', 8, 0, '(sysutcdatetime())', NULL, 0, 0 WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_columns WHERE tables_recid = @t_system_automation_statuses AND element_name = 'element_created_on');
INSERT INTO dbo.system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_system_automation_statuses, 7, 'element_modified_on', 9, 0, '(sysutcdatetime())', NULL, 0, 0 WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_columns WHERE tables_recid = @t_system_automation_statuses AND element_name = 'element_modified_on');
GO

DECLARE @t_system_trigger_types BIGINT = (SELECT recid FROM dbo.system_schema_tables WHERE element_name = 'system_trigger_types' AND element_schema = 'dbo');
INSERT INTO dbo.system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_system_trigger_types, 11, 'recid', 1, 0, NULL, NULL, 1, 0 WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_columns WHERE tables_recid = @t_system_trigger_types AND element_name = 'recid');
INSERT INTO dbo.system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_system_trigger_types, 8, 'element_slug', 2, 0, NULL, 32, 0, 0 WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_columns WHERE tables_recid = @t_system_trigger_types AND element_name = 'element_slug');
INSERT INTO dbo.system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_system_trigger_types, 8, 'element_name', 3, 0, NULL, 64, 0, 0 WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_columns WHERE tables_recid = @t_system_trigger_types AND element_name = 'element_name');
INSERT INTO dbo.system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_system_trigger_types, 8, 'element_description', 4, 1, NULL, 256, 0, 0 WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_columns WHERE tables_recid = @t_system_trigger_types AND element_name = 'element_description');
INSERT INTO dbo.system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_system_trigger_types, 7, 'element_created_on', 5, 0, '(sysutcdatetime())', NULL, 0, 0 WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_columns WHERE tables_recid = @t_system_trigger_types AND element_name = 'element_created_on');
INSERT INTO dbo.system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_system_trigger_types, 7, 'element_modified_on', 6, 0, '(sysutcdatetime())', NULL, 0, 0 WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_columns WHERE tables_recid = @t_system_trigger_types AND element_name = 'element_modified_on');
GO

DECLARE @t_system_dispositions BIGINT = (SELECT recid FROM dbo.system_schema_tables WHERE element_name = 'system_dispositions' AND element_schema = 'dbo');
INSERT INTO dbo.system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_system_dispositions, 11, 'recid', 1, 0, NULL, NULL, 1, 0 WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_columns WHERE tables_recid = @t_system_dispositions AND element_name = 'recid');
INSERT INTO dbo.system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_system_dispositions, 8, 'element_slug', 2, 0, NULL, 32, 0, 0 WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_columns WHERE tables_recid = @t_system_dispositions AND element_name = 'element_slug');
INSERT INTO dbo.system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_system_dispositions, 8, 'element_name', 3, 0, NULL, 64, 0, 0 WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_columns WHERE tables_recid = @t_system_dispositions AND element_name = 'element_name');
INSERT INTO dbo.system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_system_dispositions, 8, 'element_description', 4, 1, NULL, 256, 0, 0 WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_columns WHERE tables_recid = @t_system_dispositions AND element_name = 'element_description');
INSERT INTO dbo.system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_system_dispositions, 5, 'element_allows_rollback', 5, 0, NULL, NULL, 0, 0 WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_columns WHERE tables_recid = @t_system_dispositions AND element_name = 'element_allows_rollback');
INSERT INTO dbo.system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_system_dispositions, 5, 'element_allows_retry', 6, 0, NULL, NULL, 0, 0 WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_columns WHERE tables_recid = @t_system_dispositions AND element_name = 'element_allows_retry');
INSERT INTO dbo.system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_system_dispositions, 7, 'element_created_on', 7, 0, '(sysutcdatetime())', NULL, 0, 0 WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_columns WHERE tables_recid = @t_system_dispositions AND element_name = 'element_created_on');
INSERT INTO dbo.system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_system_dispositions, 7, 'element_modified_on', 8, 0, '(sysutcdatetime())', NULL, 0, 0 WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_columns WHERE tables_recid = @t_system_dispositions AND element_name = 'element_modified_on');
GO

DECLARE @t_system_workflow_statuses BIGINT = (SELECT recid FROM dbo.system_schema_tables WHERE element_name = 'system_workflow_statuses' AND element_schema = 'dbo');
INSERT INTO dbo.system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_system_workflow_statuses, 11, 'recid', 1, 0, NULL, NULL, 1, 0 WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_columns WHERE tables_recid = @t_system_workflow_statuses AND element_name = 'recid');
INSERT INTO dbo.system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_system_workflow_statuses, 8, 'element_slug', 2, 0, NULL, 32, 0, 0 WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_columns WHERE tables_recid = @t_system_workflow_statuses AND element_name = 'element_slug');
INSERT INTO dbo.system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_system_workflow_statuses, 8, 'element_name', 3, 0, NULL, 64, 0, 0 WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_columns WHERE tables_recid = @t_system_workflow_statuses AND element_name = 'element_name');
INSERT INTO dbo.system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_system_workflow_statuses, 7, 'element_created_on', 4, 0, '(sysutcdatetime())', NULL, 0, 0 WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_columns WHERE tables_recid = @t_system_workflow_statuses AND element_name = 'element_created_on');
INSERT INTO dbo.system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_system_workflow_statuses, 7, 'element_modified_on', 5, 0, '(sysutcdatetime())', NULL, 0, 0 WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_columns WHERE tables_recid = @t_system_workflow_statuses AND element_name = 'element_modified_on');
GO

DECLARE @t_system_scheduled_task_statuses BIGINT = (SELECT recid FROM dbo.system_schema_tables WHERE element_name = 'system_scheduled_task_statuses' AND element_schema = 'dbo');
INSERT INTO dbo.system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_system_scheduled_task_statuses, 11, 'recid', 1, 0, NULL, NULL, 1, 0 WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_columns WHERE tables_recid = @t_system_scheduled_task_statuses AND element_name = 'recid');
INSERT INTO dbo.system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_system_scheduled_task_statuses, 8, 'element_slug', 2, 0, NULL, 32, 0, 0 WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_columns WHERE tables_recid = @t_system_scheduled_task_statuses AND element_name = 'element_slug');
INSERT INTO dbo.system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_system_scheduled_task_statuses, 8, 'element_name', 3, 0, NULL, 64, 0, 0 WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_columns WHERE tables_recid = @t_system_scheduled_task_statuses AND element_name = 'element_name');
INSERT INTO dbo.system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_system_scheduled_task_statuses, 7, 'element_created_on', 4, 0, '(sysutcdatetime())', NULL, 0, 0 WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_columns WHERE tables_recid = @t_system_scheduled_task_statuses AND element_name = 'element_created_on');
INSERT INTO dbo.system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_system_scheduled_task_statuses, 7, 'element_modified_on', 5, 0, '(sysutcdatetime())', NULL, 0, 0 WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_columns WHERE tables_recid = @t_system_scheduled_task_statuses AND element_name = 'element_modified_on');
GO

INSERT INTO dbo.system_schema_indexes (tables_recid, element_name, element_columns, element_is_unique)
SELECT t.recid, 'PK_system_automation_statuses', 'recid', 1 FROM dbo.system_schema_tables t
WHERE t.element_name = 'system_automation_statuses' AND t.element_schema = 'dbo'
  AND NOT EXISTS (SELECT 1 FROM dbo.system_schema_indexes i WHERE i.tables_recid = t.recid AND i.element_name = 'PK_system_automation_statuses');
INSERT INTO dbo.system_schema_indexes (tables_recid, element_name, element_columns, element_is_unique)
SELECT t.recid, 'UQ_system_automation_statuses_slug', 'element_slug', 1 FROM dbo.system_schema_tables t
WHERE t.element_name = 'system_automation_statuses' AND t.element_schema = 'dbo'
  AND NOT EXISTS (SELECT 1 FROM dbo.system_schema_indexes i WHERE i.tables_recid = t.recid AND i.element_name = 'UQ_system_automation_statuses_slug');
INSERT INTO dbo.system_schema_indexes (tables_recid, element_name, element_columns, element_is_unique)
SELECT t.recid, 'PK_system_trigger_types', 'recid', 1 FROM dbo.system_schema_tables t
WHERE t.element_name = 'system_trigger_types' AND t.element_schema = 'dbo'
  AND NOT EXISTS (SELECT 1 FROM dbo.system_schema_indexes i WHERE i.tables_recid = t.recid AND i.element_name = 'PK_system_trigger_types');
INSERT INTO dbo.system_schema_indexes (tables_recid, element_name, element_columns, element_is_unique)
SELECT t.recid, 'UQ_system_trigger_types_slug', 'element_slug', 1 FROM dbo.system_schema_tables t
WHERE t.element_name = 'system_trigger_types' AND t.element_schema = 'dbo'
  AND NOT EXISTS (SELECT 1 FROM dbo.system_schema_indexes i WHERE i.tables_recid = t.recid AND i.element_name = 'UQ_system_trigger_types_slug');
INSERT INTO dbo.system_schema_indexes (tables_recid, element_name, element_columns, element_is_unique)
SELECT t.recid, 'PK_system_dispositions', 'recid', 1 FROM dbo.system_schema_tables t
WHERE t.element_name = 'system_dispositions' AND t.element_schema = 'dbo'
  AND NOT EXISTS (SELECT 1 FROM dbo.system_schema_indexes i WHERE i.tables_recid = t.recid AND i.element_name = 'PK_system_dispositions');
INSERT INTO dbo.system_schema_indexes (tables_recid, element_name, element_columns, element_is_unique)
SELECT t.recid, 'UQ_system_dispositions_slug', 'element_slug', 1 FROM dbo.system_schema_tables t
WHERE t.element_name = 'system_dispositions' AND t.element_schema = 'dbo'
  AND NOT EXISTS (SELECT 1 FROM dbo.system_schema_indexes i WHERE i.tables_recid = t.recid AND i.element_name = 'UQ_system_dispositions_slug');
INSERT INTO dbo.system_schema_indexes (tables_recid, element_name, element_columns, element_is_unique)
SELECT t.recid, 'PK_system_workflow_statuses', 'recid', 1 FROM dbo.system_schema_tables t
WHERE t.element_name = 'system_workflow_statuses' AND t.element_schema = 'dbo'
  AND NOT EXISTS (SELECT 1 FROM dbo.system_schema_indexes i WHERE i.tables_recid = t.recid AND i.element_name = 'PK_system_workflow_statuses');
INSERT INTO dbo.system_schema_indexes (tables_recid, element_name, element_columns, element_is_unique)
SELECT t.recid, 'UQ_system_workflow_statuses_slug', 'element_slug', 1 FROM dbo.system_schema_tables t
WHERE t.element_name = 'system_workflow_statuses' AND t.element_schema = 'dbo'
  AND NOT EXISTS (SELECT 1 FROM dbo.system_schema_indexes i WHERE i.tables_recid = t.recid AND i.element_name = 'UQ_system_workflow_statuses_slug');
INSERT INTO dbo.system_schema_indexes (tables_recid, element_name, element_columns, element_is_unique)
SELECT t.recid, 'PK_system_scheduled_task_statuses', 'recid', 1 FROM dbo.system_schema_tables t
WHERE t.element_name = 'system_scheduled_task_statuses' AND t.element_schema = 'dbo'
  AND NOT EXISTS (SELECT 1 FROM dbo.system_schema_indexes i WHERE i.tables_recid = t.recid AND i.element_name = 'PK_system_scheduled_task_statuses');
INSERT INTO dbo.system_schema_indexes (tables_recid, element_name, element_columns, element_is_unique)
SELECT t.recid, 'UQ_system_scheduled_task_statuses_slug', 'element_slug', 1 FROM dbo.system_schema_tables t
WHERE t.element_name = 'system_scheduled_task_statuses' AND t.element_schema = 'dbo'
  AND NOT EXISTS (SELECT 1 FROM dbo.system_schema_indexes i WHERE i.tables_recid = t.recid AND i.element_name = 'UQ_system_scheduled_task_statuses_slug');
GO

/*
  Step 2: Drop deprecated tables and remove reflection metadata.
*/

IF OBJECT_ID('dbo.system_async_task_events', 'U') IS NOT NULL
  DROP TABLE dbo.system_async_task_events;
GO

IF OBJECT_ID('dbo.system_async_tasks', 'U') IS NOT NULL
  DROP TABLE dbo.system_async_tasks;
GO

IF OBJECT_ID('dbo.system_workflow_run_steps', 'U') IS NOT NULL
  DROP TABLE dbo.system_workflow_run_steps;
GO

IF OBJECT_ID('dbo.system_workflow_steps', 'U') IS NOT NULL
  DROP TABLE dbo.system_workflow_steps;
GO

IF OBJECT_ID('dbo.system_workflow_runs', 'U') IS NOT NULL
  DROP TABLE dbo.system_workflow_runs;
GO

IF OBJECT_ID('dbo.system_batch_job_history', 'U') IS NOT NULL
  DROP TABLE dbo.system_batch_job_history;
GO

IF OBJECT_ID('dbo.system_batch_jobs', 'U') IS NOT NULL
  DROP TABLE dbo.system_batch_jobs;
GO

DECLARE @drop_table_recid BIGINT;

SET @drop_table_recid = (SELECT recid FROM dbo.system_schema_tables WHERE element_name = 'system_async_task_events' AND element_schema = 'dbo');
IF @drop_table_recid IS NOT NULL
BEGIN
  DELETE FROM dbo.system_schema_foreign_keys WHERE tables_recid = @drop_table_recid;
  DELETE FROM dbo.system_schema_indexes WHERE tables_recid = @drop_table_recid;
  DELETE FROM dbo.system_schema_columns WHERE tables_recid = @drop_table_recid;
  DELETE FROM dbo.system_schema_tables WHERE recid = @drop_table_recid;
END;

SET @drop_table_recid = (SELECT recid FROM dbo.system_schema_tables WHERE element_name = 'system_async_tasks' AND element_schema = 'dbo');
IF @drop_table_recid IS NOT NULL
BEGIN
  DELETE FROM dbo.system_schema_foreign_keys WHERE tables_recid = @drop_table_recid;
  DELETE FROM dbo.system_schema_indexes WHERE tables_recid = @drop_table_recid;
  DELETE FROM dbo.system_schema_columns WHERE tables_recid = @drop_table_recid;
  DELETE FROM dbo.system_schema_tables WHERE recid = @drop_table_recid;
END;

SET @drop_table_recid = (SELECT recid FROM dbo.system_schema_tables WHERE element_name = 'system_workflow_run_steps' AND element_schema = 'dbo');
IF @drop_table_recid IS NOT NULL
BEGIN
  DELETE FROM dbo.system_schema_foreign_keys WHERE tables_recid = @drop_table_recid;
  DELETE FROM dbo.system_schema_indexes WHERE tables_recid = @drop_table_recid;
  DELETE FROM dbo.system_schema_columns WHERE tables_recid = @drop_table_recid;
  DELETE FROM dbo.system_schema_tables WHERE recid = @drop_table_recid;
END;

SET @drop_table_recid = (SELECT recid FROM dbo.system_schema_tables WHERE element_name = 'system_workflow_steps' AND element_schema = 'dbo');
IF @drop_table_recid IS NOT NULL
BEGIN
  DELETE FROM dbo.system_schema_foreign_keys WHERE tables_recid = @drop_table_recid;
  DELETE FROM dbo.system_schema_indexes WHERE tables_recid = @drop_table_recid;
  DELETE FROM dbo.system_schema_columns WHERE tables_recid = @drop_table_recid;
  DELETE FROM dbo.system_schema_tables WHERE recid = @drop_table_recid;
END;

SET @drop_table_recid = (SELECT recid FROM dbo.system_schema_tables WHERE element_name = 'system_workflow_runs' AND element_schema = 'dbo');
IF @drop_table_recid IS NOT NULL
BEGIN
  DELETE FROM dbo.system_schema_foreign_keys WHERE tables_recid = @drop_table_recid;
  DELETE FROM dbo.system_schema_indexes WHERE tables_recid = @drop_table_recid;
  DELETE FROM dbo.system_schema_columns WHERE tables_recid = @drop_table_recid;
  DELETE FROM dbo.system_schema_tables WHERE recid = @drop_table_recid;
END;

SET @drop_table_recid = (SELECT recid FROM dbo.system_schema_tables WHERE element_name = 'system_batch_job_history' AND element_schema = 'dbo');
IF @drop_table_recid IS NOT NULL
BEGIN
  DELETE FROM dbo.system_schema_foreign_keys WHERE tables_recid = @drop_table_recid;
  DELETE FROM dbo.system_schema_indexes WHERE tables_recid = @drop_table_recid;
  DELETE FROM dbo.system_schema_columns WHERE tables_recid = @drop_table_recid;
  DELETE FROM dbo.system_schema_tables WHERE recid = @drop_table_recid;
END;

SET @drop_table_recid = (SELECT recid FROM dbo.system_schema_tables WHERE element_name = 'system_batch_jobs' AND element_schema = 'dbo');
IF @drop_table_recid IS NOT NULL
BEGIN
  DELETE FROM dbo.system_schema_foreign_keys WHERE tables_recid = @drop_table_recid;
  DELETE FROM dbo.system_schema_indexes WHERE tables_recid = @drop_table_recid;
  DELETE FROM dbo.system_schema_columns WHERE tables_recid = @drop_table_recid;
  DELETE FROM dbo.system_schema_tables WHERE recid = @drop_table_recid;
END;
GO

/*
  Step 3: Alter system_workflows.
*/

IF COL_LENGTH('dbo.system_workflows', 'element_is_active') IS NULL
BEGIN
  ALTER TABLE dbo.system_workflows ADD element_is_active BIT NOT NULL CONSTRAINT DF_system_workflows_is_active DEFAULT 1;
END;
GO

IF COL_LENGTH('dbo.system_workflows', 'element_max_concurrency') IS NULL
BEGIN
  ALTER TABLE dbo.system_workflows ADD element_max_concurrency INT NULL;
END;
GO

IF COL_LENGTH('dbo.system_workflows', 'element_stall_threshold_seconds') IS NULL
BEGIN
  ALTER TABLE dbo.system_workflows ADD element_stall_threshold_seconds INT NULL;
END;
GO

DECLARE @defname NVARCHAR(256);
SELECT @defname = dc.name
FROM sys.default_constraints dc
JOIN sys.columns c ON dc.parent_object_id = c.object_id AND dc.parent_column_id = c.column_id
WHERE c.name = 'element_status' AND OBJECT_NAME(dc.parent_object_id) = 'system_workflows';

IF @defname IS NOT NULL AND @defname <> 'DF_system_workflows_status'
BEGIN
  EXEC('ALTER TABLE dbo.system_workflows DROP CONSTRAINT [' + @defname + ']');
END;
GO

IF NOT EXISTS (
  SELECT 1 FROM sys.default_constraints dc
  JOIN sys.columns c ON dc.parent_object_id = c.object_id AND dc.parent_column_id = c.column_id
  WHERE OBJECT_NAME(dc.parent_object_id) = 'system_workflows'
    AND c.name = 'element_status'
    AND dc.name = 'DF_system_workflows_status'
)
BEGIN
  ALTER TABLE dbo.system_workflows ADD CONSTRAINT DF_system_workflows_status DEFAULT 0 FOR element_status;
END;
GO

IF NOT EXISTS (SELECT 1 FROM sys.foreign_keys WHERE name = 'FK_system_workflows_statuses' AND parent_object_id = OBJECT_ID('dbo.system_workflows'))
BEGIN
  ALTER TABLE dbo.system_workflows ADD CONSTRAINT FK_system_workflows_statuses FOREIGN KEY (element_status) REFERENCES dbo.system_workflow_statuses(recid);
END;
GO

DECLARE @t_system_workflows BIGINT = (SELECT recid FROM dbo.system_schema_tables WHERE element_name = 'system_workflows' AND element_schema = 'dbo');
INSERT INTO dbo.system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_system_workflows, 5, 'element_is_active', 8, 0, '((1))', NULL, 0, 0
WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_columns WHERE tables_recid = @t_system_workflows AND element_name = 'element_is_active');
INSERT INTO dbo.system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_system_workflows, 1, 'element_max_concurrency', 9, 1, NULL, NULL, 0, 0
WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_columns WHERE tables_recid = @t_system_workflows AND element_name = 'element_max_concurrency');
INSERT INTO dbo.system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_system_workflows, 1, 'element_stall_threshold_seconds', 10, 1, NULL, NULL, 0, 0
WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_columns WHERE tables_recid = @t_system_workflows AND element_name = 'element_stall_threshold_seconds');
GO

INSERT INTO dbo.system_schema_foreign_keys (tables_recid, element_column_name, referenced_tables_recid, element_referenced_column)
SELECT s.recid, 'element_status', r.recid, 'recid'
FROM dbo.system_schema_tables s
CROSS JOIN dbo.system_schema_tables r
WHERE s.element_name = 'system_workflows' AND s.element_schema = 'dbo'
  AND r.element_name = 'system_workflow_statuses' AND r.element_schema = 'dbo'
  AND NOT EXISTS (
    SELECT 1 FROM dbo.system_schema_foreign_keys fk
    WHERE fk.tables_recid = s.recid AND fk.element_column_name = 'element_status' AND fk.referenced_tables_recid = r.recid
  );
GO

/*
  Step 4: Create new core tables and reflection metadata.
*/

IF OBJECT_ID('dbo.system_workflow_actions', 'U') IS NULL
BEGIN
  CREATE TABLE dbo.system_workflow_actions (
    element_guid UNIQUEIDENTIFIER NOT NULL CONSTRAINT DF_system_workflow_actions_guid DEFAULT NEWID(),
    workflows_guid UNIQUEIDENTIFIER NOT NULL,
    element_name NVARCHAR(128) NOT NULL,
    element_description NVARCHAR(1024) NULL,
    functions_recid BIGINT NOT NULL,
    dispositions_recid TINYINT NOT NULL CONSTRAINT DF_system_workflow_actions_disposition DEFAULT 0,
    element_sequence INT NOT NULL,
    element_is_optional BIT NOT NULL CONSTRAINT DF_system_workflow_actions_optional DEFAULT 0,
    element_is_active BIT NOT NULL CONSTRAINT DF_system_workflow_actions_active DEFAULT 1,
    element_config NVARCHAR(MAX) NULL,
    element_rollback_functions_recid BIGINT NULL,
    element_created_on DATETIMEOFFSET(7) NOT NULL CONSTRAINT DF_system_workflow_actions_created_on DEFAULT SYSUTCDATETIME(),
    element_modified_on DATETIMEOFFSET(7) NOT NULL CONSTRAINT DF_system_workflow_actions_modified_on DEFAULT SYSUTCDATETIME(),
    CONSTRAINT PK_system_workflow_actions PRIMARY KEY CLUSTERED (element_guid),
    CONSTRAINT UQ_system_workflow_actions_workflow_name UNIQUE (workflows_guid, element_name),
    CONSTRAINT UQ_system_workflow_actions_workflow_sequence UNIQUE (workflows_guid, element_sequence),
    CONSTRAINT FK_system_workflow_actions_workflows FOREIGN KEY (workflows_guid) REFERENCES dbo.system_workflows(element_guid),
    CONSTRAINT FK_system_workflow_actions_functions FOREIGN KEY (functions_recid) REFERENCES dbo.reflection_rpc_functions(recid),
    CONSTRAINT FK_system_workflow_actions_dispositions FOREIGN KEY (dispositions_recid) REFERENCES dbo.system_dispositions(recid),
    CONSTRAINT FK_system_workflow_actions_rollback_functions FOREIGN KEY (element_rollback_functions_recid) REFERENCES dbo.reflection_rpc_functions(recid)
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
    element_current_action NVARCHAR(128) NULL,
    element_action_index INT NOT NULL CONSTRAINT DF_system_workflow_runs_action_index DEFAULT 0,
    element_result NVARCHAR(MAX) NULL,
    element_error NVARCHAR(MAX) NULL,
    element_trigger_type TINYINT NOT NULL CONSTRAINT DF_system_workflow_runs_trigger_type DEFAULT 0,
    element_trigger_ref NVARCHAR(256) NULL,
    element_created_by UNIQUEIDENTIFIER NULL,
    element_started_on DATETIMEOFFSET(7) NULL,
    element_ended_on DATETIMEOFFSET(7) NULL,
    element_created_on DATETIMEOFFSET(7) NOT NULL CONSTRAINT DF_system_workflow_runs_created_on DEFAULT SYSUTCDATETIME(),
    element_modified_on DATETIMEOFFSET(7) NOT NULL CONSTRAINT DF_system_workflow_runs_modified_on DEFAULT SYSUTCDATETIME(),
    CONSTRAINT PK_system_workflow_runs PRIMARY KEY CLUSTERED (recid),
    CONSTRAINT UQ_system_workflow_runs_guid UNIQUE (element_guid),
    CONSTRAINT FK_system_workflow_runs_workflows FOREIGN KEY (workflows_guid) REFERENCES dbo.system_workflows(element_guid),
    CONSTRAINT FK_system_workflow_runs_statuses FOREIGN KEY (element_status) REFERENCES dbo.system_automation_statuses(recid),
    CONSTRAINT FK_system_workflow_runs_trigger_types FOREIGN KEY (element_trigger_type) REFERENCES dbo.system_trigger_types(recid)
  );
END;
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE object_id = OBJECT_ID('dbo.system_workflow_runs') AND name = 'IX_system_workflow_runs_status')
BEGIN
  CREATE INDEX IX_system_workflow_runs_status ON dbo.system_workflow_runs(element_status);
END;
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE object_id = OBJECT_ID('dbo.system_workflow_runs') AND name = 'IX_system_workflow_runs_workflow')
BEGIN
  CREATE INDEX IX_system_workflow_runs_workflow ON dbo.system_workflow_runs(workflows_guid);
END;
GO

IF OBJECT_ID('dbo.system_workflow_run_actions', 'U') IS NULL
BEGIN
  CREATE TABLE dbo.system_workflow_run_actions (
    recid BIGINT IDENTITY(1,1) NOT NULL,
    element_guid UNIQUEIDENTIFIER NOT NULL CONSTRAINT DF_system_workflow_run_actions_guid DEFAULT NEWID(),
    runs_recid BIGINT NOT NULL,
    actions_guid UNIQUEIDENTIFIER NOT NULL,
    element_status TINYINT NOT NULL CONSTRAINT DF_system_workflow_run_actions_status DEFAULT 0,
    element_sequence INT NOT NULL,
    element_input NVARCHAR(MAX) NULL,
    element_output NVARCHAR(MAX) NULL,
    element_error NVARCHAR(MAX) NULL,
    element_retry_count INT NOT NULL CONSTRAINT DF_system_workflow_run_actions_retry DEFAULT 0,
    element_external_ref NVARCHAR(512) NULL,
    element_poll_interval_seconds INT NULL,
    element_started_on DATETIMEOFFSET(7) NULL,
    element_ended_on DATETIMEOFFSET(7) NULL,
    element_created_on DATETIMEOFFSET(7) NOT NULL CONSTRAINT DF_system_workflow_run_actions_created_on DEFAULT SYSUTCDATETIME(),
    element_modified_on DATETIMEOFFSET(7) NOT NULL CONSTRAINT DF_system_workflow_run_actions_modified_on DEFAULT SYSUTCDATETIME(),
    CONSTRAINT PK_system_workflow_run_actions PRIMARY KEY CLUSTERED (recid),
    CONSTRAINT UQ_system_workflow_run_actions_guid UNIQUE (element_guid),
    CONSTRAINT FK_system_workflow_run_actions_runs FOREIGN KEY (runs_recid) REFERENCES dbo.system_workflow_runs(recid),
    CONSTRAINT FK_system_workflow_run_actions_actions FOREIGN KEY (actions_guid) REFERENCES dbo.system_workflow_actions(element_guid),
    CONSTRAINT FK_system_workflow_run_actions_statuses FOREIGN KEY (element_status) REFERENCES dbo.system_automation_statuses(recid)
  );
END;
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE object_id = OBJECT_ID('dbo.system_workflow_run_actions') AND name = 'IX_system_workflow_run_actions_run')
BEGIN
  CREATE INDEX IX_system_workflow_run_actions_run ON dbo.system_workflow_run_actions(runs_recid, element_created_on);
END;
GO

IF OBJECT_ID('dbo.system_scheduled_tasks', 'U') IS NULL
BEGIN
  CREATE TABLE dbo.system_scheduled_tasks (
    recid BIGINT IDENTITY(1,1) NOT NULL,
    element_name NVARCHAR(128) NOT NULL,
    element_description NVARCHAR(512) NULL,
    workflows_guid UNIQUEIDENTIFIER NOT NULL,
    element_payload_template NVARCHAR(MAX) NULL,
    element_cron NVARCHAR(64) NOT NULL,
    element_recurrence_type TINYINT NOT NULL CONSTRAINT DF_system_scheduled_tasks_recurrence DEFAULT 0,
    element_run_count_limit INT NULL,
    element_run_until DATETIMEOFFSET(7) NULL,
    element_total_runs INT NOT NULL CONSTRAINT DF_system_scheduled_tasks_total_runs DEFAULT 0,
    element_status TINYINT NOT NULL CONSTRAINT DF_system_scheduled_tasks_status DEFAULT 1,
    element_last_run DATETIMEOFFSET(7) NULL,
    element_next_run DATETIMEOFFSET(7) NULL,
    element_created_on DATETIMEOFFSET(7) NOT NULL CONSTRAINT DF_system_scheduled_tasks_created_on DEFAULT SYSUTCDATETIME(),
    element_modified_on DATETIMEOFFSET(7) NOT NULL CONSTRAINT DF_system_scheduled_tasks_modified_on DEFAULT SYSUTCDATETIME(),
    CONSTRAINT PK_system_scheduled_tasks PRIMARY KEY CLUSTERED (recid),
    CONSTRAINT UQ_system_scheduled_tasks_name UNIQUE (element_name),
    CONSTRAINT FK_system_scheduled_tasks_workflows FOREIGN KEY (workflows_guid) REFERENCES dbo.system_workflows(element_guid),
    CONSTRAINT FK_system_scheduled_tasks_statuses FOREIGN KEY (element_status) REFERENCES dbo.system_scheduled_task_statuses(recid)
  );
END;
GO

IF OBJECT_ID('dbo.system_scheduled_task_history', 'U') IS NULL
BEGIN
  CREATE TABLE dbo.system_scheduled_task_history (
    recid BIGINT IDENTITY(1,1) NOT NULL,
    tasks_recid BIGINT NOT NULL,
    runs_recid BIGINT NULL,
    element_fired_on DATETIMEOFFSET(7) NOT NULL CONSTRAINT DF_system_scheduled_task_history_fired_on DEFAULT SYSUTCDATETIME(),
    element_error NVARCHAR(MAX) NULL,
    element_created_on DATETIMEOFFSET(7) NOT NULL CONSTRAINT DF_system_scheduled_task_history_created_on DEFAULT SYSUTCDATETIME(),
    element_modified_on DATETIMEOFFSET(7) NOT NULL CONSTRAINT DF_system_scheduled_task_history_modified_on DEFAULT SYSUTCDATETIME(),
    CONSTRAINT PK_system_scheduled_task_history PRIMARY KEY CLUSTERED (recid),
    CONSTRAINT FK_system_scheduled_task_history_tasks FOREIGN KEY (tasks_recid) REFERENCES dbo.system_scheduled_tasks(recid),
    CONSTRAINT FK_system_scheduled_task_history_runs FOREIGN KEY (runs_recid) REFERENCES dbo.system_workflow_runs(recid)
  );
END;
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE object_id = OBJECT_ID('dbo.system_scheduled_task_history') AND name = 'IX_system_scheduled_task_history_tasks')
BEGIN
  CREATE INDEX IX_system_scheduled_task_history_tasks ON dbo.system_scheduled_task_history(tasks_recid);
END;
GO

INSERT INTO dbo.system_schema_tables (element_name, element_schema)
SELECT 'system_workflow_actions', 'dbo'
WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_tables WHERE element_name = 'system_workflow_actions' AND element_schema = 'dbo');
INSERT INTO dbo.system_schema_tables (element_name, element_schema)
SELECT 'system_workflow_runs', 'dbo'
WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_tables WHERE element_name = 'system_workflow_runs' AND element_schema = 'dbo');
INSERT INTO dbo.system_schema_tables (element_name, element_schema)
SELECT 'system_workflow_run_actions', 'dbo'
WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_tables WHERE element_name = 'system_workflow_run_actions' AND element_schema = 'dbo');
INSERT INTO dbo.system_schema_tables (element_name, element_schema)
SELECT 'system_scheduled_tasks', 'dbo'
WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_tables WHERE element_name = 'system_scheduled_tasks' AND element_schema = 'dbo');
INSERT INTO dbo.system_schema_tables (element_name, element_schema)
SELECT 'system_scheduled_task_history', 'dbo'
WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_tables WHERE element_name = 'system_scheduled_task_history' AND element_schema = 'dbo');
GO

DECLARE @t_system_workflow_actions BIGINT = (SELECT recid FROM dbo.system_schema_tables WHERE element_name = 'system_workflow_actions' AND element_schema = 'dbo');
INSERT INTO dbo.system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_system_workflow_actions, 4, 'element_guid', 1, 0, '(newid())', NULL, 1, 0 WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_columns WHERE tables_recid = @t_system_workflow_actions AND element_name = 'element_guid');
INSERT INTO dbo.system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_system_workflow_actions, 4, 'workflows_guid', 2, 0, NULL, NULL, 0, 0 WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_columns WHERE tables_recid = @t_system_workflow_actions AND element_name = 'workflows_guid');
INSERT INTO dbo.system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_system_workflow_actions, 8, 'element_name', 3, 0, NULL, 128, 0, 0 WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_columns WHERE tables_recid = @t_system_workflow_actions AND element_name = 'element_name');
INSERT INTO dbo.system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_system_workflow_actions, 8, 'element_description', 4, 1, NULL, 1024, 0, 0 WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_columns WHERE tables_recid = @t_system_workflow_actions AND element_name = 'element_description');
INSERT INTO dbo.system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_system_workflow_actions, 2, 'functions_recid', 5, 0, NULL, NULL, 0, 0 WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_columns WHERE tables_recid = @t_system_workflow_actions AND element_name = 'functions_recid');
INSERT INTO dbo.system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_system_workflow_actions, 11, 'dispositions_recid', 6, 0, '((0))', NULL, 0, 0 WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_columns WHERE tables_recid = @t_system_workflow_actions AND element_name = 'dispositions_recid');
INSERT INTO dbo.system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_system_workflow_actions, 1, 'element_sequence', 7, 0, NULL, NULL, 0, 0 WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_columns WHERE tables_recid = @t_system_workflow_actions AND element_name = 'element_sequence');
INSERT INTO dbo.system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_system_workflow_actions, 5, 'element_is_optional', 8, 0, '((0))', NULL, 0, 0 WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_columns WHERE tables_recid = @t_system_workflow_actions AND element_name = 'element_is_optional');
INSERT INTO dbo.system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_system_workflow_actions, 5, 'element_is_active', 9, 0, '((1))', NULL, 0, 0 WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_columns WHERE tables_recid = @t_system_workflow_actions AND element_name = 'element_is_active');
INSERT INTO dbo.system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_system_workflow_actions, 9, 'element_config', 10, 1, NULL, -1, 0, 0 WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_columns WHERE tables_recid = @t_system_workflow_actions AND element_name = 'element_config');
INSERT INTO dbo.system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_system_workflow_actions, 2, 'element_rollback_functions_recid', 11, 1, NULL, NULL, 0, 0 WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_columns WHERE tables_recid = @t_system_workflow_actions AND element_name = 'element_rollback_functions_recid');
INSERT INTO dbo.system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_system_workflow_actions, 7, 'element_created_on', 12, 0, '(sysutcdatetime())', NULL, 0, 0 WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_columns WHERE tables_recid = @t_system_workflow_actions AND element_name = 'element_created_on');
INSERT INTO dbo.system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_system_workflow_actions, 7, 'element_modified_on', 13, 0, '(sysutcdatetime())', NULL, 0, 0 WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_columns WHERE tables_recid = @t_system_workflow_actions AND element_name = 'element_modified_on');
GO

DECLARE @t_system_workflow_runs_new BIGINT = (SELECT recid FROM dbo.system_schema_tables WHERE element_name = 'system_workflow_runs' AND element_schema = 'dbo');
INSERT INTO dbo.system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_system_workflow_runs_new, 3, 'recid', 1, 0, NULL, NULL, 1, 1 WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_columns WHERE tables_recid = @t_system_workflow_runs_new AND element_name = 'recid');
INSERT INTO dbo.system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_system_workflow_runs_new, 4, 'element_guid', 2, 0, '(newid())', NULL, 0, 0 WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_columns WHERE tables_recid = @t_system_workflow_runs_new AND element_name = 'element_guid');
INSERT INTO dbo.system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_system_workflow_runs_new, 4, 'workflows_guid', 3, 0, NULL, NULL, 0, 0 WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_columns WHERE tables_recid = @t_system_workflow_runs_new AND element_name = 'workflows_guid');
INSERT INTO dbo.system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_system_workflow_runs_new, 11, 'element_status', 4, 0, '((0))', NULL, 0, 0 WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_columns WHERE tables_recid = @t_system_workflow_runs_new AND element_name = 'element_status');
INSERT INTO dbo.system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_system_workflow_runs_new, 9, 'element_payload', 5, 1, NULL, -1, 0, 0 WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_columns WHERE tables_recid = @t_system_workflow_runs_new AND element_name = 'element_payload');
INSERT INTO dbo.system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_system_workflow_runs_new, 9, 'element_context', 6, 1, NULL, -1, 0, 0 WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_columns WHERE tables_recid = @t_system_workflow_runs_new AND element_name = 'element_context');
INSERT INTO dbo.system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_system_workflow_runs_new, 8, 'element_current_action', 7, 1, NULL, 128, 0, 0 WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_columns WHERE tables_recid = @t_system_workflow_runs_new AND element_name = 'element_current_action');
INSERT INTO dbo.system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_system_workflow_runs_new, 1, 'element_action_index', 8, 0, '((0))', NULL, 0, 0 WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_columns WHERE tables_recid = @t_system_workflow_runs_new AND element_name = 'element_action_index');
INSERT INTO dbo.system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_system_workflow_runs_new, 9, 'element_result', 9, 1, NULL, -1, 0, 0 WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_columns WHERE tables_recid = @t_system_workflow_runs_new AND element_name = 'element_result');
INSERT INTO dbo.system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_system_workflow_runs_new, 9, 'element_error', 10, 1, NULL, -1, 0, 0 WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_columns WHERE tables_recid = @t_system_workflow_runs_new AND element_name = 'element_error');
INSERT INTO dbo.system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_system_workflow_runs_new, 11, 'element_trigger_type', 11, 0, '((0))', NULL, 0, 0 WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_columns WHERE tables_recid = @t_system_workflow_runs_new AND element_name = 'element_trigger_type');
INSERT INTO dbo.system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_system_workflow_runs_new, 8, 'element_trigger_ref', 12, 1, NULL, 256, 0, 0 WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_columns WHERE tables_recid = @t_system_workflow_runs_new AND element_name = 'element_trigger_ref');
INSERT INTO dbo.system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_system_workflow_runs_new, 4, 'element_created_by', 13, 1, NULL, NULL, 0, 0 WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_columns WHERE tables_recid = @t_system_workflow_runs_new AND element_name = 'element_created_by');
INSERT INTO dbo.system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_system_workflow_runs_new, 7, 'element_started_on', 14, 1, NULL, NULL, 0, 0 WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_columns WHERE tables_recid = @t_system_workflow_runs_new AND element_name = 'element_started_on');
INSERT INTO dbo.system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_system_workflow_runs_new, 7, 'element_ended_on', 15, 1, NULL, NULL, 0, 0 WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_columns WHERE tables_recid = @t_system_workflow_runs_new AND element_name = 'element_ended_on');
INSERT INTO dbo.system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_system_workflow_runs_new, 7, 'element_created_on', 16, 0, '(sysutcdatetime())', NULL, 0, 0 WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_columns WHERE tables_recid = @t_system_workflow_runs_new AND element_name = 'element_created_on');
INSERT INTO dbo.system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_system_workflow_runs_new, 7, 'element_modified_on', 17, 0, '(sysutcdatetime())', NULL, 0, 0 WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_columns WHERE tables_recid = @t_system_workflow_runs_new AND element_name = 'element_modified_on');
GO

DECLARE @t_system_workflow_run_actions BIGINT = (SELECT recid FROM dbo.system_schema_tables WHERE element_name = 'system_workflow_run_actions' AND element_schema = 'dbo');
INSERT INTO dbo.system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_system_workflow_run_actions, 3, 'recid', 1, 0, NULL, NULL, 1, 1 WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_columns WHERE tables_recid = @t_system_workflow_run_actions AND element_name = 'recid');
INSERT INTO dbo.system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_system_workflow_run_actions, 4, 'element_guid', 2, 0, '(newid())', NULL, 0, 0 WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_columns WHERE tables_recid = @t_system_workflow_run_actions AND element_name = 'element_guid');
INSERT INTO dbo.system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_system_workflow_run_actions, 2, 'runs_recid', 3, 0, NULL, NULL, 0, 0 WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_columns WHERE tables_recid = @t_system_workflow_run_actions AND element_name = 'runs_recid');
INSERT INTO dbo.system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_system_workflow_run_actions, 4, 'actions_guid', 4, 0, NULL, NULL, 0, 0 WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_columns WHERE tables_recid = @t_system_workflow_run_actions AND element_name = 'actions_guid');
INSERT INTO dbo.system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_system_workflow_run_actions, 11, 'element_status', 5, 0, '((0))', NULL, 0, 0 WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_columns WHERE tables_recid = @t_system_workflow_run_actions AND element_name = 'element_status');
INSERT INTO dbo.system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_system_workflow_run_actions, 1, 'element_sequence', 6, 0, NULL, NULL, 0, 0 WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_columns WHERE tables_recid = @t_system_workflow_run_actions AND element_name = 'element_sequence');
INSERT INTO dbo.system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_system_workflow_run_actions, 9, 'element_input', 7, 1, NULL, -1, 0, 0 WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_columns WHERE tables_recid = @t_system_workflow_run_actions AND element_name = 'element_input');
INSERT INTO dbo.system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_system_workflow_run_actions, 9, 'element_output', 8, 1, NULL, -1, 0, 0 WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_columns WHERE tables_recid = @t_system_workflow_run_actions AND element_name = 'element_output');
INSERT INTO dbo.system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_system_workflow_run_actions, 9, 'element_error', 9, 1, NULL, -1, 0, 0 WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_columns WHERE tables_recid = @t_system_workflow_run_actions AND element_name = 'element_error');
INSERT INTO dbo.system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_system_workflow_run_actions, 1, 'element_retry_count', 10, 0, '((0))', NULL, 0, 0 WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_columns WHERE tables_recid = @t_system_workflow_run_actions AND element_name = 'element_retry_count');
INSERT INTO dbo.system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_system_workflow_run_actions, 8, 'element_external_ref', 11, 1, NULL, 512, 0, 0 WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_columns WHERE tables_recid = @t_system_workflow_run_actions AND element_name = 'element_external_ref');
INSERT INTO dbo.system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_system_workflow_run_actions, 1, 'element_poll_interval_seconds', 12, 1, NULL, NULL, 0, 0 WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_columns WHERE tables_recid = @t_system_workflow_run_actions AND element_name = 'element_poll_interval_seconds');
INSERT INTO dbo.system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_system_workflow_run_actions, 7, 'element_started_on', 13, 1, NULL, NULL, 0, 0 WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_columns WHERE tables_recid = @t_system_workflow_run_actions AND element_name = 'element_started_on');
INSERT INTO dbo.system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_system_workflow_run_actions, 7, 'element_ended_on', 14, 1, NULL, NULL, 0, 0 WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_columns WHERE tables_recid = @t_system_workflow_run_actions AND element_name = 'element_ended_on');
INSERT INTO dbo.system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_system_workflow_run_actions, 7, 'element_created_on', 15, 0, '(sysutcdatetime())', NULL, 0, 0 WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_columns WHERE tables_recid = @t_system_workflow_run_actions AND element_name = 'element_created_on');
INSERT INTO dbo.system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_system_workflow_run_actions, 7, 'element_modified_on', 16, 0, '(sysutcdatetime())', NULL, 0, 0 WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_columns WHERE tables_recid = @t_system_workflow_run_actions AND element_name = 'element_modified_on');
GO

DECLARE @t_system_scheduled_tasks BIGINT = (SELECT recid FROM dbo.system_schema_tables WHERE element_name = 'system_scheduled_tasks' AND element_schema = 'dbo');
INSERT INTO dbo.system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_system_scheduled_tasks, 3, 'recid', 1, 0, NULL, NULL, 1, 1 WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_columns WHERE tables_recid = @t_system_scheduled_tasks AND element_name = 'recid');
INSERT INTO dbo.system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_system_scheduled_tasks, 8, 'element_name', 2, 0, NULL, 128, 0, 0 WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_columns WHERE tables_recid = @t_system_scheduled_tasks AND element_name = 'element_name');
INSERT INTO dbo.system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_system_scheduled_tasks, 8, 'element_description', 3, 1, NULL, 512, 0, 0 WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_columns WHERE tables_recid = @t_system_scheduled_tasks AND element_name = 'element_description');
INSERT INTO dbo.system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_system_scheduled_tasks, 4, 'workflows_guid', 4, 0, NULL, NULL, 0, 0 WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_columns WHERE tables_recid = @t_system_scheduled_tasks AND element_name = 'workflows_guid');
INSERT INTO dbo.system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_system_scheduled_tasks, 9, 'element_payload_template', 5, 1, NULL, -1, 0, 0 WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_columns WHERE tables_recid = @t_system_scheduled_tasks AND element_name = 'element_payload_template');
INSERT INTO dbo.system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_system_scheduled_tasks, 8, 'element_cron', 6, 0, NULL, 64, 0, 0 WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_columns WHERE tables_recid = @t_system_scheduled_tasks AND element_name = 'element_cron');
INSERT INTO dbo.system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_system_scheduled_tasks, 11, 'element_recurrence_type', 7, 0, '((0))', NULL, 0, 0 WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_columns WHERE tables_recid = @t_system_scheduled_tasks AND element_name = 'element_recurrence_type');
INSERT INTO dbo.system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_system_scheduled_tasks, 1, 'element_run_count_limit', 8, 1, NULL, NULL, 0, 0 WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_columns WHERE tables_recid = @t_system_scheduled_tasks AND element_name = 'element_run_count_limit');
INSERT INTO dbo.system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_system_scheduled_tasks, 7, 'element_run_until', 9, 1, NULL, NULL, 0, 0 WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_columns WHERE tables_recid = @t_system_scheduled_tasks AND element_name = 'element_run_until');
INSERT INTO dbo.system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_system_scheduled_tasks, 1, 'element_total_runs', 10, 0, '((0))', NULL, 0, 0 WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_columns WHERE tables_recid = @t_system_scheduled_tasks AND element_name = 'element_total_runs');
INSERT INTO dbo.system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_system_scheduled_tasks, 11, 'element_status', 11, 0, '((1))', NULL, 0, 0 WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_columns WHERE tables_recid = @t_system_scheduled_tasks AND element_name = 'element_status');
INSERT INTO dbo.system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_system_scheduled_tasks, 7, 'element_last_run', 12, 1, NULL, NULL, 0, 0 WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_columns WHERE tables_recid = @t_system_scheduled_tasks AND element_name = 'element_last_run');
INSERT INTO dbo.system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_system_scheduled_tasks, 7, 'element_next_run', 13, 1, NULL, NULL, 0, 0 WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_columns WHERE tables_recid = @t_system_scheduled_tasks AND element_name = 'element_next_run');
INSERT INTO dbo.system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_system_scheduled_tasks, 7, 'element_created_on', 14, 0, '(sysutcdatetime())', NULL, 0, 0 WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_columns WHERE tables_recid = @t_system_scheduled_tasks AND element_name = 'element_created_on');
INSERT INTO dbo.system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_system_scheduled_tasks, 7, 'element_modified_on', 15, 0, '(sysutcdatetime())', NULL, 0, 0 WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_columns WHERE tables_recid = @t_system_scheduled_tasks AND element_name = 'element_modified_on');
GO

DECLARE @t_system_scheduled_task_history BIGINT = (SELECT recid FROM dbo.system_schema_tables WHERE element_name = 'system_scheduled_task_history' AND element_schema = 'dbo');
INSERT INTO dbo.system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_system_scheduled_task_history, 3, 'recid', 1, 0, NULL, NULL, 1, 1 WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_columns WHERE tables_recid = @t_system_scheduled_task_history AND element_name = 'recid');
INSERT INTO dbo.system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_system_scheduled_task_history, 2, 'tasks_recid', 2, 0, NULL, NULL, 0, 0 WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_columns WHERE tables_recid = @t_system_scheduled_task_history AND element_name = 'tasks_recid');
INSERT INTO dbo.system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_system_scheduled_task_history, 2, 'runs_recid', 3, 1, NULL, NULL, 0, 0 WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_columns WHERE tables_recid = @t_system_scheduled_task_history AND element_name = 'runs_recid');
INSERT INTO dbo.system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_system_scheduled_task_history, 7, 'element_fired_on', 4, 0, '(sysutcdatetime())', NULL, 0, 0 WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_columns WHERE tables_recid = @t_system_scheduled_task_history AND element_name = 'element_fired_on');
INSERT INTO dbo.system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_system_scheduled_task_history, 9, 'element_error', 5, 1, NULL, -1, 0, 0 WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_columns WHERE tables_recid = @t_system_scheduled_task_history AND element_name = 'element_error');
INSERT INTO dbo.system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_system_scheduled_task_history, 7, 'element_created_on', 6, 0, '(sysutcdatetime())', NULL, 0, 0 WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_columns WHERE tables_recid = @t_system_scheduled_task_history AND element_name = 'element_created_on');
INSERT INTO dbo.system_schema_columns (tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
SELECT @t_system_scheduled_task_history, 7, 'element_modified_on', 7, 0, '(sysutcdatetime())', NULL, 0, 0 WHERE NOT EXISTS (SELECT 1 FROM dbo.system_schema_columns WHERE tables_recid = @t_system_scheduled_task_history AND element_name = 'element_modified_on');
GO

INSERT INTO dbo.system_schema_indexes (tables_recid, element_name, element_columns, element_is_unique)
SELECT t.recid, 'PK_system_workflow_actions', 'element_guid', 1 FROM dbo.system_schema_tables t
WHERE t.element_name = 'system_workflow_actions' AND t.element_schema = 'dbo'
  AND NOT EXISTS (SELECT 1 FROM dbo.system_schema_indexes i WHERE i.tables_recid = t.recid AND i.element_name = 'PK_system_workflow_actions');
INSERT INTO dbo.system_schema_indexes (tables_recid, element_name, element_columns, element_is_unique)
SELECT t.recid, 'UQ_system_workflow_actions_workflow_name', 'workflows_guid,element_name', 1 FROM dbo.system_schema_tables t
WHERE t.element_name = 'system_workflow_actions' AND t.element_schema = 'dbo'
  AND NOT EXISTS (SELECT 1 FROM dbo.system_schema_indexes i WHERE i.tables_recid = t.recid AND i.element_name = 'UQ_system_workflow_actions_workflow_name');
INSERT INTO dbo.system_schema_indexes (tables_recid, element_name, element_columns, element_is_unique)
SELECT t.recid, 'UQ_system_workflow_actions_workflow_sequence', 'workflows_guid,element_sequence', 1 FROM dbo.system_schema_tables t
WHERE t.element_name = 'system_workflow_actions' AND t.element_schema = 'dbo'
  AND NOT EXISTS (SELECT 1 FROM dbo.system_schema_indexes i WHERE i.tables_recid = t.recid AND i.element_name = 'UQ_system_workflow_actions_workflow_sequence');

INSERT INTO dbo.system_schema_indexes (tables_recid, element_name, element_columns, element_is_unique)
SELECT t.recid, 'PK_system_workflow_runs', 'recid', 1 FROM dbo.system_schema_tables t
WHERE t.element_name = 'system_workflow_runs' AND t.element_schema = 'dbo'
  AND NOT EXISTS (SELECT 1 FROM dbo.system_schema_indexes i WHERE i.tables_recid = t.recid AND i.element_name = 'PK_system_workflow_runs');
INSERT INTO dbo.system_schema_indexes (tables_recid, element_name, element_columns, element_is_unique)
SELECT t.recid, 'UQ_system_workflow_runs_guid', 'element_guid', 1 FROM dbo.system_schema_tables t
WHERE t.element_name = 'system_workflow_runs' AND t.element_schema = 'dbo'
  AND NOT EXISTS (SELECT 1 FROM dbo.system_schema_indexes i WHERE i.tables_recid = t.recid AND i.element_name = 'UQ_system_workflow_runs_guid');
INSERT INTO dbo.system_schema_indexes (tables_recid, element_name, element_columns, element_is_unique)
SELECT t.recid, 'IX_system_workflow_runs_status', 'element_status', 0 FROM dbo.system_schema_tables t
WHERE t.element_name = 'system_workflow_runs' AND t.element_schema = 'dbo'
  AND NOT EXISTS (SELECT 1 FROM dbo.system_schema_indexes i WHERE i.tables_recid = t.recid AND i.element_name = 'IX_system_workflow_runs_status');
INSERT INTO dbo.system_schema_indexes (tables_recid, element_name, element_columns, element_is_unique)
SELECT t.recid, 'IX_system_workflow_runs_workflow', 'workflows_guid', 0 FROM dbo.system_schema_tables t
WHERE t.element_name = 'system_workflow_runs' AND t.element_schema = 'dbo'
  AND NOT EXISTS (SELECT 1 FROM dbo.system_schema_indexes i WHERE i.tables_recid = t.recid AND i.element_name = 'IX_system_workflow_runs_workflow');

INSERT INTO dbo.system_schema_indexes (tables_recid, element_name, element_columns, element_is_unique)
SELECT t.recid, 'PK_system_workflow_run_actions', 'recid', 1 FROM dbo.system_schema_tables t
WHERE t.element_name = 'system_workflow_run_actions' AND t.element_schema = 'dbo'
  AND NOT EXISTS (SELECT 1 FROM dbo.system_schema_indexes i WHERE i.tables_recid = t.recid AND i.element_name = 'PK_system_workflow_run_actions');
INSERT INTO dbo.system_schema_indexes (tables_recid, element_name, element_columns, element_is_unique)
SELECT t.recid, 'UQ_system_workflow_run_actions_guid', 'element_guid', 1 FROM dbo.system_schema_tables t
WHERE t.element_name = 'system_workflow_run_actions' AND t.element_schema = 'dbo'
  AND NOT EXISTS (SELECT 1 FROM dbo.system_schema_indexes i WHERE i.tables_recid = t.recid AND i.element_name = 'UQ_system_workflow_run_actions_guid');
INSERT INTO dbo.system_schema_indexes (tables_recid, element_name, element_columns, element_is_unique)
SELECT t.recid, 'IX_system_workflow_run_actions_run', 'runs_recid,element_created_on', 0 FROM dbo.system_schema_tables t
WHERE t.element_name = 'system_workflow_run_actions' AND t.element_schema = 'dbo'
  AND NOT EXISTS (SELECT 1 FROM dbo.system_schema_indexes i WHERE i.tables_recid = t.recid AND i.element_name = 'IX_system_workflow_run_actions_run');

INSERT INTO dbo.system_schema_indexes (tables_recid, element_name, element_columns, element_is_unique)
SELECT t.recid, 'PK_system_scheduled_tasks', 'recid', 1 FROM dbo.system_schema_tables t
WHERE t.element_name = 'system_scheduled_tasks' AND t.element_schema = 'dbo'
  AND NOT EXISTS (SELECT 1 FROM dbo.system_schema_indexes i WHERE i.tables_recid = t.recid AND i.element_name = 'PK_system_scheduled_tasks');
INSERT INTO dbo.system_schema_indexes (tables_recid, element_name, element_columns, element_is_unique)
SELECT t.recid, 'UQ_system_scheduled_tasks_name', 'element_name', 1 FROM dbo.system_schema_tables t
WHERE t.element_name = 'system_scheduled_tasks' AND t.element_schema = 'dbo'
  AND NOT EXISTS (SELECT 1 FROM dbo.system_schema_indexes i WHERE i.tables_recid = t.recid AND i.element_name = 'UQ_system_scheduled_tasks_name');

INSERT INTO dbo.system_schema_indexes (tables_recid, element_name, element_columns, element_is_unique)
SELECT t.recid, 'PK_system_scheduled_task_history', 'recid', 1 FROM dbo.system_schema_tables t
WHERE t.element_name = 'system_scheduled_task_history' AND t.element_schema = 'dbo'
  AND NOT EXISTS (SELECT 1 FROM dbo.system_schema_indexes i WHERE i.tables_recid = t.recid AND i.element_name = 'PK_system_scheduled_task_history');
INSERT INTO dbo.system_schema_indexes (tables_recid, element_name, element_columns, element_is_unique)
SELECT t.recid, 'IX_system_scheduled_task_history_tasks', 'tasks_recid', 0 FROM dbo.system_schema_tables t
WHERE t.element_name = 'system_scheduled_task_history' AND t.element_schema = 'dbo'
  AND NOT EXISTS (SELECT 1 FROM dbo.system_schema_indexes i WHERE i.tables_recid = t.recid AND i.element_name = 'IX_system_scheduled_task_history_tasks');
GO

INSERT INTO dbo.system_schema_foreign_keys (tables_recid, element_column_name, referenced_tables_recid, element_referenced_column)
SELECT s.recid, 'workflows_guid', r.recid, 'element_guid'
FROM dbo.system_schema_tables s CROSS JOIN dbo.system_schema_tables r
WHERE s.element_name = 'system_workflow_actions' AND s.element_schema = 'dbo'
  AND r.element_name = 'system_workflows' AND r.element_schema = 'dbo'
  AND NOT EXISTS (SELECT 1 FROM dbo.system_schema_foreign_keys fk WHERE fk.tables_recid = s.recid AND fk.element_column_name = 'workflows_guid');
INSERT INTO dbo.system_schema_foreign_keys (tables_recid, element_column_name, referenced_tables_recid, element_referenced_column)
SELECT s.recid, 'functions_recid', r.recid, 'recid'
FROM dbo.system_schema_tables s CROSS JOIN dbo.system_schema_tables r
WHERE s.element_name = 'system_workflow_actions' AND s.element_schema = 'dbo'
  AND r.element_name = 'reflection_rpc_functions' AND r.element_schema = 'dbo'
  AND NOT EXISTS (SELECT 1 FROM dbo.system_schema_foreign_keys fk WHERE fk.tables_recid = s.recid AND fk.element_column_name = 'functions_recid');
INSERT INTO dbo.system_schema_foreign_keys (tables_recid, element_column_name, referenced_tables_recid, element_referenced_column)
SELECT s.recid, 'dispositions_recid', r.recid, 'recid'
FROM dbo.system_schema_tables s CROSS JOIN dbo.system_schema_tables r
WHERE s.element_name = 'system_workflow_actions' AND s.element_schema = 'dbo'
  AND r.element_name = 'system_dispositions' AND r.element_schema = 'dbo'
  AND NOT EXISTS (SELECT 1 FROM dbo.system_schema_foreign_keys fk WHERE fk.tables_recid = s.recid AND fk.element_column_name = 'dispositions_recid');
INSERT INTO dbo.system_schema_foreign_keys (tables_recid, element_column_name, referenced_tables_recid, element_referenced_column)
SELECT s.recid, 'element_rollback_functions_recid', r.recid, 'recid'
FROM dbo.system_schema_tables s CROSS JOIN dbo.system_schema_tables r
WHERE s.element_name = 'system_workflow_actions' AND s.element_schema = 'dbo'
  AND r.element_name = 'reflection_rpc_functions' AND r.element_schema = 'dbo'
  AND NOT EXISTS (SELECT 1 FROM dbo.system_schema_foreign_keys fk WHERE fk.tables_recid = s.recid AND fk.element_column_name = 'element_rollback_functions_recid');

INSERT INTO dbo.system_schema_foreign_keys (tables_recid, element_column_name, referenced_tables_recid, element_referenced_column)
SELECT s.recid, 'workflows_guid', r.recid, 'element_guid'
FROM dbo.system_schema_tables s CROSS JOIN dbo.system_schema_tables r
WHERE s.element_name = 'system_workflow_runs' AND s.element_schema = 'dbo'
  AND r.element_name = 'system_workflows' AND r.element_schema = 'dbo'
  AND NOT EXISTS (SELECT 1 FROM dbo.system_schema_foreign_keys fk WHERE fk.tables_recid = s.recid AND fk.element_column_name = 'workflows_guid');
INSERT INTO dbo.system_schema_foreign_keys (tables_recid, element_column_name, referenced_tables_recid, element_referenced_column)
SELECT s.recid, 'element_status', r.recid, 'recid'
FROM dbo.system_schema_tables s CROSS JOIN dbo.system_schema_tables r
WHERE s.element_name = 'system_workflow_runs' AND s.element_schema = 'dbo'
  AND r.element_name = 'system_automation_statuses' AND r.element_schema = 'dbo'
  AND NOT EXISTS (SELECT 1 FROM dbo.system_schema_foreign_keys fk WHERE fk.tables_recid = s.recid AND fk.element_column_name = 'element_status' AND fk.referenced_tables_recid = r.recid);
INSERT INTO dbo.system_schema_foreign_keys (tables_recid, element_column_name, referenced_tables_recid, element_referenced_column)
SELECT s.recid, 'element_trigger_type', r.recid, 'recid'
FROM dbo.system_schema_tables s CROSS JOIN dbo.system_schema_tables r
WHERE s.element_name = 'system_workflow_runs' AND s.element_schema = 'dbo'
  AND r.element_name = 'system_trigger_types' AND r.element_schema = 'dbo'
  AND NOT EXISTS (SELECT 1 FROM dbo.system_schema_foreign_keys fk WHERE fk.tables_recid = s.recid AND fk.element_column_name = 'element_trigger_type');

INSERT INTO dbo.system_schema_foreign_keys (tables_recid, element_column_name, referenced_tables_recid, element_referenced_column)
SELECT s.recid, 'runs_recid', r.recid, 'recid'
FROM dbo.system_schema_tables s CROSS JOIN dbo.system_schema_tables r
WHERE s.element_name = 'system_workflow_run_actions' AND s.element_schema = 'dbo'
  AND r.element_name = 'system_workflow_runs' AND r.element_schema = 'dbo'
  AND NOT EXISTS (SELECT 1 FROM dbo.system_schema_foreign_keys fk WHERE fk.tables_recid = s.recid AND fk.element_column_name = 'runs_recid');
INSERT INTO dbo.system_schema_foreign_keys (tables_recid, element_column_name, referenced_tables_recid, element_referenced_column)
SELECT s.recid, 'actions_guid', r.recid, 'element_guid'
FROM dbo.system_schema_tables s CROSS JOIN dbo.system_schema_tables r
WHERE s.element_name = 'system_workflow_run_actions' AND s.element_schema = 'dbo'
  AND r.element_name = 'system_workflow_actions' AND r.element_schema = 'dbo'
  AND NOT EXISTS (SELECT 1 FROM dbo.system_schema_foreign_keys fk WHERE fk.tables_recid = s.recid AND fk.element_column_name = 'actions_guid');
INSERT INTO dbo.system_schema_foreign_keys (tables_recid, element_column_name, referenced_tables_recid, element_referenced_column)
SELECT s.recid, 'element_status', r.recid, 'recid'
FROM dbo.system_schema_tables s CROSS JOIN dbo.system_schema_tables r
WHERE s.element_name = 'system_workflow_run_actions' AND s.element_schema = 'dbo'
  AND r.element_name = 'system_automation_statuses' AND r.element_schema = 'dbo'
  AND NOT EXISTS (SELECT 1 FROM dbo.system_schema_foreign_keys fk WHERE fk.tables_recid = s.recid AND fk.element_column_name = 'element_status' AND fk.referenced_tables_recid = r.recid);

INSERT INTO dbo.system_schema_foreign_keys (tables_recid, element_column_name, referenced_tables_recid, element_referenced_column)
SELECT s.recid, 'workflows_guid', r.recid, 'element_guid'
FROM dbo.system_schema_tables s CROSS JOIN dbo.system_schema_tables r
WHERE s.element_name = 'system_scheduled_tasks' AND s.element_schema = 'dbo'
  AND r.element_name = 'system_workflows' AND r.element_schema = 'dbo'
  AND NOT EXISTS (SELECT 1 FROM dbo.system_schema_foreign_keys fk WHERE fk.tables_recid = s.recid AND fk.element_column_name = 'workflows_guid');
INSERT INTO dbo.system_schema_foreign_keys (tables_recid, element_column_name, referenced_tables_recid, element_referenced_column)
SELECT s.recid, 'element_status', r.recid, 'recid'
FROM dbo.system_schema_tables s CROSS JOIN dbo.system_schema_tables r
WHERE s.element_name = 'system_scheduled_tasks' AND s.element_schema = 'dbo'
  AND r.element_name = 'system_scheduled_task_statuses' AND r.element_schema = 'dbo'
  AND NOT EXISTS (SELECT 1 FROM dbo.system_schema_foreign_keys fk WHERE fk.tables_recid = s.recid AND fk.element_column_name = 'element_status' AND fk.referenced_tables_recid = r.recid);

INSERT INTO dbo.system_schema_foreign_keys (tables_recid, element_column_name, referenced_tables_recid, element_referenced_column)
SELECT s.recid, 'tasks_recid', r.recid, 'recid'
FROM dbo.system_schema_tables s CROSS JOIN dbo.system_schema_tables r
WHERE s.element_name = 'system_scheduled_task_history' AND s.element_schema = 'dbo'
  AND r.element_name = 'system_scheduled_tasks' AND r.element_schema = 'dbo'
  AND NOT EXISTS (SELECT 1 FROM dbo.system_schema_foreign_keys fk WHERE fk.tables_recid = s.recid AND fk.element_column_name = 'tasks_recid');
INSERT INTO dbo.system_schema_foreign_keys (tables_recid, element_column_name, referenced_tables_recid, element_referenced_column)
SELECT s.recid, 'runs_recid', r.recid, 'recid'
FROM dbo.system_schema_tables s CROSS JOIN dbo.system_schema_tables r
WHERE s.element_name = 'system_scheduled_task_history' AND s.element_schema = 'dbo'
  AND r.element_name = 'system_workflow_runs' AND r.element_schema = 'dbo'
  AND NOT EXISTS (SELECT 1 FROM dbo.system_schema_foreign_keys fk WHERE fk.tables_recid = s.recid AND fk.element_column_name = 'runs_recid');
GO

/*
  Step 5: Seed workflows and scheduled tasks.
*/

INSERT INTO dbo.system_workflows (element_guid, element_name, element_description, element_version, element_status, element_is_active, element_max_concurrency, element_stall_threshold_seconds)
SELECT 'C1D2E3F4-A5B6-7890-CDEF-123456789010', 'storage_reindex', 'Scan Azure Blob Storage and synchronize the users_storage_cache table.', 1, 1, 1, 1, 3600
WHERE NOT EXISTS (SELECT 1 FROM dbo.system_workflows WHERE element_guid = 'C1D2E3F4-A5B6-7890-CDEF-123456789010');
GO

INSERT INTO dbo.system_workflows (element_guid, element_name, element_description, element_version, element_status, element_is_active, element_max_concurrency, element_stall_threshold_seconds)
SELECT 'D1E2F3A4-B5C6-7890-DEFA-123456789020', 'stall_monitor', 'Scan for Workflow Runs stuck in running or waiting status longer than their stall threshold and transition them to stalled.', 1, 1, 1, 1, 300
WHERE NOT EXISTS (SELECT 1 FROM dbo.system_workflows WHERE element_guid = 'D1E2F3A4-B5C6-7890-DEFA-123456789020');
GO

INSERT INTO dbo.system_scheduled_tasks (element_name, element_description, workflows_guid, element_cron, element_recurrence_type, element_status)
SELECT 'Storage Reindex', 'Periodically scan Azure Blob Storage and synchronize the users_storage_cache table.', 'C1D2E3F4-A5B6-7890-CDEF-123456789010', '0 */12 * * *', 1, 1
WHERE NOT EXISTS (SELECT 1 FROM dbo.system_scheduled_tasks WHERE element_name = 'Storage Reindex');
GO

INSERT INTO dbo.system_scheduled_tasks (element_name, element_description, workflows_guid, element_cron, element_recurrence_type, element_status)
SELECT 'Stall Monitor', 'Periodically scan for stalled Workflow Runs and flag them.', 'D1E2F3A4-B5C6-7890-DEFA-123456789020', '*/5 * * * *', 1, 1
WHERE NOT EXISTS (SELECT 1 FROM dbo.system_scheduled_tasks WHERE element_name = 'Stall Monitor');
GO

UPDATE dbo.system_workflows
SET element_max_concurrency = NULL,
    element_stall_threshold_seconds = 300
WHERE element_name = 'persona_conversation';
GO

UPDATE dbo.system_workflows
SET element_max_concurrency = 1,
    element_stall_threshold_seconds = 1800
WHERE element_name = 'billing_import';
GO
