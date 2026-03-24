SET NOCOUNT ON;
GO

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
WHERE j.element_status = 1
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

IF OBJECT_ID(N'[dbo].[vw_finance_journal_summary]', N'V') IS NOT NULL
BEGIN
  DROP VIEW [dbo].[vw_finance_journal_summary];
END;
GO

CREATE VIEW [dbo].[vw_finance_journal_summary] AS
SELECT
  j.recid,
  j.element_name AS journal_name,
  j.element_description AS journal_description,
  j.element_posting_key AS posting_key,
  j.element_source_type AS source_type,
  j.element_source_id AS source_id,
  j.element_status AS journal_status,
  j.periods_guid,
  p.element_year AS fiscal_year,
  p.element_period_name AS period_name,
  j.element_posted_by AS posted_by,
  j.element_posted_on AS posted_on,
  j.element_reversed_by AS reversed_by,
  j.element_reversal_of AS reversal_of,
  j.element_created_on AS created_on,
  ISNULL(line_agg.line_count, 0) AS line_count,
  ISNULL(line_agg.total_debit, 0) AS total_debit,
  ISNULL(line_agg.total_credit, 0) AS total_credit
FROM finance_journals AS j
LEFT JOIN finance_periods AS p ON p.element_guid = j.periods_guid
LEFT JOIN (
  SELECT
    journals_recid,
    COUNT(*) AS line_count,
    SUM(element_debit) AS total_debit,
    SUM(element_credit) AS total_credit
  FROM finance_journal_lines
  GROUP BY journals_recid
) AS line_agg ON line_agg.journals_recid = j.recid;
GO

IF OBJECT_ID(N'[dbo].[vw_finance_period_status]', N'V') IS NOT NULL
BEGIN
  DROP VIEW [dbo].[vw_finance_period_status];
END;
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
  ISNULL(j_agg.total_journals, 0) AS total_journals,
  ISNULL(j_agg.unposted_journals, 0) AS unposted_journals,
  ISNULL(j_agg.posted_journals, 0) AS posted_journals,
  ISNULL(j_agg.reversed_journals, 0) AS reversed_journals
FROM finance_periods AS p
LEFT JOIN (
  SELECT
    periods_guid,
    COUNT(*) AS total_journals,
    SUM(CASE WHEN element_status = 0 THEN 1 ELSE 0 END) AS unposted_journals,
    SUM(CASE WHEN element_status = 1 THEN 1 ELSE 0 END) AS posted_journals,
    SUM(CASE WHEN element_status = 2 THEN 1 ELSE 0 END) AS reversed_journals
  FROM finance_journals
  GROUP BY periods_guid
) AS j_agg ON j_agg.periods_guid = p.element_guid;
GO

IF OBJECT_ID(N'[dbo].[vw_finance_credit_lot_summary]', N'V') IS NOT NULL
BEGIN
  DROP VIEW [dbo].[vw_finance_credit_lot_summary];
END;
GO

CREATE VIEW [dbo].[vw_finance_credit_lot_summary] AS
SELECT
  cl.recid,
  cl.users_guid,
  au.element_display AS user_display_name,
  cl.element_lot_number AS lot_number,
  cl.element_source_type AS source_type,
  cl.element_credits_original AS credits_original,
  cl.element_credits_remaining AS credits_remaining,
  cl.element_unit_price AS unit_price,
  cl.element_total_paid AS total_paid,
  cl.element_currency AS currency,
  cl.element_expires_at AS expires_at,
  cl.element_expired AS expired,
  cl.element_source_id AS source_id,
  cl.element_status AS lot_status,
  cl.element_created_on AS created_on,
  ISNULL(evt.event_count, 0) AS event_count,
  ISNULL(evt.total_consumed, 0) AS total_consumed
FROM finance_credit_lots AS cl
JOIN account_users AS au ON au.element_guid = cl.users_guid
LEFT JOIN (
  SELECT
    lots_recid,
    COUNT(*) AS event_count,
    ISNULL(SUM(CASE WHEN element_event_type = 'Consume' THEN element_credits ELSE 0 END), 0) AS total_consumed
  FROM finance_credit_lot_events
  GROUP BY lots_recid
) AS evt ON evt.lots_recid = cl.recid;
GO

IF NOT EXISTS (
  SELECT 1 FROM system_schema_views WHERE element_name = 'vw_finance_trial_balance' AND element_schema = 'dbo'
)
BEGIN
  INSERT INTO system_schema_views (element_name, element_schema)
  VALUES ('vw_finance_trial_balance', 'dbo');
END;
GO

IF NOT EXISTS (
  SELECT 1 FROM system_schema_views WHERE element_name = 'vw_finance_journal_summary' AND element_schema = 'dbo'
)
BEGIN
  INSERT INTO system_schema_views (element_name, element_schema)
  VALUES ('vw_finance_journal_summary', 'dbo');
END;
GO

IF NOT EXISTS (
  SELECT 1 FROM system_schema_views WHERE element_name = 'vw_finance_period_status' AND element_schema = 'dbo'
)
BEGIN
  INSERT INTO system_schema_views (element_name, element_schema)
  VALUES ('vw_finance_period_status', 'dbo');
END;
GO

IF NOT EXISTS (
  SELECT 1 FROM system_schema_views WHERE element_name = 'vw_finance_credit_lot_summary' AND element_schema = 'dbo'
)
BEGIN
  INSERT INTO system_schema_views (element_name, element_schema)
  VALUES ('vw_finance_credit_lot_summary', 'dbo');
END;
GO


------------- Manual patch


IF NOT EXISTS (SELECT 1 FROM system_schema_views WHERE element_name = 'vw_finance_trial_balance' AND element_schema = 'dbo')
BEGIN
    INSERT INTO system_schema_views (element_name, element_schema, element_definition)
    SELECT 'vw_finance_trial_balance', 'dbo', m.definition
    FROM sys.views v JOIN sys.sql_modules m ON v.object_id = m.object_id
    WHERE v.name = 'vw_finance_trial_balance';
END
GO

IF NOT EXISTS (SELECT 1 FROM system_schema_views WHERE element_name = 'vw_finance_journal_summary' AND element_schema = 'dbo')
BEGIN
    INSERT INTO system_schema_views (element_name, element_schema, element_definition)
    SELECT 'vw_finance_journal_summary', 'dbo', m.definition
    FROM sys.views v JOIN sys.sql_modules m ON v.object_id = m.object_id
    WHERE v.name = 'vw_finance_journal_summary';
END
GO

IF NOT EXISTS (SELECT 1 FROM system_schema_views WHERE element_name = 'vw_finance_period_status' AND element_schema = 'dbo')
BEGIN
    INSERT INTO system_schema_views (element_name, element_schema, element_definition)
    SELECT 'vw_finance_period_status', 'dbo', m.definition
    FROM sys.views v JOIN sys.sql_modules m ON v.object_id = m.object_id
    WHERE v.name = 'vw_finance_period_status';
END
GO

IF NOT EXISTS (SELECT 1 FROM system_schema_views WHERE element_name = 'vw_finance_credit_lot_summary' AND element_schema = 'dbo')
BEGIN
    INSERT INTO system_schema_views (element_name, element_schema, element_definition)
    SELECT 'vw_finance_credit_lot_summary', 'dbo', m.definition
    FROM sys.views v JOIN sys.sql_modules m ON v.object_id = m.object_id
    WHERE v.name = 'vw_finance_credit_lot_summary';
END
GO