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
