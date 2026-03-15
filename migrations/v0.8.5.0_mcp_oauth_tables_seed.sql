SET NOCOUNT ON;

INSERT INTO system_schema_tables (element_name, element_schema) VALUES
  ('account_mcp_agents', 'dbo'),
  ('account_mcp_agent_tokens', 'dbo'),
  ('account_mcp_auth_codes', 'dbo');

INSERT INTO system_schema_columns (
  tables_recid, edt_recid, element_name, element_ordinal, element_nullable,
  element_default, element_max_length, element_is_primary_key, element_is_identity
) VALUES
  ((SELECT recid FROM system_schema_tables WHERE element_name = 'account_mcp_agents' AND element_schema = 'dbo'), (SELECT recid FROM system_edt_mappings WHERE element_name = 'INT64_IDENTITY'), 'recid', 1, 0, NULL, NULL, 1, 1),
  ((SELECT recid FROM system_schema_tables WHERE element_name = 'account_mcp_agents' AND element_schema = 'dbo'), (SELECT recid FROM system_edt_mappings WHERE element_name = 'UUID'), 'element_client_id', 2, 0, '(newid())', NULL, 0, 0),
  ((SELECT recid FROM system_schema_tables WHERE element_name = 'account_mcp_agents' AND element_schema = 'dbo'), (SELECT recid FROM system_edt_mappings WHERE element_name = 'STRING'), 'element_client_secret', 3, 1, NULL, 512, 0, 0),
  ((SELECT recid FROM system_schema_tables WHERE element_name = 'account_mcp_agents' AND element_schema = 'dbo'), (SELECT recid FROM system_edt_mappings WHERE element_name = 'STRING'), 'element_client_name', 4, 0, NULL, 256, 0, 0),
  ((SELECT recid FROM system_schema_tables WHERE element_name = 'account_mcp_agents' AND element_schema = 'dbo'), (SELECT recid FROM system_edt_mappings WHERE element_name = 'TEXT'), 'element_redirect_uris', 5, 1, NULL, NULL, 0, 0),
  ((SELECT recid FROM system_schema_tables WHERE element_name = 'account_mcp_agents' AND element_schema = 'dbo'), (SELECT recid FROM system_edt_mappings WHERE element_name = 'STRING'), 'element_grant_types', 6, 0, 'authorization_code', 1024, 0, 0),
  ((SELECT recid FROM system_schema_tables WHERE element_name = 'account_mcp_agents' AND element_schema = 'dbo'), (SELECT recid FROM system_edt_mappings WHERE element_name = 'STRING'), 'element_response_types', 7, 0, 'code', 256, 0, 0),
  ((SELECT recid FROM system_schema_tables WHERE element_name = 'account_mcp_agents' AND element_schema = 'dbo'), (SELECT recid FROM system_edt_mappings WHERE element_name = 'STRING'), 'element_scopes', 8, 0, 'mcp:schema:read', 1024, 0, 0),
  ((SELECT recid FROM system_schema_tables WHERE element_name = 'account_mcp_agents' AND element_schema = 'dbo'), (SELECT recid FROM system_edt_mappings WHERE element_name = 'INT64'), 'element_roles', 9, 0, '((0))', NULL, 0, 0),
  ((SELECT recid FROM system_schema_tables WHERE element_name = 'account_mcp_agents' AND element_schema = 'dbo'), (SELECT recid FROM system_edt_mappings WHERE element_name = 'INT64'), 'users_recid', 10, 1, NULL, NULL, 0, 0),
  ((SELECT recid FROM system_schema_tables WHERE element_name = 'account_mcp_agents' AND element_schema = 'dbo'), (SELECT recid FROM system_edt_mappings WHERE element_name = 'STRING'), 'element_ip_address', 11, 1, NULL, 64, 0, 0),
  ((SELECT recid FROM system_schema_tables WHERE element_name = 'account_mcp_agents' AND element_schema = 'dbo'), (SELECT recid FROM system_edt_mappings WHERE element_name = 'STRING'), 'element_user_agent', 12, 1, NULL, 1024, 0, 0),
  ((SELECT recid FROM system_schema_tables WHERE element_name = 'account_mcp_agents' AND element_schema = 'dbo'), (SELECT recid FROM system_edt_mappings WHERE element_name = 'BOOL'), 'element_is_active', 13, 0, '((1))', NULL, 0, 0),
  ((SELECT recid FROM system_schema_tables WHERE element_name = 'account_mcp_agents' AND element_schema = 'dbo'), (SELECT recid FROM system_edt_mappings WHERE element_name = 'DATETIME_TZ'), 'element_revoked_at', 14, 1, NULL, NULL, 0, 0),
  ((SELECT recid FROM system_schema_tables WHERE element_name = 'account_mcp_agents' AND element_schema = 'dbo'), (SELECT recid FROM system_edt_mappings WHERE element_name = 'DATETIME_TZ'), 'element_created_on', 15, 0, '(sysutcdatetime())', NULL, 0, 0),
  ((SELECT recid FROM system_schema_tables WHERE element_name = 'account_mcp_agents' AND element_schema = 'dbo'), (SELECT recid FROM system_edt_mappings WHERE element_name = 'DATETIME_TZ'), 'element_modified_on', 16, 0, '(sysutcdatetime())', NULL, 0, 0),

  ((SELECT recid FROM system_schema_tables WHERE element_name = 'account_mcp_agent_tokens' AND element_schema = 'dbo'), (SELECT recid FROM system_edt_mappings WHERE element_name = 'INT64_IDENTITY'), 'recid', 1, 0, NULL, NULL, 1, 1),
  ((SELECT recid FROM system_schema_tables WHERE element_name = 'account_mcp_agent_tokens' AND element_schema = 'dbo'), (SELECT recid FROM system_edt_mappings WHERE element_name = 'INT64'), 'agents_recid', 2, 0, NULL, NULL, 0, 0),
  ((SELECT recid FROM system_schema_tables WHERE element_name = 'account_mcp_agent_tokens' AND element_schema = 'dbo'), (SELECT recid FROM system_edt_mappings WHERE element_name = 'TEXT'), 'element_access_token', 3, 0, NULL, NULL, 0, 0),
  ((SELECT recid FROM system_schema_tables WHERE element_name = 'account_mcp_agent_tokens' AND element_schema = 'dbo'), (SELECT recid FROM system_edt_mappings WHERE element_name = 'TEXT'), 'element_refresh_token', 4, 1, NULL, NULL, 0, 0),
  ((SELECT recid FROM system_schema_tables WHERE element_name = 'account_mcp_agent_tokens' AND element_schema = 'dbo'), (SELECT recid FROM system_edt_mappings WHERE element_name = 'DATETIME_TZ'), 'element_access_exp', 5, 0, NULL, NULL, 0, 0),
  ((SELECT recid FROM system_schema_tables WHERE element_name = 'account_mcp_agent_tokens' AND element_schema = 'dbo'), (SELECT recid FROM system_edt_mappings WHERE element_name = 'DATETIME_TZ'), 'element_refresh_exp', 6, 1, NULL, NULL, 0, 0),
  ((SELECT recid FROM system_schema_tables WHERE element_name = 'account_mcp_agent_tokens' AND element_schema = 'dbo'), (SELECT recid FROM system_edt_mappings WHERE element_name = 'STRING'), 'element_scopes', 7, 0, NULL, 1024, 0, 0),
  ((SELECT recid FROM system_schema_tables WHERE element_name = 'account_mcp_agent_tokens' AND element_schema = 'dbo'), (SELECT recid FROM system_edt_mappings WHERE element_name = 'DATETIME_TZ'), 'element_revoked_at', 8, 1, NULL, NULL, 0, 0),
  ((SELECT recid FROM system_schema_tables WHERE element_name = 'account_mcp_agent_tokens' AND element_schema = 'dbo'), (SELECT recid FROM system_edt_mappings WHERE element_name = 'DATETIME_TZ'), 'element_created_on', 9, 0, '(sysutcdatetime())', NULL, 0, 0),

  ((SELECT recid FROM system_schema_tables WHERE element_name = 'account_mcp_auth_codes' AND element_schema = 'dbo'), (SELECT recid FROM system_edt_mappings WHERE element_name = 'INT64_IDENTITY'), 'recid', 1, 0, NULL, NULL, 1, 1),
  ((SELECT recid FROM system_schema_tables WHERE element_name = 'account_mcp_auth_codes' AND element_schema = 'dbo'), (SELECT recid FROM system_edt_mappings WHERE element_name = 'INT64'), 'agents_recid', 2, 0, NULL, NULL, 0, 0),
  ((SELECT recid FROM system_schema_tables WHERE element_name = 'account_mcp_auth_codes' AND element_schema = 'dbo'), (SELECT recid FROM system_edt_mappings WHERE element_name = 'INT64'), 'users_recid', 3, 0, NULL, NULL, 0, 0),
  ((SELECT recid FROM system_schema_tables WHERE element_name = 'account_mcp_auth_codes' AND element_schema = 'dbo'), (SELECT recid FROM system_edt_mappings WHERE element_name = 'STRING'), 'element_code', 4, 0, NULL, 256, 0, 0),
  ((SELECT recid FROM system_schema_tables WHERE element_name = 'account_mcp_auth_codes' AND element_schema = 'dbo'), (SELECT recid FROM system_edt_mappings WHERE element_name = 'STRING'), 'element_code_challenge', 5, 0, NULL, 256, 0, 0),
  ((SELECT recid FROM system_schema_tables WHERE element_name = 'account_mcp_auth_codes' AND element_schema = 'dbo'), (SELECT recid FROM system_edt_mappings WHERE element_name = 'STRING'), 'element_code_method', 6, 0, 'S256', 16, 0, 0),
  ((SELECT recid FROM system_schema_tables WHERE element_name = 'account_mcp_auth_codes' AND element_schema = 'dbo'), (SELECT recid FROM system_edt_mappings WHERE element_name = 'STRING'), 'element_redirect_uri', 7, 0, NULL, 2048, 0, 0),
  ((SELECT recid FROM system_schema_tables WHERE element_name = 'account_mcp_auth_codes' AND element_schema = 'dbo'), (SELECT recid FROM system_edt_mappings WHERE element_name = 'STRING'), 'element_scopes', 8, 0, NULL, 1024, 0, 0),
  ((SELECT recid FROM system_schema_tables WHERE element_name = 'account_mcp_auth_codes' AND element_schema = 'dbo'), (SELECT recid FROM system_edt_mappings WHERE element_name = 'BOOL'), 'element_consumed', 9, 0, '((0))', NULL, 0, 0),
  ((SELECT recid FROM system_schema_tables WHERE element_name = 'account_mcp_auth_codes' AND element_schema = 'dbo'), (SELECT recid FROM system_edt_mappings WHERE element_name = 'DATETIME_TZ'), 'element_expires_on', 10, 0, NULL, NULL, 0, 0),
  ((SELECT recid FROM system_schema_tables WHERE element_name = 'account_mcp_auth_codes' AND element_schema = 'dbo'), (SELECT recid FROM system_edt_mappings WHERE element_name = 'DATETIME_TZ'), 'element_created_on', 11, 0, '(sysutcdatetime())', NULL, 0, 0);

