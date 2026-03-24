CREATE TABLE [dbo].[system_batch_jobs] (
  [recid]                   BIGINT IDENTITY(1,1) NOT NULL,
  [element_name]            NVARCHAR(128) NOT NULL,
  [element_description]     NVARCHAR(512) NULL,
  [element_class]           NVARCHAR(256) NOT NULL,
  [element_parameters]      NVARCHAR(MAX) NULL,
  [element_cron]            NVARCHAR(64) NOT NULL,
  [element_recurrence_type] TINYINT NOT NULL DEFAULT (0),
  [element_run_count_limit] INT NULL,
  [element_run_until]       DATETIMEOFFSET(7) NULL,
  [element_total_runs]      INT NOT NULL DEFAULT (0),
  [element_is_enabled]      BIT NOT NULL DEFAULT (1),
  [element_last_run]        DATETIMEOFFSET(7) NULL,
  [element_next_run]        DATETIMEOFFSET(7) NULL,
  [element_status]          TINYINT NOT NULL DEFAULT (0),
  [element_created_on]      DATETIMEOFFSET(7) NOT NULL DEFAULT (SYSUTCDATETIME()),
  [element_modified_on]     DATETIMEOFFSET(7) NOT NULL DEFAULT (SYSUTCDATETIME()),
  CONSTRAINT [PK_system_batch_jobs] PRIMARY KEY ([recid])
);
CREATE UNIQUE INDEX [UQ_system_batch_jobs_name] ON [dbo].[system_batch_jobs] ([element_name]);

CREATE TABLE [dbo].[system_batch_job_history] (
  [recid]               BIGINT IDENTITY(1,1) NOT NULL,
  [jobs_recid]          BIGINT NOT NULL,
  [element_started_on]  DATETIMEOFFSET(7) NOT NULL DEFAULT (SYSUTCDATETIME()),
  [element_ended_on]    DATETIMEOFFSET(7) NULL,
  [element_status]      TINYINT NOT NULL DEFAULT (1),
  [element_error]       NVARCHAR(MAX) NULL,
  [element_result]      NVARCHAR(MAX) NULL,
  [element_created_on]  DATETIMEOFFSET(7) NOT NULL DEFAULT (SYSUTCDATETIME()),
  CONSTRAINT [PK_system_batch_job_history] PRIMARY KEY ([recid]),
  CONSTRAINT [FK_batch_job_history_jobs] FOREIGN KEY ([jobs_recid])
    REFERENCES [dbo].[system_batch_jobs] ([recid])
);
CREATE INDEX [IX_batch_job_history_jobs_recid] ON [dbo].[system_batch_job_history] ([jobs_recid]);

-- ============================================================
-- Schema reflection metadata for batch job tables
-- ============================================================

INSERT INTO system_schema_tables (element_name, element_schema) VALUES
  ('system_batch_jobs', 'dbo'),
  ('system_batch_job_history', 'dbo');

