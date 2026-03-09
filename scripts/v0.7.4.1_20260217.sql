IF NOT EXISTS (SELECT 1 FROM sys.tables WHERE name = 'system_schema_tables' AND schema_id = SCHEMA_ID('dbo'))
BEGIN
  CREATE TABLE dbo.system_schema_tables (
    recid bigint NOT NULL,
    element_name nvarchar(128) NOT NULL,
    element_schema nvarchar(64) DEFAULT ('dbo') NOT NULL,
    element_description nvarchar(1024) NULL,
    element_created_on datetimeoffset DEFAULT (sysutcdatetime()) NOT NULL,
    element_modified_on datetimeoffset DEFAULT (sysutcdatetime()) NOT NULL,
    PRIMARY KEY (recid)
  );
END;

IF NOT EXISTS (SELECT 1 FROM sys.tables WHERE name = 'system_schema_columns' AND schema_id = SCHEMA_ID('dbo'))
BEGIN
  CREATE TABLE dbo.system_schema_columns (
    recid bigint NOT NULL,
    tables_recid bigint NOT NULL,
    edt_recid bigint NOT NULL,
    element_name nvarchar(128) NOT NULL,
    element_ordinal int NOT NULL,
    element_nullable bit DEFAULT ((0)) NOT NULL,
    element_default nvarchar(512) NULL,
    element_max_length int NULL,
    element_is_primary_key bit DEFAULT ((0)) NOT NULL,
    element_is_identity bit DEFAULT ((0)) NOT NULL,
    element_description nvarchar(1024) NULL,
    element_created_on datetimeoffset DEFAULT (sysutcdatetime()) NOT NULL,
    element_modified_on datetimeoffset DEFAULT (sysutcdatetime()) NOT NULL,
    PRIMARY KEY (recid),
    FOREIGN KEY (tables_recid) REFERENCES dbo.system_schema_tables(recid),
    FOREIGN KEY (edt_recid) REFERENCES dbo.system_edt_mappings(recid)
  );
END;

IF NOT EXISTS (SELECT 1 FROM sys.tables WHERE name = 'system_schema_indexes' AND schema_id = SCHEMA_ID('dbo'))
BEGIN
  CREATE TABLE dbo.system_schema_indexes (
    recid bigint NOT NULL,
    tables_recid bigint NOT NULL,
    element_name nvarchar(256) NOT NULL,
    element_columns nvarchar(1024) NOT NULL,
    element_is_unique bit DEFAULT ((0)) NOT NULL,
    element_created_on datetimeoffset DEFAULT (sysutcdatetime()) NOT NULL,
    element_modified_on datetimeoffset DEFAULT (sysutcdatetime()) NOT NULL,
    PRIMARY KEY (recid),
    FOREIGN KEY (tables_recid) REFERENCES dbo.system_schema_tables(recid)
  );
END;

IF NOT EXISTS (SELECT 1 FROM sys.tables WHERE name = 'system_schema_foreign_keys' AND schema_id = SCHEMA_ID('dbo'))
BEGIN
  CREATE TABLE dbo.system_schema_foreign_keys (
    recid bigint NOT NULL,
    tables_recid bigint NOT NULL,
    element_column_name nvarchar(128) NOT NULL,
    referenced_tables_recid bigint NOT NULL,
    element_referenced_column nvarchar(128) NOT NULL,
    element_created_on datetimeoffset DEFAULT (sysutcdatetime()) NOT NULL,
    element_modified_on datetimeoffset DEFAULT (sysutcdatetime()) NOT NULL,
    PRIMARY KEY (recid),
    FOREIGN KEY (tables_recid) REFERENCES dbo.system_schema_tables(recid),
    FOREIGN KEY (referenced_tables_recid) REFERENCES dbo.system_schema_tables(recid)
  );
END;

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'UQ_system_schema_tables_schema_name' AND object_id = OBJECT_ID('dbo.system_schema_tables'))
BEGIN
  CREATE UNIQUE INDEX UQ_system_schema_tables_schema_name ON dbo.system_schema_tables (element_schema, element_name);
END;

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'UQ_system_schema_columns_table_column' AND object_id = OBJECT_ID('dbo.system_schema_columns'))
BEGIN
  CREATE UNIQUE INDEX UQ_system_schema_columns_table_column ON dbo.system_schema_columns (tables_recid, element_name);
