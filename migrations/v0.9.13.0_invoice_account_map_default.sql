INSERT INTO finance_staging_account_map (
  element_service_pattern,
  element_meter_pattern,
  accounts_guid,
  element_priority,
  element_description,
  element_status,
  element_created_on,
  element_modified_on
)
SELECT
  'Azure Invoice',
  NULL,
  CAST('FB72A666-E9C3-47B5-A3D8-7A93D2132FC5' AS UNIQUEIDENTIFIER),
  10,
  'Azure Invoice summary line',
  1,
  SYSUTCDATETIME(),
  SYSUTCDATETIME()
WHERE NOT EXISTS (
  SELECT 1
  FROM finance_staging_account_map
  WHERE element_service_pattern = 'Azure Invoice'
    AND element_meter_pattern IS NULL
);
GO