INSERT INTO system_schema_indexes (tables_recid, element_name, element_columns, element_is_unique) VALUES
  ((SELECT recid FROM system_schema_tables WHERE element_name = 'account_mcp_agents' AND element_schema = 'dbo'), 'UQ_account_mcp_agents_client_id', 'element_client_id', 1),
  ((SELECT recid FROM system_schema_tables WHERE element_name = 'account_mcp_agents' AND element_schema = 'dbo'), 'IX_account_mcp_agents_users', 'users_recid', 0),
  ((SELECT recid FROM system_schema_tables WHERE element_name = 'account_mcp_agent_tokens' AND element_schema = 'dbo'), 'IX_account_mcp_agent_tokens_agents', 'agents_recid', 0),
  ((SELECT recid FROM system_schema_tables WHERE element_name = 'account_mcp_auth_codes' AND element_schema = 'dbo'), 'UQ_account_mcp_auth_codes_code', 'element_code', 1);

INSERT INTO system_schema_foreign_keys (
  tables_recid, element_column_name, referenced_tables_recid, element_referenced_column
) VALUES
  ((SELECT recid FROM system_schema_tables WHERE element_name = 'account_mcp_agents' AND element_schema = 'dbo'), 'users_recid', (SELECT recid FROM system_schema_tables WHERE element_name = 'account_users' AND element_schema = 'dbo'), 'recid'),
  ((SELECT recid FROM system_schema_tables WHERE element_name = 'account_mcp_agent_tokens' AND element_schema = 'dbo'), 'agents_recid', (SELECT recid FROM system_schema_tables WHERE element_name = 'account_mcp_agents' AND element_schema = 'dbo'), 'recid'),
  ((SELECT recid FROM system_schema_tables WHERE element_name = 'account_mcp_auth_codes' AND element_schema = 'dbo'), 'agents_recid', (SELECT recid FROM system_schema_tables WHERE element_name = 'account_mcp_agents' AND element_schema = 'dbo'), 'recid'),
  ((SELECT recid FROM system_schema_tables WHERE element_name = 'account_mcp_auth_codes' AND element_schema = 'dbo'), 'users_recid', (SELECT recid FROM system_schema_tables WHERE element_name = 'account_users' AND element_schema = 'dbo'), 'recid');
