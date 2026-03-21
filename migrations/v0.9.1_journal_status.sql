UPDATE finance_journals
SET element_status = 3
WHERE element_status = 2;
GO

UPDATE finance_journals
SET element_status = 2
WHERE element_status = 1;
GO
