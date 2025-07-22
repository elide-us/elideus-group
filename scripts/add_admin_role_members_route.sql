INSERT INTO routes(path, name, icon, required_roles, sequence)
VALUES ('/admin_role_members', 'Role Members', 'group', (SELECT mask FROM roles WHERE name='ROLE_SYSTEM_ADMIN') | (SELECT mask FROM roles WHERE name='ROLE_REGISTERED'), (SELECT COALESCE(MAX(sequence),0)+10 FROM routes));
