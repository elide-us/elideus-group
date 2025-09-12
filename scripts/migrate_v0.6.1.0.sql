-- Migrate database to version 0.6.1.0 by seeding auth_providers with Discord support.
IF NOT EXISTS (SELECT 1 FROM auth_providers WHERE recid = 1)
    INSERT INTO auth_providers (recid, element_name, element_display) VALUES (1, 'microsoft', 'Microsoft');
IF NOT EXISTS (SELECT 1 FROM auth_providers WHERE recid = 2)
    INSERT INTO auth_providers (recid, element_name, element_display) VALUES (2, 'google', 'Google');
IF NOT EXISTS (SELECT 1 FROM auth_providers WHERE recid = 3)
    INSERT INTO auth_providers (recid, element_name, element_display) VALUES (3, 'discord', 'Discord');
