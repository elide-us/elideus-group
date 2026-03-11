INSERT INTO frontend_routes (element_enablement, element_roles, element_sequence, element_path, element_name, element_icon)
SELECT '1', sr.element_mask, 15, '/system-models', 'System Models', 'Settings'
FROM system_roles sr WHERE sr.element_name = 'ROLE_SYSTEM_ADMIN';
GO
