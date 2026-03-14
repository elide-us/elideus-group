SET NOCOUNT ON;

INSERT INTO system_schema_tables (element_name, element_schema) VALUES
  ('account_api_tokens', 'dbo');

INSERT INTO system_schema_columns (
  tables_recid, edt_recid, element_name, element_ordinal, element_nullable,
  element_default, element_max_length, element_is_primary_key, element_is_identity
) VALUES
  ((SELECT recid FROM system_schema_tables WHERE element_name = 'account_api_tokens' AND element_schema = 'dbo'), (SELECT recid FROM system_edt_mappings WHERE element_name = 'UUID'), 'element_token', 1, 0, '(newid())', NULL, 1, 0),
  ((SELECT recid FROM system_schema_tables WHERE element_name = 'account_api_tokens' AND element_schema = 'dbo'), (SELECT recid FROM system_edt_mappings WHERE element_name = 'INT64'), 'users_recid', 2, 0, NULL, NULL, 0, 0),
  ((SELECT recid FROM system_schema_tables WHERE element_name = 'account_api_tokens' AND element_schema = 'dbo'), (SELECT recid FROM system_edt_mappings WHERE element_name = 'STRING'), 'element_label', 3, 0, NULL, 256, 0, 0),
  ((SELECT recid FROM system_schema_tables WHERE element_name = 'account_api_tokens' AND element_schema = 'dbo'), (SELECT recid FROM system_edt_mappings WHERE element_name = 'INT64'), 'element_roles', 4, 0, '((0))', NULL, 0, 0),
  ((SELECT recid FROM system_schema_tables WHERE element_name = 'account_api_tokens' AND element_schema = 'dbo'), (SELECT recid FROM system_edt_mappings WHERE element_name = 'DATETIME_TZ'), 'element_created_on', 5, 0, '(sysutcdatetime())', NULL, 0, 0),
  ((SELECT recid FROM system_schema_tables WHERE element_name = 'account_api_tokens' AND element_schema = 'dbo'), (SELECT recid FROM system_edt_mappings WHERE element_name = 'DATETIME_TZ'), 'element_expires_on', 6, 1, NULL, NULL, 0, 0);

-- No additional indexes to register in system_schema_indexes;
-- the PK constraint creates the clustered index automatically.

INSERT INTO system_schema_foreign_keys (
  tables_recid, element_column_name, referenced_tables_recid, element_referenced_column
) VALUES
  ((SELECT recid FROM system_schema_tables WHERE element_name = 'account_api_tokens' AND element_schema = 'dbo'), 'users_recid', (SELECT recid FROM system_schema_tables WHERE element_name = 'account_users' AND element_schema = 'dbo'), 'recid');
