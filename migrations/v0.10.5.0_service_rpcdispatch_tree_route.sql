UPDATE dbo.frontend_routes
SET
  element_name = 'RPC Tree View',
  element_icon = 'AccountTree',
  element_sequence = 2045,
  element_roles = 4611686018427387904,
  element_enablement = '0'
WHERE element_path = '/service-rpcdispatch-tree';
GO

IF NOT EXISTS (
  SELECT 1
  FROM dbo.frontend_routes
  WHERE element_path = '/service-rpcdispatch-tree'
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
    '/service-rpcdispatch-tree',
    'RPC Tree View',
    'AccountTree',
    2045,
    4611686018427387904,
    '0'
  );
END;
GO
