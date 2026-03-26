IF NOT EXISTS (SELECT 1 FROM frontend_routes WHERE element_sequence = 2050)
BEGIN
  INSERT INTO frontend_routes (element_enablement, element_roles, element_sequence, element_path, element_name, element_icon)
  VALUES ('0', 4611686018427387904, 2050, '/service-pages', 'Content Pages', 'Article');
END
GO
