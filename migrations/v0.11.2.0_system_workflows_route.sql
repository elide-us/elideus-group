IF NOT EXISTS (SELECT 1 FROM frontend_routes WHERE element_path = '/system-workflows')
BEGIN
  INSERT INTO frontend_routes (element_enablement, element_roles, element_sequence, element_path, element_name, element_icon)
  SELECT
    '1',
    COALESCE((SELECT TOP 1 element_roles FROM frontend_routes WHERE element_path = '/system-async-tasks'), 32768),
    820,
    '/system-workflows',
    'Workflows',
    'AccountTree';
END;
GO
