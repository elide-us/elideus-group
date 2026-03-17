CREATE TABLE [dbo].[system_async_tasks] (
  [recid] BIGINT IDENTITY(1,1) NOT NULL,
  [element_guid] UNIQUEIDENTIFIER NOT NULL DEFAULT (NEWID()),
  [element_handler_type] NVARCHAR(20) NOT NULL,
  [element_handler_name] NVARCHAR(256) NOT NULL,
  [element_payload] NVARCHAR(MAX) NULL,
  [element_status] TINYINT NOT NULL DEFAULT (0),
  [element_result] NVARCHAR(MAX) NULL,
  [element_error] NVARCHAR(MAX) NULL,
  [element_current_step] NVARCHAR(128) NULL,
  [element_step_index] INT NOT NULL DEFAULT (0),
  [element_max_retries] INT NOT NULL DEFAULT (0),
  [element_retry_count] INT NOT NULL DEFAULT (0),
  [element_poll_interval_seconds] INT NULL,
  [element_timeout_seconds] INT NULL,
  [element_timeout_at] DATETIMEOFFSET(7) NULL,
  [element_external_id] NVARCHAR(512) NULL,
  [element_source_type] NVARCHAR(64) NULL,
  [element_source_id] NVARCHAR(256) NULL,
  [element_created_by] UNIQUEIDENTIFIER NULL,
  [element_created_on] DATETIMEOFFSET(7) NOT NULL DEFAULT (SYSUTCDATETIME()),
  [element_modified_on] DATETIMEOFFSET(7) NOT NULL DEFAULT (SYSUTCDATETIME()),
  CONSTRAINT [PK_system_async_tasks] PRIMARY KEY ([recid])
);

CREATE UNIQUE INDEX [UQ_system_async_tasks_guid] ON [dbo].[system_async_tasks] ([element_guid]);
CREATE INDEX [IX_system_async_tasks_status_handler_type] ON [dbo].[system_async_tasks] ([element_status], [element_handler_type]);

CREATE TABLE [dbo].[system_async_task_events] (
  [recid] BIGINT IDENTITY(1,1) NOT NULL,
  [tasks_recid] BIGINT NOT NULL,
  [element_event_type] NVARCHAR(64) NOT NULL,
  [element_step_name] NVARCHAR(128) NULL,
  [element_detail] NVARCHAR(MAX) NULL,
  [element_created_on] DATETIMEOFFSET(7) NOT NULL DEFAULT (SYSUTCDATETIME()),
  CONSTRAINT [PK_system_async_task_events] PRIMARY KEY ([recid]),
  CONSTRAINT [FK_system_async_task_events_tasks] FOREIGN KEY ([tasks_recid])
    REFERENCES [dbo].[system_async_tasks] ([recid])
);

CREATE INDEX [IX_system_async_task_events_tasks_created_on]
  ON [dbo].[system_async_task_events] ([tasks_recid], [element_created_on]);

-- Reflection metadata registration (table + column + index + foreign key)
INSERT INTO system_schema_tables (element_name, element_schema)
SELECT v.element_name, v.element_schema
FROM (VALUES
  ('system_async_tasks', 'dbo'),
  ('system_async_task_events', 'dbo')
) v(element_name, element_schema)
WHERE NOT EXISTS (
  SELECT 1 FROM system_schema_tables t
  WHERE t.element_name = v.element_name AND t.element_schema = v.element_schema
);

DELETE c
FROM system_schema_columns c
INNER JOIN system_schema_tables t ON t.recid = c.tables_recid
WHERE t.element_schema = 'dbo'
  AND t.element_name IN ('system_async_tasks', 'system_async_task_events');

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
SELECT
  st.recid,
  COALESCE(edt_exact.recid, edt_base.recid) AS edt_recid,
  c.COLUMN_NAME,
  c.ORDINAL_POSITION,
  CASE WHEN c.IS_NULLABLE = 'YES' THEN 1 ELSE 0 END,
  c.COLUMN_DEFAULT,
  CASE WHEN c.CHARACTER_MAXIMUM_LENGTH < 0 THEN NULL ELSE c.CHARACTER_MAXIMUM_LENGTH END,
  CASE WHEN pk.COLUMN_NAME IS NULL THEN 0 ELSE 1 END,
  CASE WHEN ic.COLUMN_NAME IS NULL THEN 0 ELSE 1 END