-- system_batch_jobs columns
INSERT INTO system_schema_columns (
  tables_recid, edt_recid, element_name, element_ordinal, element_nullable,
  element_default, element_max_length, element_is_primary_key, element_is_identity
) VALUES
  ((SELECT recid FROM system_schema_tables WHERE element_name = 'system_batch_jobs' AND element_schema = 'dbo'), (SELECT recid FROM system_edt_mappings WHERE element_name = 'INT64_IDENTITY'), 'recid', 1, 0, NULL, NULL, 1, 1),
  ((SELECT recid FROM system_schema_tables WHERE element_name = 'system_batch_jobs' AND element_schema = 'dbo'), (SELECT recid FROM system_edt_mappings WHERE element_name = 'STRING'), 'element_name', 2, 0, NULL, 128, 0, 0),
  ((SELECT recid FROM system_schema_tables WHERE element_name = 'system_batch_jobs' AND element_schema = 'dbo'), (SELECT recid FROM system_edt_mappings WHERE element_name = 'STRING'), 'element_description', 3, 1, NULL, 512, 0, 0),
  ((SELECT recid FROM system_schema_tables WHERE element_name = 'system_batch_jobs' AND element_schema = 'dbo'), (SELECT recid FROM system_edt_mappings WHERE element_name = 'STRING'), 'element_class', 4, 0, NULL, 256, 0, 0),
  ((SELECT recid FROM system_schema_tables WHERE element_name = 'system_batch_jobs' AND element_schema = 'dbo'), (SELECT recid FROM system_edt_mappings WHERE element_name = 'TEXT'), 'element_parameters', 5, 1, NULL, NULL, 0, 0),
  ((SELECT recid FROM system_schema_tables WHERE element_name = 'system_batch_jobs' AND element_schema = 'dbo'), (SELECT recid FROM system_edt_mappings WHERE element_name = 'STRING'), 'element_cron', 6, 0, NULL, 64, 0, 0),
  ((SELECT recid FROM system_schema_tables WHERE element_name = 'system_batch_jobs' AND element_schema = 'dbo'), (SELECT recid FROM system_edt_mappings WHERE element_name = 'INT8'), 'element_recurrence_type', 7, 0, '((0))', NULL, 0, 0),
  ((SELECT recid FROM system_schema_tables WHERE element_name = 'system_batch_jobs' AND element_schema = 'dbo'), (SELECT recid FROM system_edt_mappings WHERE element_name = 'INT32'), 'element_run_count_limit', 8, 1, NULL, NULL, 0, 0),
  ((SELECT recid FROM system_schema_tables WHERE element_name = 'system_batch_jobs' AND element_schema = 'dbo'), (SELECT recid FROM system_edt_mappings WHERE element_name = 'DATETIME_TZ'), 'element_run_until', 9, 1, NULL, NULL, 0, 0),
  ((SELECT recid FROM system_schema_tables WHERE element_name = 'system_batch_jobs' AND element_schema = 'dbo'), (SELECT recid FROM system_edt_mappings WHERE element_name = 'INT32'), 'element_total_runs', 10, 0, '((0))', NULL, 0, 0),
  ((SELECT recid FROM system_schema_tables WHERE element_name = 'system_batch_jobs' AND element_schema = 'dbo'), (SELECT recid FROM system_edt_mappings WHERE element_name = 'BOOL'), 'element_is_enabled', 11, 0, '((1))', NULL, 0, 0),
  ((SELECT recid FROM system_schema_tables WHERE element_name = 'system_batch_jobs' AND element_schema = 'dbo'), (SELECT recid FROM system_edt_mappings WHERE element_name = 'DATETIME_TZ'), 'element_last_run', 12, 1, NULL, NULL, 0, 0),
  ((SELECT recid FROM system_schema_tables WHERE element_name = 'system_batch_jobs' AND element_schema = 'dbo'), (SELECT recid FROM system_edt_mappings WHERE element_name = 'DATETIME_TZ'), 'element_next_run', 13, 1, NULL, NULL, 0, 0),
  ((SELECT recid FROM system_schema_tables WHERE element_name = 'system_batch_jobs' AND element_schema = 'dbo'), (SELECT recid FROM system_edt_mappings WHERE element_name = 'INT8'), 'element_status', 14, 0, '((0))', NULL, 0, 0),
  ((SELECT recid FROM system_schema_tables WHERE element_name = 'system_batch_jobs' AND element_schema = 'dbo'), (SELECT recid FROM system_edt_mappings WHERE element_name = 'DATETIME_TZ'), 'element_created_on', 15, 0, '(sysutcdatetime())', NULL, 0, 0),
  ((SELECT recid FROM system_schema_tables WHERE element_name = 'system_batch_jobs' AND element_schema = 'dbo'), (SELECT recid FROM system_edt_mappings WHERE element_name = 'DATETIME_TZ'), 'element_modified_on', 16, 0, '(sysutcdatetime())', NULL, 0, 0);