END;

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'IX_system_schema_columns_table_ordinal' AND object_id = OBJECT_ID('dbo.system_schema_columns'))
BEGIN
  CREATE INDEX IX_system_schema_columns_table_ordinal ON dbo.system_schema_columns (tables_recid, element_ordinal);
END;

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'UQ_system_schema_indexes_table_name' AND object_id = OBJECT_ID('dbo.system_schema_indexes'))
BEGIN
  CREATE UNIQUE INDEX UQ_system_schema_indexes_table_name ON dbo.system_schema_indexes (tables_recid, element_name);
END;

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'UQ_system_schema_foreign_keys_table_column' AND object_id = OBJECT_ID('dbo.system_schema_foreign_keys'))
BEGIN
  CREATE UNIQUE INDEX UQ_system_schema_foreign_keys_table_column ON dbo.system_schema_foreign_keys (tables_recid, element_column_name);
END;

MERGE dbo.system_schema_tables AS target
USING (
  VALUES
    (1, 'auth_providers', 'dbo'),
    (2, 'account_users', 'dbo'),
    (3, 'users_sessions', 'dbo'),
    (4, 'storage_types', 'dbo'),
    (5, 'users_auth', 'dbo'),
    (6, 'account_actions', 'dbo'),
    (7, 'users_storage_cache', 'dbo'),
    (8, 'frontend_links', 'dbo'),
    (9, 'frontend_routes', 'dbo'),
    (10, 'system_config', 'dbo'),
    (11, 'users_credits', 'dbo'),
    (12, 'users_enablements', 'dbo'),
    (13, 'users_profileimg', 'dbo'),
    (14, 'users_roles', 'dbo'),
    (15, 'system_roles', 'dbo'),
    (16, 'discord_guilds', 'dbo'),
    (17, 'sessions_devices', 'dbo'),
    (18, 'users_actions_log', 'dbo'),
    (19, 'assistant_models', 'dbo'),
    (20, 'assistant_personas', 'dbo'),
    (21, 'assistant_conversations', 'dbo'),
    (22, 'service_pages', 'dbo'),
    (23, 'system_edt_mappings', 'dbo'),
    (24, 'system_schema_tables', 'dbo'),
    (25, 'system_schema_columns', 'dbo'),
    (26, 'system_schema_indexes', 'dbo'),
    (27, 'system_schema_foreign_keys', 'dbo')
) AS source (recid, element_name, element_schema)
ON target.recid = source.recid
WHEN MATCHED THEN
  UPDATE SET
    element_name = source.element_name,
    element_schema = source.element_schema,
    element_modified_on = sysutcdatetime()
WHEN NOT MATCHED BY TARGET THEN
  INSERT (recid, element_name, element_schema)
  VALUES (source.recid, source.element_name, source.element_schema);

