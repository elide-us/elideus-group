ALTER TABLE assistant_conversations ADD element_role NVARCHAR(16) NOT NULL DEFAULT 'user';
ALTER TABLE assistant_conversations ADD element_content NVARCHAR(MAX) NULL;
ALTER TABLE assistant_conversations ADD element_thread_id NVARCHAR(64) NULL;
ALTER TABLE assistant_conversations ADD users_guid UNIQUEIDENTIFIER NULL;
ALTER TABLE assistant_conversations ADD element_modified_on DATETIMEOFFSET(7) NOT NULL DEFAULT (SYSUTCDATETIME());
GO

ALTER TABLE assistant_conversations ADD CONSTRAINT FK_assistant_conversations_users
  FOREIGN KEY (users_guid) REFERENCES account_users(element_guid);
GO

CREATE NONCLUSTERED INDEX IX_assistant_conversations_thread
  ON assistant_conversations (element_thread_id, element_created_on)
  WHERE element_thread_id IS NOT NULL;
GO

CREATE NONCLUSTERED INDEX IX_assistant_conversations_persona_time
  ON assistant_conversations (personas_recid, element_created_on);
GO

CREATE NONCLUSTERED INDEX IX_assistant_conversations_guild_channel
  ON assistant_conversations (element_guild_id, element_channel_id, element_created_on)
  WHERE element_guild_id IS NOT NULL;
GO

ALTER TABLE discord_guilds ADD element_credits INT NOT NULL DEFAULT 0;
GO

ALTER TABLE assistant_personas ADD element_is_active BIT NOT NULL DEFAULT 1;
GO

CREATE TABLE [dbo].[discord_channels] (
  [recid] BIGINT IDENTITY(1,1) NOT NULL,
  [guilds_recid] BIGINT NOT NULL,
  [element_channel_id] NVARCHAR(64) NOT NULL,
  [element_name] NVARCHAR(256) NULL,
  [element_type] NVARCHAR(32) NULL,
  [element_message_count] BIGINT NOT NULL DEFAULT 0,
  [element_last_activity_on] DATETIMEOFFSET(7) NULL,
  [element_created_on] DATETIMEOFFSET(7) NOT NULL DEFAULT (SYSUTCDATETIME()),
  [element_modified_on] DATETIMEOFFSET(7) NOT NULL DEFAULT (SYSUTCDATETIME()),
  [element_notes] NVARCHAR(MAX) NULL,
  CONSTRAINT [PK_discord_channels] PRIMARY KEY ([recid]),
  CONSTRAINT [FK_discord_channels_guilds] FOREIGN KEY ([guilds_recid]) REFERENCES [discord_guilds]([recid]),
  CONSTRAINT [UQ_discord_channels_channel_id] UNIQUE ([element_channel_id])
);
GO

CREATE NONCLUSTERED INDEX IX_discord_channels_guild
  ON discord_channels (guilds_recid);
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'UQ_discord_guilds_guild_id')
BEGIN
  CREATE UNIQUE NONCLUSTERED INDEX UQ_discord_guilds_guild_id
    ON discord_guilds (element_guild_id);
END
GO

-- ============================================================================
-- REFLECTION TABLE UPDATES
-- ============================================================================

-- Register new table
INSERT INTO system_schema_tables (element_name, element_schema) VALUES
  ('discord_channels', 'dbo');
GO

-- New columns on assistant_conversations (ordinals 11-15)
INSERT INTO system_schema_columns (
  tables_recid, edt_recid, element_name, element_ordinal, element_nullable,
  element_default, element_max_length, element_is_primary_key, element_is_identity
) VALUES
  ((SELECT recid FROM system_schema_tables WHERE element_name = 'assistant_conversations' AND element_schema = 'dbo'), (SELECT recid FROM system_edt_mappings WHERE element_name = 'STRING'), 'element_role', 11, 0, '''user''', 16, 0, 0),
  ((SELECT recid FROM system_schema_tables WHERE element_name = 'assistant_conversations' AND element_schema = 'dbo'), (SELECT recid FROM system_edt_mappings WHERE element_name = 'TEXT'), 'element_content', 12, 1, NULL, NULL, 0, 0),
  ((SELECT recid FROM system_schema_tables WHERE element_name = 'assistant_conversations' AND element_schema = 'dbo'), (SELECT recid FROM system_edt_mappings WHERE element_name = 'STRING'), 'element_thread_id', 13, 1, NULL, 64, 0, 0),
  ((SELECT recid FROM system_schema_tables WHERE element_name = 'assistant_conversations' AND element_schema = 'dbo'), (SELECT recid FROM system_edt_mappings WHERE element_name = 'UUID'), 'users_guid', 14, 1, NULL, NULL, 0, 0),
  ((SELECT recid FROM system_schema_tables WHERE element_name = 'assistant_conversations' AND element_schema = 'dbo'), (SELECT recid FROM system_edt_mappings WHERE element_name = 'DATETIME_TZ'), 'element_modified_on', 15, 0, '(sysutcdatetime())', NULL, 0, 0);
GO

-- New column on discord_guilds (ordinal 10)
INSERT INTO system_schema_columns (
  tables_recid, edt_recid, element_name, element_ordinal, element_nullable,
  element_default, element_max_length, element_is_primary_key, element_is_identity
) VALUES
  ((SELECT recid FROM system_schema_tables WHERE element_name = 'discord_guilds' AND element_schema = 'dbo'), (SELECT recid FROM system_edt_mappings WHERE element_name = 'INT32'), 'element_credits', 10, 0, '((0))', NULL, 0, 0);
GO

