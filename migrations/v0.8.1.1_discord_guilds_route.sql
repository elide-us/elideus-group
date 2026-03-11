-- Add guild management route to frontend navigation
-- The element_roles value should match ROLE_DISCORD_ADMIN's mask
-- Check the system_roles table for the correct mask value
INSERT INTO frontend_routes (element_enablement, element_roles, element_sequence, element_path, element_name, element_icon)
SELECT '1', sr.element_mask, 82, '/discord-guilds', 'Discord Guilds', 'Groups'
FROM system_roles sr WHERE sr.element_name = 'ROLE_DISCORD_ADMIN';
GO
