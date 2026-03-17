UPDATE finance_periods
SET numbers_recid = NULL
WHERE numbers_recid IS NOT NULL;
GO

DELETE FROM finance_numbers
WHERE element_account_number LIKE 'FP-%';
GO

DELETE FROM finance_accounts
WHERE element_parent = (
  SELECT element_guid FROM finance_accounts WHERE element_number = '5500'
);
GO

DELETE FROM finance_accounts
WHERE element_number = '5500';
GO

DELETE FROM finance_periods;
GO

DBCC CHECKIDENT ('finance_numbers', RESEED, 12);
GO
