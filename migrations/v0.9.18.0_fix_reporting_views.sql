SET NOCOUNT ON;
GO

ALTER VIEW [dbo].[vw_finance_period_status] AS
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
  ISNULL(j_agg.total_journals, 0) AS total_journals,
  ISNULL(j_agg.draft_journals, 0) AS draft_journals,
  ISNULL(j_agg.pending_journals, 0) AS pending_journals,
  ISNULL(j_agg.posted_journals, 0) AS posted_journals,
  ISNULL(j_agg.reversed_journals, 0) AS reversed_journals
FROM finance_periods AS p
LEFT JOIN (
  SELECT
    periods_guid,
    COUNT(*) AS total_journals,
    SUM(CASE WHEN element_status = 0 THEN 1 ELSE 0 END) AS draft_journals,
    SUM(CASE WHEN element_status = 1 THEN 1 ELSE 0 END) AS pending_journals,
    SUM(CASE WHEN element_status = 2 THEN 1 ELSE 0 END) AS posted_journals,
    SUM(CASE WHEN element_status = 3 THEN 1 ELSE 0 END) AS reversed_journals
  FROM finance_journals
  GROUP BY periods_guid
) AS j_agg ON j_agg.periods_guid = p.element_guid;
GO

ALTER VIEW [dbo].[vw_finance_trial_balance] AS
SELECT
  p.element_guid AS period_guid,
  p.element_year AS fiscal_year,
  p.element_period_number AS period_number,
  p.element_period_name AS period_name,
  a.element_guid AS account_guid,
  a.element_number AS account_number,
  a.element_name AS account_name,
  a.element_type AS account_type,
  ISNULL(SUM(jl.element_debit), 0) AS total_debit,
  ISNULL(SUM(jl.element_credit), 0) AS total_credit,
  ISNULL(SUM(jl.element_debit), 0) - ISNULL(SUM(jl.element_credit), 0) AS net_balance
FROM finance_journal_lines AS jl
JOIN finance_journals AS j ON j.recid = jl.journals_recid
JOIN finance_accounts AS a ON a.element_guid = jl.accounts_guid
JOIN finance_periods AS p ON p.element_guid = j.periods_guid
WHERE j.element_status IN (2, 3)
GROUP BY
  p.element_guid,
  p.element_year,
  p.element_period_number,
  p.element_period_name,
  a.element_guid,
  a.element_number,
  a.element_name,
  a.element_type;
GO

DELETE FROM finance_status_codes WHERE element_domain = 'journal';
GO

INSERT INTO finance_status_codes (element_domain, element_code, element_name, element_description)
VALUES
  ('journal', 0, 'draft', 'Journal created, not yet submitted'),
  ('journal', 1, 'pending_approval', 'Journal submitted, awaiting manager approval'),
  ('journal', 2, 'posted', 'Journal approved and posted to general ledger'),
  ('journal', 3, 'reversed', 'Journal has been reversed');
GO

UPDATE finance_status_codes
SET element_name = 'approved',
    element_description = 'Import approved for promotion',
    element_modified_on = SYSUTCDATETIME()
WHERE element_domain = 'import' AND element_code = 1;
GO

UPDATE finance_status_codes
SET element_name = 'pending_approval',
    element_description = 'Import staged, awaiting manager approval',
    element_modified_on = SYSUTCDATETIME()
WHERE element_domain = 'import' AND element_code = 4;
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
  WHERE element_name = 'vw_finance_trial_balance' AND element_schema = 'dbo'
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
    WHERE v.name = 'vw_finance_trial_balance' AND SCHEMA_NAME(v.schema_id) = 'dbo'
  ) AS m
  WHERE s.element_name = 'vw_finance_trial_balance' AND s.element_schema = 'dbo';
END
ELSE
BEGIN
  INSERT INTO system_schema_views (element_name, element_schema, element_definition)
  SELECT 'vw_finance_trial_balance', 'dbo', sm.definition
  FROM sys.views AS v
  JOIN sys.sql_modules AS sm ON sm.object_id = v.object_id
  WHERE v.name = 'vw_finance_trial_balance' AND SCHEMA_NAME(v.schema_id) = 'dbo';
END;
GO
