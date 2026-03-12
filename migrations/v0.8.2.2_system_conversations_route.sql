IF NOT EXISTS (SELECT 1 FROM frontend_routes WHERE element_path = '/system-conversations')
  INSERT INTO frontend_routes (element_enablement, element_roles, element_sequence, element_path, element_name, element_icon)
  SELECT '1', sr.element_mask, 16, '/system-conversations', 'Conversations', 'smartToy'
  FROM system_roles sr WHERE sr.element_name = 'ROLE_SYSTEM_ADMIN';
GO