FROM INFORMATION_SCHEMA.COLUMNS c
INNER JOIN system_schema_tables st
  ON st.element_schema = c.TABLE_SCHEMA
 AND st.element_name = c.TABLE_NAME
LEFT JOIN INFORMATION_SCHEMA.KEY_COLUMN_USAGE pk
  ON pk.TABLE_SCHEMA = c.TABLE_SCHEMA
 AND pk.TABLE_NAME = c.TABLE_NAME
 AND pk.COLUMN_NAME = c.COLUMN_NAME
 AND pk.CONSTRAINT_NAME LIKE 'PK_%'
LEFT JOIN (
  SELECT TABLE_SCHEMA, TABLE_NAME, COLUMN_NAME
  FROM INFORMATION_SCHEMA.COLUMNS
  WHERE COLUMNPROPERTY(OBJECT_ID(TABLE_SCHEMA + '.' + TABLE_NAME), COLUMN_NAME, 'IsIdentity') = 1
) ic
  ON ic.TABLE_SCHEMA = c.TABLE_SCHEMA
 AND ic.TABLE_NAME = c.TABLE_NAME
 AND ic.COLUMN_NAME = c.COLUMN_NAME
OUTER APPLY (
  SELECT TOP (1) m.recid
  FROM system_edt_mappings m
  WHERE UPPER(m.element_mssql_type) = UPPER(
    CASE
      WHEN c.DATA_TYPE IN ('nvarchar', 'nchar', 'varchar', 'char')
        THEN CONCAT(c.DATA_TYPE, '(', CASE WHEN c.CHARACTER_MAXIMUM_LENGTH = -1 THEN 'max' ELSE CAST(c.CHARACTER_MAXIMUM_LENGTH AS NVARCHAR(10)) END, ')')
      WHEN c.DATA_TYPE IN ('decimal', 'numeric')
        THEN CONCAT(c.DATA_TYPE, '(', CAST(c.NUMERIC_PRECISION AS NVARCHAR(10)), ',', CAST(c.NUMERIC_SCALE AS NVARCHAR(10)), ')')
      WHEN c.DATA_TYPE IN ('datetime2', 'datetimeoffset', 'time')
        THEN CONCAT(c.DATA_TYPE, '(', CAST(c.DATETIME_PRECISION AS NVARCHAR(10)), ')')
      ELSE c.DATA_TYPE
    END
  )
) edt_exact
OUTER APPLY (
  SELECT TOP (1) m.recid
  FROM system_edt_mappings m
  WHERE UPPER(m.element_mssql_type) = UPPER(c.DATA_TYPE)
) edt_base
WHERE c.TABLE_SCHEMA = 'dbo'
  AND c.TABLE_NAME IN ('system_async_tasks', 'system_async_task_events');

DELETE i
FROM system_schema_indexes i
INNER JOIN system_schema_tables t ON t.recid = i.tables_recid
WHERE t.element_schema = 'dbo'
  AND t.element_name IN ('system_async_tasks', 'system_async_task_events');

INSERT INTO system_schema_indexes (tables_recid, element_name, element_columns, element_is_unique)
VALUES
  ((SELECT recid FROM system_schema_tables WHERE element_name = 'system_async_tasks' AND element_schema = 'dbo'), 'UQ_system_async_tasks_guid', 'element_guid', 1),
  ((SELECT recid FROM system_schema_tables WHERE element_name = 'system_async_tasks' AND element_schema = 'dbo'), 'IX_system_async_tasks_status_handler_type', 'element_status,element_handler_type', 0),
  ((SELECT recid FROM system_schema_tables WHERE element_name = 'system_async_task_events' AND element_schema = 'dbo'), 'IX_system_async_task_events_tasks_created_on', 'tasks_recid,element_created_on', 0);

DELETE fk
FROM system_schema_foreign_keys fk
INNER JOIN system_schema_tables t ON t.recid = fk.tables_recid
WHERE t.element_schema = 'dbo'
  AND t.element_name = 'system_async_task_events';

INSERT INTO system_schema_foreign_keys (
  tables_recid,
  element_column_name,
  referenced_tables_recid,
  element_referenced_column
)
VALUES (
  (SELECT recid FROM system_schema_tables WHERE element_name = 'system_async_task_events' AND element_schema = 'dbo'),
  'tasks_recid',
  (SELECT recid FROM system_schema_tables WHERE element_name = 'system_async_tasks' AND element_schema = 'dbo'),
  'recid'
);
