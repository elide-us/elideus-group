UPDATE dbo.frontend_routes
SET
  element_name = 'RPC Dispatch',
  element_icon = 'Api',
  element_sequence = 2040,
  element_roles = 4611686018427387904,
  element_enablement = '0'
WHERE element_path = '/service-rpcdispatch';
GO

IF NOT EXISTS (
  SELECT 1
  FROM dbo.frontend_routes
  WHERE element_path = '/service-rpcdispatch'
)
BEGIN
  INSERT INTO dbo.frontend_routes (
    element_path,
    element_name,
    element_icon,
    element_sequence,
    element_roles,
    element_enablement
  )
  VALUES (
    '/service-rpcdispatch',
    'RPC Dispatch',
    'Api',
    2040,
    4611686018427387904,
    '0'
  );
END;
GO