-- system_batch_job_history columns
INSERT INTO system_schema_columns (
  tables_recid, edt_recid, element_name, element_ordinal, element_nullable,
  element_default, element_max_length, element_is_primary_key, element_is_identity
) VALUES
  ((SELECT recid FROM system_schema_tables WHERE element_name = 'system_batch_job_history' AND element_schema = 'dbo'), (SELECT recid FROM system_edt_mappings WHERE element_name = 'INT64_IDENTITY'), 'recid', 1, 0, NULL, NULL, 1, 1),
  ((SELECT recid FROM system_schema_tables WHERE element_name = 'system_batch_job_history' AND element_schema = 'dbo'), (SELECT recid FROM system_edt_mappings WHERE element_name = 'INT64'), 'jobs_recid', 2, 0, NULL, NULL, 0, 0),
  ((SELECT recid FROM system_schema_tables WHERE element_name = 'system_batch_job_history' AND element_schema = 'dbo'), (SELECT recid FROM system_edt_mappings WHERE element_name = 'DATETIME_TZ'), 'element_started_on', 3, 0, '(sysutcdatetime())', NULL, 0, 0),
  ((SELECT recid FROM system_schema_tables WHERE element_name = 'system_batch_job_history' AND element_schema = 'dbo'), (SELECT recid FROM system_edt_mappings WHERE element_name = 'DATETIME_TZ'), 'element_ended_on', 4, 1, NULL, NULL, 0, 0),
  ((SELECT recid FROM system_schema_tables WHERE element_name = 'system_batch_job_history' AND element_schema = 'dbo'), (SELECT recid FROM system_edt_mappings WHERE element_name = 'INT8'), 'element_status', 5, 0, '((1))', NULL, 0, 0),
  ((SELECT recid FROM system_schema_tables WHERE element_name = 'system_batch_job_history' AND element_schema = 'dbo'), (SELECT recid FROM system_edt_mappings WHERE element_name = 'TEXT'), 'element_error', 6, 1, NULL, NULL, 0, 0),
  ((SELECT recid FROM system_schema_tables WHERE element_name = 'system_batch_job_history' AND element_schema = 'dbo'), (SELECT recid FROM system_edt_mappings WHERE element_name = 'TEXT'), 'element_result', 7, 1, NULL, NULL, 0, 0),
  ((SELECT recid FROM system_schema_tables WHERE element_name = 'system_batch_job_history' AND element_schema = 'dbo'), (SELECT recid FROM system_edt_mappings WHERE element_name = 'DATETIME_TZ'), 'element_created_on', 8, 0, '(sysutcdatetime())', NULL, 0, 0);

-- system_batch_jobs indexes
INSERT INTO system_schema_indexes (tables_recid, element_name, element_columns, element_is_unique) VALUES
  ((SELECT recid FROM system_schema_tables WHERE element_name = 'system_batch_jobs' AND element_schema = 'dbo'), 'UQ_system_batch_jobs_name', 'element_name', 1);

-- system_batch_job_history indexes
INSERT INTO system_schema_indexes (tables_recid, element_name, element_columns, element_is_unique) VALUES
  ((SELECT recid FROM system_schema_tables WHERE element_name = 'system_batch_job_history' AND element_schema = 'dbo'), 'IX_batch_job_history_jobs_recid', 'jobs_recid', 0);

-- system_batch_job_history foreign keys
INSERT INTO system_schema_foreign_keys (tables_recid, element_column_name, referenced_tables_recid, element_referenced_column) VALUES
  ((SELECT recid FROM system_schema_tables WHERE element_name = 'system_batch_job_history' AND element_schema = 'dbo'), 'jobs_recid', (SELECT recid FROM system_schema_tables WHERE element_name = 'system_batch_jobs' AND element_schema = 'dbo'), 'recid');

-- ============================================================
-- Navigation route for Batch Jobs page
-- ============================================================

INSERT INTO [dbo].[frontend_routes] (
    [element_enablement],
    [element_roles],
    [element_sequence],
    [element_path],
    [element_name],
    [element_icon]
) VALUES (
    '0',
    2305843009213693952,
    1820,
    '/system-batch-jobs',
    'Batch Jobs',
    'schedule'
);

-- ============================================================
-- Seed: Storage Reindex batch job
-- ============================================================

INSERT INTO [dbo].[system_batch_jobs] (
    [element_name],
    [element_description],
    [element_class],
    [element_parameters],
    [element_cron],
    [element_recurrence_type],
    [element_is_enabled],
    [element_status]
) VALUES (
    'Storage Reindex',
    'Periodically scan Azure Blob Storage and synchronize the users_storage_cache table.',
    'server.jobs.storage_reindex.run',
    NULL,
    '0 */12 * * *',
    1,
    1,
    0
);
