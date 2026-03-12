IF EXISTS (SELECT 1 FROM system_roles WHERE element_name = 'ROLE_FINANCE_ADMIN')
BEGIN
  INSERT INTO frontend_routes (element_enablement, element_roles, element_sequence, element_path, element_name, element_icon)
  SELECT '1', sr.element_mask, 90, '/finance-admin', 'Finance Admin', 'money'
  FROM system_roles sr WHERE sr.element_name = 'ROLE_FINANCE_ADMIN';
END
ELSE
BEGIN
  INSERT INTO frontend_routes (element_enablement, element_roles, element_sequence, element_path, element_name, element_icon)
  SELECT '1', COALESCE(sr.element_mask, 0), 90, '/finance-admin', 'Finance Admin', 'money'
  FROM system_roles sr WHERE sr.element_name = 'ROLE_SERVICE_ADMIN';
END
GO