MERGE dbo.system_schema_columns AS target
USING (
  SELECT raw_source.recid, raw_source.tables_recid, edt.recid AS edt_recid, raw_source.element_name, raw_source.element_ordinal, raw_source.element_nullable, raw_source.element_default, raw_source.element_max_length, raw_source.element_is_primary_key, raw_source.element_is_identity
  FROM (
    VALUES
    (1, 1, 'INT32', 'recid', 1, 0, NULL, NULL, 1, 0),
    (2, 1, 'STRING', 'element_name', 2, 0, NULL, 1024, 0, 0),
    (3, 1, 'STRING', 'element_display', 3, 0, NULL, 1024, 0, 0),
    (4, 2, 'INT32', 'recid', 1, 0, NULL, NULL, 1, 0),
    (5, 2, 'UUID', 'element_guid', 2, 0, NULL, NULL, 0, 0),
    (6, 2, 'TEXT', 'element_rotkey', 3, 0, NULL, NULL, 0, 0),
    (7, 2, 'DATETIME_TZ', 'element_rotkey_iat', 4, 0, '(sysdatetimeoffset())', NULL, 0, 0),
    (8, 2, 'DATETIME_TZ', 'element_rotkey_exp', 5, 0, NULL, NULL, 0, 0),
    (9, 2, 'STRING', 'element_email', 6, 0, NULL, 1024, 0, 0),
    (10, 2, 'STRING', 'element_display', 7, 0, NULL, 1024, 0, 0),
    (11, 2, 'INT32', 'providers_recid', 8, 1, NULL, NULL, 0, 0),
    (12, 2, 'BOOL', 'element_optin', 9, 0, '((0))', NULL, 0, 0),
    (13, 2, 'DATETIME_TZ', 'element_created_on', 10, 0, '(sysdatetimeoffset())', NULL, 0, 0),
    (14, 2, 'DATETIME_TZ', 'element_modified_on', 11, 0, '(sysdatetimeoffset())', NULL, 0, 0),
    (15, 3, 'UUID', 'element_guid', 1, 0, NULL, NULL, 1, 0),
    (16, 3, 'UUID', 'users_guid', 2, 0, NULL, NULL, 0, 0),
    (17, 3, 'DATETIME_TZ', 'element_created_at', 3, 0, '(sysdatetimeoffset())', NULL, 0, 0),
    (18, 3, 'TEXT', 'element_token', 4, 0, '(CONVERT([nvarchar](64),newid()))', NULL, 0, 0),
    (19, 3, 'DATETIME_TZ', 'element_token_iat', 5, 0, '(sysutcdatetime())', NULL, 0, 0),
    (20, 3, 'DATETIME_TZ', 'element_token_exp', 6, 0, '(sysutcdatetime())', NULL, 0, 0),
    (21, 3, 'DATETIME', 'element_created_on', 7, 0, '(sysutcdatetime())', NULL, 0, 0),
    (22, 3, 'DATETIME', 'element_modified_on', 8, 0, '(sysutcdatetime())', NULL, 0, 0),
    (23, 4, 'INT32', 'recid', 1, 0, NULL, NULL, 1, 0),
    (24, 4, 'STRING_ASCII', 'element_mimetype', 2, 0, NULL, 128, 0, 0),
    (25, 4, 'STRING_ASCII', 'element_displaytype', 3, 0, NULL, 64, 0, 0),
    (26, 5, 'INT32', 'recid', 1, 0, NULL, NULL, 1, 0),
    (27, 5, 'UUID', 'users_guid', 2, 0, NULL, NULL, 0, 0),
    (28, 5, 'INT32', 'providers_recid', 3, 0, NULL, NULL, 0, 0),
    (29, 5, 'UUID', 'element_identifier', 4, 0, NULL, NULL, 0, 0),
    (30, 5, 'BOOL', 'element_linked', 5, 0, '((0))', NULL, 0, 0),
    (31, 5, 'DATETIME_TZ', 'created_on', 6, 0, '(sysutcdatetime())', NULL, 0, 0),
    (32, 5, 'DATETIME_TZ', 'modified_on', 7, 0, '(sysutcdatetime())', NULL, 0, 0),
    (33, 6, 'INT32', 'recid', 1, 0, NULL, NULL, 1, 0),
    (34, 6, 'STRING', 'action_label', 2, 0, NULL, 64, 0, 0),
    (35, 6, 'STRING', 'action_description', 3, 1, NULL, 1024, 0, 0),
    (36, 7, 'INT64', 'recid', 1, 0, NULL, NULL, 1, 0),
    (37, 7, 'UUID', 'users_guid', 2, 0, NULL, NULL, 0, 0),
    (38, 7, 'INT32', 'types_recid', 3, 0, NULL, NULL, 0, 0),
    (39, 7, 'STRING', 'element_path', 4, 0, NULL, 512, 0, 0),
    (40, 7, 'STRING', 'element_filename', 5, 0, NULL, 255, 0, 0),
    (41, 7, 'BOOL', 'element_public', 6, 0, '((0))', NULL, 0, 0),
    (42, 7, 'DATETIME', 'element_created_on', 7, 0, '(sysutcdatetime())', NULL, 0, 0),
    (43, 7, 'DATETIME', 'element_modified_on', 8, 1, NULL, NULL, 0, 0),
    (44, 7, 'BOOL', 'element_deleted', 9, 0, '((0))', NULL, 0, 0),
    (45, 7, 'STRING', 'element_url', 10, 1, NULL, 1024, 0, 0),
    (46, 7, 'BOOL', 'element_reported', 11, 0, '((0))', NULL, 0, 0),
    (47, 7, 'INT32', 'moderation_recid', 12, 1, NULL, NULL, 0, 0),
    (48, 8, 'INT32', 'recid', 1, 0, NULL, NULL, 1, 0),
    (49, 8, 'INT32', 'element_sequence', 2, 0, '((0))', NULL, 0, 0),
    (50, 8, 'TEXT', 'element_title', 3, 1, NULL, NULL, 0, 0),
    (51, 8, 'TEXT', 'element_url', 4, 1, NULL, NULL, 0, 0),
    (52, 9, 'INT32', 'recid', 1, 0, NULL, NULL, 1, 0),
    (53, 9, 'STRING', 'element_enablement', 2, 0, '(''0'')', 1, 0, 0),
    (54, 9, 'INT64', 'element_roles', 3, 0, '((0))', NULL, 0, 0),
    (55, 9, 'INT32', 'element_sequence', 4, 0, '((0))', NULL, 0, 0),
    (56, 9, 'STRING', 'element_path', 5, 1, NULL, 512, 0, 0),
    (57, 9, 'STRING', 'element_name', 6, 1, NULL, 256, 0, 0),
    (58, 9, 'STRING', 'element_icon', 7, 1, NULL, 256, 0, 0),
    (59, 10, 'INT32', 'recid', 1, 0, NULL, NULL, 1, 0),
    (60, 10, 'STRING', 'element_key', 2, 1, NULL, 1024, 0, 0),
    (61, 10, 'TEXT', 'element_value', 3, 1, NULL, NULL, 0, 0),
    (62, 11, 'UUID', 'users_guid', 1, 0, NULL, NULL, 1, 0),
    (63, 11, 'INT32', 'element_credits', 2, 0, NULL, NULL, 0, 0),
    (64, 11, 'INT32', 'element_reserve', 3, 1, NULL, NULL, 0, 0),
    (65, 11, 'DATETIME_TZ', 'created_on', 4, 0, '(sysutcdatetime())', NULL, 0, 0),
    (66, 11, 'DATETIME_TZ', 'modified_on', 5, 0, '(sysutcdatetime())', NULL, 0, 0),
    (67, 12, 'UUID', 'users_guid', 1, 0, NULL, NULL, 1, 0),
    (68, 12, 'TEXT', 'element_enablements', 2, 0, '(''0'')', NULL, 0, 0),
    (69, 12, 'DATETIME_TZ', 'created_on', 3, 0, '(sysutcdatetime())', NULL, 0, 0),
    (70, 12, 'DATETIME_TZ', 'modified_on', 4, 0, '(sysutcdatetime())', NULL, 0, 0),
    (71, 13, 'UUID', 'users_guid', 1, 0, NULL, NULL, 0, 0),
    (72, 13, 'TEXT', 'element_base64', 2, 1, NULL, NULL, 0, 0),
    (73, 13, 'INT32', 'providers_recid', 3, 0, NULL, NULL, 0, 0),
    (74, 13, 'DATETIME_TZ', 'created_on', 4, 0, '(sysutcdatetime())', NULL, 0, 0),
    (75, 13, 'DATETIME_TZ', 'modified_on', 5, 0, '(sysutcdatetime())', NULL, 0, 0),
    (76, 14, 'UUID', 'users_guid', 1, 0, NULL, NULL, 1, 0),
    (77, 14, 'INT64', 'element_roles', 2, 0, '((0))', NULL, 0, 0),
    (78, 14, 'DATETIME_TZ', 'created_on', 3, 0, '(sysutcdatetime())', NULL, 0, 0),
    (79, 14, 'DATETIME_TZ', 'modified_on', 4, 0, '(sysutcdatetime())', NULL, 0, 0),
    (80, 15, 'INT32', 'recid', 1, 0, NULL, NULL, 1, 0),
    (81, 15, 'INT64', 'element_mask', 2, 0, '((0))', NULL, 0, 0),
    (82, 15, 'STRING', 'element_enablement', 3, 0, '(''0'')', 1, 0, 0),
    (83, 15, 'STRING', 'element_name', 4, 0, NULL, 1024, 0, 0),
    (84, 15, 'STRING', 'element_display', 5, 1, NULL, 1024, 0, 0),
    (85, 16, 'INT64_IDENTITY', 'recid', 1, 0, NULL, NULL, 1, 1),
    (86, 16, 'STRING', 'element_guild_id', 2, 0, NULL, 64, 0, 0),
    (87, 16, 'STRING', 'element_name', 3, 0, NULL, 256, 0, 0),
    (88, 16, 'DATETIME_TZ', 'element_joined_on', 4, 0, '(sysutcdatetime())', NULL, 0, 0),
    (89, 16, 'INT32', 'element_member_count', 5, 1, NULL, NULL, 0, 0),
    (90, 16, 'STRING', 'element_owner_id', 6, 1, NULL, 64, 0, 0),
    (91, 16, 'STRING', 'element_region', 7, 1, NULL, 128, 0, 0),
    (92, 16, 'DATETIME_TZ', 'element_left_on', 8, 1, NULL, NULL, 0, 0),
    (93, 16, 'TEXT', 'element_notes', 9, 1, NULL, NULL, 0, 0),
    (94, 17, 'UUID', 'element_guid', 1, 0, NULL, NULL, 1, 0),
    (95, 17, 'UUID', 'sessions_guid', 2, 0, NULL, NULL, 0, 0),
    (96, 17, 'TEXT', 'element_token', 3, 0, NULL, NULL, 0, 0),
    (97, 17, 'DATETIME_TZ', 'element_token_iat', 4, 0, '(sysdatetimeoffset())', NULL, 0, 0),
    (98, 17, 'DATETIME_TZ', 'element_token_exp', 5, 0, '(sysutcdatetime())', NULL, 0, 0),
    (99, 17, 'STRING', 'element_device_fingerprint', 6, 1, NULL, 512, 0, 0),
    (100, 17, 'STRING', 'element_user_agent', 7, 1, NULL, 1024, 0, 0),
    (101, 17, 'STRING', 'element_ip_last_seen', 8, 1, NULL, 64, 0, 0),
    (102, 17, 'DATETIME_TZ', 'element_revoked_at', 9, 1, NULL, NULL, 0, 0),
    (103, 17, 'INT32', 'providers_recid', 10, 0, '((0))', NULL, 0, 0),
    (104, 17, 'DATETIME', 'element_created_on', 11, 0, '(sysutcdatetime())', NULL, 0, 0),
    (105, 17, 'DATETIME', 'element_modified_on', 12, 0, '(sysutcdatetime())', NULL, 0, 0),
    (106, 18, 'INT64', 'recid', 1, 0, NULL, NULL, 1, 0),
    (107, 18, 'UUID', 'users_guid', 2, 0, NULL, NULL, 0, 0),
    (108, 18, 'INT32', 'action_recid', 3, 0, NULL, NULL, 0, 0),
    (109, 18, 'STRING', 'element_url', 4, 1, NULL, 1024, 0, 0),
    (110, 18, 'DATETIME', 'element_logged_on', 5, 0, '(sysutcdatetime())', NULL, 0, 0),
    (111, 18, 'STRING', 'element_notes', 6, 1, NULL, 1024, 0, 0),
    (112, 19, 'INT64', 'recid', 1, 0, NULL, NULL, 1, 0),
    (113, 19, 'STRING', 'element_name', 2, 0, NULL, 50, 0, 0),
    (114, 20, 'INT64', 'recid', 1, 0, NULL, NULL, 1, 0),
    (115, 20, 'STRING', 'element_name', 2, 0, NULL, 256, 0, 0),
    (116, 20, 'TEXT', 'element_metadata', 3, 1, NULL, NULL, 0, 0),
    (117, 20, 'DATETIME_TZ', 'element_created_on', 4, 0, '(sysutcdatetime())', NULL, 0, 0),
    (118, 20, 'DATETIME_TZ', 'element_modified_on', 5, 0, '(sysutcdatetime())', NULL, 0, 0),
    (119, 20, 'INT32', 'element_tokens', 6, 0, NULL, NULL, 0, 0),
    (120, 20, 'TEXT', 'element_prompt', 7, 0, NULL, NULL, 0, 0),
    (121, 20, 'INT64', 'models_recid', 8, 0, NULL, NULL, 0, 0),
    (122, 21, 'INT64', 'recid', 1, 0, NULL, NULL, 1, 0),
    (123, 21, 'INT64', 'personas_recid', 2, 0, NULL, NULL, 0, 0),
    (124, 21, 'STRING', 'element_guild_id', 3, 1, NULL, 64, 0, 0),
    (125, 21, 'STRING', 'element_channel_id', 4, 1, NULL, 64, 0, 0),
    (126, 21, 'TEXT', 'element_input', 5, 1, NULL, NULL, 0, 0),
    (127, 21, 'TEXT', 'element_output', 6, 1, NULL, NULL, 0, 0),
    (128, 21, 'DATETIME_TZ', 'element_created_on', 7, 0, '(sysutcdatetime())', NULL, 0, 0),
    (129, 21, 'INT32', 'element_tokens', 8, 1, NULL, NULL, 0, 0),
    (130, 21, 'STRING', 'element_user_id', 9, 1, NULL, 64, 0, 0),
    (131, 21, 'INT64', 'models_recid', 10, 0, NULL, NULL, 0, 0),
    (132, 22, 'INT64', 'recid', 1, 0, NULL, NULL, 1, 0),
    (133, 22, 'STRING', 'element_route_name', 2, 0, NULL, 200, 0, 0),
    (134, 22, 'TEXT', 'element_pageblob', 3, 0, NULL, NULL, 0, 0),
    (135, 22, 'INT32', 'element_version', 4, 0, '((1))', NULL, 0, 0),
    (136, 22, 'DATETIME', 'element_created_on', 5, 0, '(sysutcdatetime())', NULL, 0, 0),
    (137, 22, 'DATETIME', 'element_modified_on', 6, 0, '(sysutcdatetime())', NULL, 0, 0),
    (138, 22, 'UUID', 'element_created_by', 7, 0, NULL, NULL, 0, 0),
    (139, 22, 'UUID', 'element_modified_by', 8, 0, NULL, NULL, 0, 0),
    (140, 22, 'BOOL', 'element_is_active', 9, 0, '((1))', NULL, 0, 0),
    (141, 23, 'INT64', 'recid', 1, 0, NULL, NULL, 1, 0),
    (142, 23, 'STRING', 'element_name', 2, 0, NULL, 64, 0, 0),
    (143, 23, 'STRING', 'element_mssql_type', 3, 0, NULL, 128, 0, 0),
    (144, 23, 'STRING', 'element_postgresql_type', 4, 0, NULL, 128, 0, 0),
    (145, 23, 'STRING', 'element_mysql_type', 5, 0, NULL, 128, 0, 0),
    (146, 23, 'STRING', 'element_python_type', 6, 0, NULL, 64, 0, 0),
    (147, 23, 'INT32', 'element_odbc_type_code', 7, 0, NULL, NULL, 0, 0),
    (148, 23, 'INT32', 'element_max_length', 8, 1, NULL, NULL, 0, 0),
    (149, 23, 'STRING', 'element_notes', 9, 1, NULL, 2048, 0, 0),
    (150, 23, 'DATETIME_TZ', 'element_created_on', 10, 0, '(sysutcdatetime())', NULL, 0, 0),
    (151, 23, 'DATETIME_TZ', 'element_modified_on', 11, 0, '(sysutcdatetime())', NULL, 0, 0),
    (152, 24, 'INT64', 'recid', 1, 0, NULL, NULL, 1, 0),
    (153, 24, 'STRING', 'element_name', 2, 0, NULL, 128, 0, 0),
    (154, 24, 'STRING', 'element_schema', 3, 0, '(''dbo'')', 64, 0, 0),
    (155, 24, 'STRING', 'element_description', 4, 1, NULL, 1024, 0, 0),
    (156, 24, 'DATETIME_TZ', 'element_created_on', 5, 0, '(sysutcdatetime())', NULL, 0, 0),
    (157, 24, 'DATETIME_TZ', 'element_modified_on', 6, 0, '(sysutcdatetime())', NULL, 0, 0),
    (158, 25, 'INT64', 'recid', 1, 0, NULL, NULL, 1, 0),
    (159, 25, 'INT64', 'tables_recid', 2, 0, NULL, NULL, 0, 0),
    (160, 25, 'INT64', 'edt_recid', 3, 0, NULL, NULL, 0, 0),
    (161, 25, 'STRING', 'element_name', 4, 0, NULL, 128, 0, 0),
    (162, 25, 'INT32', 'element_ordinal', 5, 0, NULL, NULL, 0, 0),
    (163, 25, 'BOOL', 'element_nullable', 6, 0, '((0))', NULL, 0, 0),
    (164, 25, 'STRING', 'element_default', 7, 1, NULL, 512, 0, 0),
    (165, 25, 'INT32', 'element_max_length', 8, 1, NULL, NULL, 0, 0),
    (166, 25, 'BOOL', 'element_is_primary_key', 9, 0, '((0))', NULL, 0, 0),
    (167, 25, 'BOOL', 'element_is_identity', 10, 0, '((0))', NULL, 0, 0),
    (168, 25, 'STRING', 'element_description', 11, 1, NULL, 1024, 0, 0),
    (169, 25, 'DATETIME_TZ', 'element_created_on', 12, 0, '(sysutcdatetime())', NULL, 0, 0),
    (170, 25, 'DATETIME_TZ', 'element_modified_on', 13, 0, '(sysutcdatetime())', NULL, 0, 0),
    (171, 26, 'INT64', 'recid', 1, 0, NULL, NULL, 1, 0),
    (172, 26, 'INT64', 'tables_recid', 2, 0, NULL, NULL, 0, 0),
    (173, 26, 'STRING', 'element_name', 3, 0, NULL, 256, 0, 0),
    (174, 26, 'STRING', 'element_columns', 4, 0, NULL, 1024, 0, 0),
    (175, 26, 'BOOL', 'element_is_unique', 5, 0, '((0))', NULL, 0, 0),
    (176, 26, 'DATETIME_TZ', 'element_created_on', 6, 0, '(sysutcdatetime())', NULL, 0, 0),
    (177, 26, 'DATETIME_TZ', 'element_modified_on', 7, 0, '(sysutcdatetime())', NULL, 0, 0),
    (178, 27, 'INT64', 'recid', 1, 0, NULL, NULL, 1, 0),
    (179, 27, 'INT64', 'tables_recid', 2, 0, NULL, NULL, 0, 0),
    (180, 27, 'STRING', 'element_column_name', 3, 0, NULL, 128, 0, 0),
    (181, 27, 'INT64', 'referenced_tables_recid', 4, 0, NULL, NULL, 0, 0),
    (182, 27, 'STRING', 'element_referenced_column', 5, 0, NULL, 128, 0, 0),
    (183, 27, 'DATETIME_TZ', 'element_created_on', 6, 0, '(sysutcdatetime())', NULL, 0, 0),
    (184, 27, 'DATETIME_TZ', 'element_modified_on', 7, 0, '(sysutcdatetime())', NULL, 0, 0)
) AS raw_source (recid, tables_recid, edt_name, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
JOIN dbo.system_edt_mappings AS edt ON edt.element_name = raw_source.edt_name
) AS source
ON target.recid = source.recid
WHEN MATCHED THEN
  UPDATE SET
    tables_recid = source.tables_recid,
    edt_recid = source.edt_recid,
    element_name = source.element_name,
    element_ordinal = source.element_ordinal,
    element_nullable = source.element_nullable,
    element_default = source.element_default,
    element_max_length = source.element_max_length,
    element_is_primary_key = source.element_is_primary_key,
    element_is_identity = source.element_is_identity,
    element_modified_on = sysutcdatetime()
WHEN NOT MATCHED BY TARGET THEN
  INSERT (recid, tables_recid, edt_recid, element_name, element_ordinal, element_nullable, element_default, element_max_length, element_is_primary_key, element_is_identity)
  VALUES (source.recid, source.tables_recid, source.edt_recid, source.element_name, source.element_ordinal, source.element_nullable, source.element_default, source.element_max_length, source.element_is_primary_key, source.element_is_identity);

MERGE dbo.system_schema_indexes AS target
USING (
  VALUES
    (1, 2, 'UQ__account___D23E50605BA10A17', 'element_guid', 0),
    (2, 4, 'UQ__element___2647B0A5A8CD3589', 'element_mimetype', 0),
    (3, 5, 'UQ_users_auth_element_identifier', 'element_identifier', 0),
    (4, 6, 'UQ__account___83A9315D3DCF8A1B', 'action_label', 0),
    (5, 7, 'UQ_users_storage_cache', 'users_guid,element_path,element_filename', 0),
    (6, 23, 'UQ_system_edt_mappings_name', 'element_name', 1),
    (7, 16, 'UQ__discord_guilds__guild_id', 'element_guild_id', 1),
    (8, 22, 'UQ__service___BD1501E83FFF3970', 'element_route_name', 0),
    (9, 24, 'UQ_system_schema_tables_schema_name', 'element_schema,element_name', 1),
    (10, 25, 'UQ_system_schema_columns_table_column', 'tables_recid,element_name', 1),
    (11, 25, 'IX_system_schema_columns_table_ordinal', 'tables_recid,element_ordinal', 0),
    (12, 26, 'UQ_system_schema_indexes_table_name', 'tables_recid,element_name', 1),
    (13, 27, 'UQ_system_schema_foreign_keys_table_column', 'tables_recid,element_column_name', 1)
) AS source (recid, tables_recid, element_name, element_columns, element_is_unique)
ON target.recid = source.recid
WHEN MATCHED THEN
  UPDATE SET
    tables_recid = source.tables_recid,
    element_name = source.element_name,
    element_columns = source.element_columns,
    element_is_unique = source.element_is_unique,
    element_modified_on = sysutcdatetime()
WHEN NOT MATCHED BY TARGET THEN
  INSERT (recid, tables_recid, element_name, element_columns, element_is_unique)
  VALUES (source.recid, source.tables_recid, source.element_name, source.element_columns, source.element_is_unique);

MERGE dbo.system_schema_foreign_keys AS target
USING (
  VALUES
    (1, 2, 'providers_recid', 1, 'recid'),
    (2, 3, 'users_guid', 2, 'element_guid'),
    (3, 5, 'providers_recid', 1, 'recid'),
    (4, 5, 'users_guid', 2, 'element_guid'),
    (5, 7, 'moderation_recid', 6, 'recid'),
    (6, 7, 'users_guid', 2, 'element_guid'),
    (7, 7, 'types_recid', 4, 'recid'),
    (8, 11, 'users_guid', 2, 'element_guid'),
    (9, 12, 'users_guid', 2, 'element_guid'),
    (10, 13, 'providers_recid', 1, 'recid'),
    (11, 13, 'users_guid', 2, 'element_guid'),
    (12, 14, 'users_guid', 2, 'element_guid'),
    (13, 17, 'providers_recid', 1, 'recid'),
    (14, 17, 'sessions_guid', 3, 'element_guid'),
    (15, 18, 'action_recid', 6, 'recid'),
    (16, 18, 'users_guid', 2, 'element_guid'),
    (17, 20, 'models_recid', 19, 'recid'),
    (18, 21, 'models_recid', 19, 'recid'),
    (19, 21, 'personas_recid', 20, 'recid'),
    (20, 22, 'element_created_by', 2, 'element_guid'),
    (21, 22, 'element_modified_by', 2, 'element_guid'),
    (22, 25, 'edt_recid', 23, 'recid'),
    (23, 25, 'tables_recid', 24, 'recid'),
    (24, 26, 'tables_recid', 24, 'recid'),
    (25, 27, 'referenced_tables_recid', 24, 'recid'),
    (26, 27, 'tables_recid', 24, 'recid')
) AS source (recid, tables_recid, element_column_name, referenced_tables_recid, element_referenced_column)
ON target.recid = source.recid
WHEN MATCHED THEN
  UPDATE SET
    tables_recid = source.tables_recid,
    element_column_name = source.element_column_name,
    referenced_tables_recid = source.referenced_tables_recid,
    element_referenced_column = source.element_referenced_column,
    element_modified_on = sysutcdatetime()
WHEN NOT MATCHED BY TARGET THEN
  INSERT (recid, tables_recid, element_column_name, referenced_tables_recid, element_referenced_column)
  VALUES (source.recid, source.tables_recid, source.element_column_name, source.referenced_tables_recid, source.element_referenced_column);
