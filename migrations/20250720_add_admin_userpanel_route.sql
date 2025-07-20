INSERT INTO routes (path, name, icon, required_roles, sequence)
VALUES ('/admin_userpanel', 'User Admin', 'menu', 0, 50)
ON CONFLICT (path) DO NOTHING;
