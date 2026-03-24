SET NOCOUNT ON;
GO

-- Fix trial balance to include reversed journals.
-- Both Posted (1) and Reversed (2) journals have valid ledger entries.
IF OBJECT_ID(N'[dbo].[vw_finance_trial_balance]', N'V') IS NOT NULL
BEGIN
  DROP VIEW [dbo].[vw_finance_trial_balance];
END;
GO

CREATE VIEW [dbo].[vw_finance_trial_balance] AS
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
WHERE j.element_status IN (1, 2)
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

IF EXISTS (
  SELECT 1
  FROM system_schema_views
  WHERE element_name = 'vw_finance_trial_balance' AND element_schema = 'dbo'
)
BEGIN
  UPDATE s
  SET s.element_definition = m.definition
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