-- New column on assistant_personas (ordinal 9)
INSERT INTO system_schema_columns (
  tables_recid, edt_recid, element_name, element_ordinal, element_nullable,
  element_default, element_max_length, element_is_primary_key, element_is_identity
) VALUES
  ((SELECT recid FROM system_schema_tables WHERE element_name = 'assistant_personas' AND element_schema = 'dbo'), (SELECT recid FROM system_edt_mappings WHERE element_name = 'BOOL'), 'element_is_active', 9, 0, '((1))', NULL, 0, 0);
GO

-- All columns for discord_channels (ordinals 1-10)
INSERT INTO system_schema_columns (
  tables_recid, edt_recid, element_name, element_ordinal, element_nullable,
  element_default, element_max_length, element_is_primary_key, element_is_identity
) VALUES
  ((SELECT recid FROM system_schema_tables WHERE element_name = 'discord_channels' AND element_schema = 'dbo'), (SELECT recid FROM system_edt_mappings WHERE element_name = 'INT64_IDENTITY'), 'recid', 1, 0, NULL, NULL, 1, 1),
  ((SELECT recid FROM system_schema_tables WHERE element_name = 'discord_channels' AND element_schema = 'dbo'), (SELECT recid FROM system_edt_mappings WHERE element_name = 'INT64'), 'guilds_recid', 2, 0, NULL, NULL, 0, 0),
  ((SELECT recid FROM system_schema_tables WHERE element_name = 'discord_channels' AND element_schema = 'dbo'), (SELECT recid FROM system_edt_mappings WHERE element_name = 'STRING'), 'element_channel_id', 3, 0, NULL, 64, 0, 0),
  ((SELECT recid FROM system_schema_tables WHERE element_name = 'discord_channels' AND element_schema = 'dbo'), (SELECT recid FROM system_edt_mappings WHERE element_name = 'STRING'), 'element_name', 4, 1, NULL, 256, 0, 0),
  ((SELECT recid FROM system_schema_tables WHERE element_name = 'discord_channels' AND element_schema = 'dbo'), (SELECT recid FROM system_edt_mappings WHERE element_name = 'STRING'), 'element_type', 5, 1, NULL, 32, 0, 0),
  ((SELECT recid FROM system_schema_tables WHERE element_name = 'discord_channels' AND element_schema = 'dbo'), (SELECT recid FROM system_edt_mappings WHERE element_name = 'INT64'), 'element_message_count', 6, 0, '((0))', NULL, 0, 0),
  ((SELECT recid FROM system_schema_tables WHERE element_name = 'discord_channels' AND element_schema = 'dbo'), (SELECT recid FROM system_edt_mappings WHERE element_name = 'DATETIME_TZ'), 'element_last_activity_on', 7, 1, NULL, NULL, 0, 0),
  ((SELECT recid FROM system_schema_tables WHERE element_name = 'discord_channels' AND element_schema = 'dbo'), (SELECT recid FROM system_edt_mappings WHERE element_name = 'DATETIME_TZ'), 'element_created_on', 8, 0, '(sysutcdatetime())', NULL, 0, 0),
  ((SELECT recid FROM system_schema_tables WHERE element_name = 'discord_channels' AND element_schema = 'dbo'), (SELECT recid FROM system_edt_mappings WHERE element_name = 'DATETIME_TZ'), 'element_modified_on', 9, 0, '(sysutcdatetime())', NULL, 0, 0),
  ((SELECT recid FROM system_schema_tables WHERE element_name = 'discord_channels' AND element_schema = 'dbo'), (SELECT recid FROM system_edt_mappings WHERE element_name = 'TEXT'), 'element_notes', 10, 1, NULL, NULL, 0, 0);
GO

-- New indexes
INSERT INTO system_schema_indexes (
  tables_recid, element_name, element_columns, element_is_unique
) VALUES
  ((SELECT recid FROM system_schema_tables WHERE element_name = 'assistant_conversations' AND element_schema = 'dbo'), 'IX_assistant_conversations_thread', 'element_thread_id, element_created_on', 0),
  ((SELECT recid FROM system_schema_tables WHERE element_name = 'assistant_conversations' AND element_schema = 'dbo'), 'IX_assistant_conversations_persona_time', 'personas_recid, element_created_on', 0),
  ((SELECT recid FROM system_schema_tables WHERE element_name = 'assistant_conversations' AND element_schema = 'dbo'), 'IX_assistant_conversations_guild_channel', 'element_guild_id, element_channel_id, element_created_on', 0),
  ((SELECT recid FROM system_schema_tables WHERE element_name = 'discord_channels' AND element_schema = 'dbo'), 'IX_discord_channels_guild', 'guilds_recid', 0),
  ((SELECT recid FROM system_schema_tables WHERE element_name = 'discord_guilds' AND element_schema = 'dbo'), 'UQ_discord_guilds_guild_id', 'element_guild_id', 1);
GO

-- New foreign keys
INSERT INTO system_schema_foreign_keys (
  tables_recid, element_column_name, referenced_tables_recid, element_referenced_column
) VALUES
  ((SELECT recid FROM system_schema_tables WHERE element_name = 'assistant_conversations' AND element_schema = 'dbo'), 'users_guid', (SELECT recid FROM system_schema_tables WHERE element_name = 'account_users' AND element_schema = 'dbo'), 'element_guid'),
  ((SELECT recid FROM system_schema_tables WHERE element_name = 'discord_channels' AND element_schema = 'dbo'), 'guilds_recid', (SELECT recid FROM system_schema_tables WHERE element_name = 'discord_guilds' AND element_schema = 'dbo'), 'recid');
GO
