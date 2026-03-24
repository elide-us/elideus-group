IF COL_LENGTH('dbo.finance_periods', 'element_closed_by') IS NULL
BEGIN
  ALTER TABLE [dbo].[finance_periods]
  ADD [element_closed_by] NVARCHAR(128) NULL;
END;
GO

IF COL_LENGTH('dbo.finance_periods', 'element_closed_on') IS NULL
BEGIN
  ALTER TABLE [dbo].[finance_periods]
  ADD [element_closed_on] DATETIMEOFFSET(7) NULL;
END;
GO

IF COL_LENGTH('dbo.finance_periods', 'element_locked_by') IS NULL
BEGIN
  ALTER TABLE [dbo].[finance_periods]
  ADD [element_locked_by] NVARCHAR(128) NULL;
END;
GO

IF COL_LENGTH('dbo.finance_periods', 'element_locked_on') IS NULL
BEGIN
  ALTER TABLE [dbo].[finance_periods]
  ADD [element_locked_on] DATETIMEOFFSET(7) NULL;
END;
GO

DECLARE @finance_periods_table_recid BIGINT;
SELECT @finance_periods_table_recid = recid
FROM system_schema_tables
WHERE element_name = 'finance_periods'
  AND element_schema = 'dbo';

IF NOT EXISTS (
  SELECT 1
  FROM system_schema_columns
  WHERE tables_recid = @finance_periods_table_recid
    AND element_name = 'element_closed_by'
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
  VALUES (@finance_periods_table_recid, 8, 'element_closed_by', 17, 1, NULL, 128, 0, 0);
END;

IF NOT EXISTS (
  SELECT 1
  FROM system_schema_columns
  WHERE tables_recid = @finance_periods_table_recid
    AND element_name = 'element_closed_on'
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
  VALUES (@finance_periods_table_recid, 7, 'element_closed_on', 18, 1, NULL, NULL, 0, 0);
END;

IF NOT EXISTS (
  SELECT 1
  FROM system_schema_columns
  WHERE tables_recid = @finance_periods_table_recid
    AND element_name = 'element_locked_by'
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
  VALUES (@finance_periods_table_recid, 8, 'element_locked_by', 19, 1, NULL, 128, 0, 0);
END;

IF NOT EXISTS (
  SELECT 1
  FROM system_schema_columns
  WHERE tables_recid = @finance_periods_table_recid
    AND element_name = 'element_locked_on'
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
  VALUES (@finance_periods_table_recid, 7, 'element_locked_on', 20, 1, NULL, NULL, 0, 0);
END;
GO

IF OBJECT_ID(N'dbo.vw_finance_period_status', N'V') IS NOT NULL
  DROP VIEW dbo.vw_finance_period_status;
GO

CREATE VIEW [dbo].[vw_finance_period_status] AS
SELECT
  p.element_guid AS period_guid,
  p.element_year AS fiscal_year,
  p.element_period_number AS period_number,
  p.element_period_name AS period_name,
  p.element_start_date AS start_date,
  p.element_end_date AS end_date,
  p.element_close_type AS close_type,
  p.element_status AS period_status,
  p.element_has_closing_week AS has_closing_week,
  p.element_closed_by AS closed_by,
  p.element_closed_on AS closed_on,
  p.element_locked_by AS locked_by,
  p.element_locked_on AS locked_on,
  ISNULL(j_agg.total_journals, 0) AS total_journals,
  ISNULL(j_agg.draft_journals, 0) AS draft_journals,
  ISNULL(j_agg.pending_approval_journals, 0) AS pending_approval_journals,
  ISNULL(j_agg.posted_journals, 0) AS posted_journals,
  ISNULL(j_agg.reversed_journals, 0) AS reversed_journals
FROM finance_periods AS p
LEFT JOIN (
  SELECT
    periods_guid,
    COUNT(*) AS total_journals,
    SUM(CASE WHEN element_status = 0 THEN 1 ELSE 0 END) AS draft_journals,            -- JOURNAL_DRAFT
    SUM(CASE WHEN element_status = 1 THEN 1 ELSE 0 END) AS pending_approval_journals, -- JOURNAL_PENDING_APPROVAL
    SUM(CASE WHEN element_status = 2 THEN 1 ELSE 0 END) AS posted_journals,           -- JOURNAL_POSTED
    SUM(CASE WHEN element_status = 3 THEN 1 ELSE 0 END) AS reversed_journals          -- JOURNAL_REVERSED
  FROM finance_journals
  GROUP BY periods_guid
) AS j_agg ON j_agg.periods_guid = p.element_guid;
GO

IF OBJECT_ID(N'dbo.vw_finance_period_close_blockers', N'V') IS NOT NULL
  DROP VIEW dbo.vw_finance_period_close_blockers;
GO

CREATE VIEW [dbo].[vw_finance_period_close_blockers] AS
SELECT
  p.element_guid AS period_guid,
  CAST('journal' AS NVARCHAR(64)) AS blocker_type,
  j.recid AS blocker_recid,
  COALESCE(j.element_posting_key, j.element_name, CONCAT('Journal #', CAST(j.recid AS NVARCHAR(32)))) AS blocker_name,
  CASE
    WHEN j.element_status = 0 THEN 'Journal is still in Draft status and must be posted, reversed, or deleted before close.' -- JOURNAL_DRAFT
    WHEN j.element_status = 1 THEN 'Journal is still Pending Approval and must be posted, reversed, or deleted before close.' -- JOURNAL_PENDING_APPROVAL
    ELSE 'Journal is not in a terminal status.'
  END AS blocker_reason
FROM finance_periods AS p
JOIN finance_journals AS j ON j.periods_guid = p.element_guid
WHERE j.element_status IN (0, 1) -- JOURNAL_DRAFT, JOURNAL_PENDING_APPROVAL

UNION ALL

SELECT
  p.element_guid AS period_guid,
  CAST('import' AS NVARCHAR(64)) AS blocker_type,
  si.recid AS blocker_recid,
  CONCAT(si.element_source, ' / ', si.element_metric, ' / #', CAST(si.recid AS NVARCHAR(32))) AS blocker_name,
  CASE
    WHEN si.element_status = 0 THEN 'Import is still Pending and must be promoted, rejected, or deleted before close.' -- IMPORT_PENDING
    WHEN si.element_status = 1 THEN 'Import is still Approved and must be promoted, rejected, or deleted before close.' -- IMPORT_APPROVED
    WHEN si.element_status = 4 THEN 'Import is still Pending Approval and must be promoted, rejected, or deleted before close.' -- IMPORT_PENDING_APPROVAL
    ELSE 'Import is not in a terminal status.'
  END AS blocker_reason
FROM finance_periods AS p
JOIN finance_staging_imports AS si
  ON si.element_period_start <= p.element_end_date
 AND si.element_period_end >= p.element_start_date
WHERE si.element_status IN (0, 1, 4) -- IMPORT_PENDING, IMPORT_APPROVED, IMPORT_PENDING_APPROVAL

UNION ALL

SELECT
  p.element_guid AS period_guid,
  CAST('credit_lot_revrec' AS NVARCHAR(64)) AS blocker_type,
  e.recid AS blocker_recid,
  COALESCE(cl.element_lot_number, CONCAT('Credit lot #', CAST(cl.recid AS NVARCHAR(32)))) AS blocker_name,
  CASE
    WHEN e.journals_recid IS NULL THEN 'Revenue recognition journal has not been created for this purchase credit consumption.'
    WHEN j.element_status <> 2 THEN 'Linked revenue recognition journal is not posted.' -- JOURNAL_POSTED
    ELSE 'Revenue recognition is incomplete.'
  END AS blocker_reason
FROM finance_periods AS p
JOIN finance_credit_lot_events AS e
  ON CAST(e.element_created_on AS DATE) BETWEEN p.element_start_date AND p.element_end_date
JOIN finance_credit_lots AS cl ON cl.recid = e.lots_recid
LEFT JOIN finance_journals AS j ON j.recid = e.journals_recid
WHERE e.element_event_type = 'Consume'
  AND cl.element_source_type = 'purchase'
  AND (e.journals_recid IS NULL OR j.element_status <> 2); -- JOURNAL_POSTED
GO

IF EXISTS (
  SELECT 1
  FROM system_schema_views
  WHERE element_name = 'vw_finance_period_status' AND element_schema = 'dbo'
)
BEGIN
  UPDATE s
  SET s.element_definition = m.definition,
      s.element_modified_on = SYSUTCDATETIME()
  FROM system_schema_views AS s
  CROSS JOIN (
    SELECT sm.definition
    FROM sys.views AS v
    JOIN sys.sql_modules AS sm ON sm.object_id = v.object_id
    WHERE v.name = 'vw_finance_period_status' AND SCHEMA_NAME(v.schema_id) = 'dbo'
  ) AS m
  WHERE s.element_name = 'vw_finance_period_status' AND s.element_schema = 'dbo';
END
ELSE
BEGIN
  INSERT INTO system_schema_views (element_name, element_schema, element_definition)
  SELECT 'vw_finance_period_status', 'dbo', sm.definition
  FROM sys.views AS v
  JOIN sys.sql_modules AS sm ON sm.object_id = v.object_id
  WHERE v.name = 'vw_finance_period_status' AND SCHEMA_NAME(v.schema_id) = 'dbo';
END;
GO

IF EXISTS (
  SELECT 1
  FROM system_schema_views
  WHERE element_name = 'vw_finance_period_close_blockers' AND element_schema = 'dbo'
)
BEGIN
  UPDATE s
  SET s.element_definition = m.definition,
      s.element_modified_on = SYSUTCDATETIME()
  FROM system_schema_views AS s
  CROSS JOIN (
    SELECT sm.definition
    FROM sys.views AS v
    JOIN sys.sql_modules AS sm ON sm.object_id = v.object_id
    WHERE v.name = 'vw_finance_period_close_blockers' AND SCHEMA_NAME(v.schema_id) = 'dbo'
  ) AS m
  WHERE s.element_name = 'vw_finance_period_close_blockers' AND s.element_schema = 'dbo';
END
ELSE
BEGIN
  INSERT INTO system_schema_views (element_name, element_schema, element_definition)
  SELECT 'vw_finance_period_close_blockers', 'dbo', sm.definition
  FROM sys.views AS v
  JOIN sys.sql_modules AS sm ON sm.object_id = v.object_id
  WHERE v.name = 'vw_finance_period_close_blockers' AND SCHEMA_NAME(v.schema_id) = 'dbo';
END;
GO
