-- ============================================================================
-- v0.10.1.0 — Migrate account_users PK from recid to element_guid
-- ============================================================================
-- This migration:
--   1. Converts account_api_tokens.users_recid → users_guid (uniqueidentifier)
--   2. Converts account_mcp_agents.users_recid → users_guid (uniqueidentifier)
--   3. Converts account_mcp_auth_codes.users_recid → users_guid (uniqueidentifier)
--   4. Drops account_users.recid, promotes element_guid to PK
--
-- Prerequisites: Backup databases before running.
-- ============================================================================

SET XACT_ABORT ON;
BEGIN TRANSACTION;

-- ============================================================================
-- PHASE 1: Add users_guid columns to downstream tables, backfill from JOIN
-- ============================================================================

-- 1a. account_api_tokens
IF NOT EXISTS (
  SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS
  WHERE TABLE_NAME = 'account_api_tokens' AND COLUMN_NAME = 'users_guid'
)
BEGIN
  ALTER TABLE dbo.account_api_tokens ADD users_guid uniqueidentifier NULL;
END;

UPDATE t
SET t.users_guid = au.element_guid
FROM dbo.account_api_tokens t
JOIN dbo.account_users au ON au.recid = t.users_recid
WHERE t.users_guid IS NULL;

-- 1b. account_mcp_agents
IF NOT EXISTS (
  SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS
  WHERE TABLE_NAME = 'account_mcp_agents' AND COLUMN_NAME = 'users_guid'
)
BEGIN
  ALTER TABLE dbo.account_mcp_agents ADD users_guid uniqueidentifier NULL;
END;

UPDATE t
SET t.users_guid = au.element_guid
FROM dbo.account_mcp_agents t
JOIN dbo.account_users au ON au.recid = t.users_recid
WHERE t.users_guid IS NULL AND t.users_recid IS NOT NULL;

-- 1c. account_mcp_auth_codes
IF NOT EXISTS (
  SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS
  WHERE TABLE_NAME = 'account_mcp_auth_codes' AND COLUMN_NAME = 'users_guid'
)
BEGIN
  ALTER TABLE dbo.account_mcp_auth_codes ADD users_guid uniqueidentifier NULL;
END;

UPDATE t
SET t.users_guid = au.element_guid
FROM dbo.account_mcp_auth_codes t
JOIN dbo.account_users au ON au.recid = t.users_recid
WHERE t.users_guid IS NULL;

-- ============================================================================
-- PHASE 2: Drop old FK constraints referencing account_users.recid
-- ============================================================================

-- account_api_tokens → account_users.recid
DECLARE @fk_api_tokens NVARCHAR(256);
SELECT @fk_api_tokens = fk.name
FROM sys.foreign_keys fk
JOIN sys.foreign_key_columns fkc ON fk.object_id = fkc.constraint_object_id
JOIN sys.columns c ON fkc.parent_object_id = c.object_id AND fkc.parent_column_id = c.column_id
WHERE OBJECT_NAME(fk.parent_object_id) = 'account_api_tokens'
  AND c.name = 'users_recid';

IF @fk_api_tokens IS NOT NULL
  EXEC('ALTER TABLE dbo.account_api_tokens DROP CONSTRAINT [' + @fk_api_tokens + '];');

-- account_mcp_agents → account_users.recid
DECLARE @fk_mcp_agents NVARCHAR(256);
SELECT @fk_mcp_agents = fk.name
FROM sys.foreign_keys fk
JOIN sys.foreign_key_columns fkc ON fk.object_id = fkc.constraint_object_id
JOIN sys.columns c ON fkc.parent_object_id = c.object_id AND fkc.parent_column_id = c.column_id
WHERE OBJECT_NAME(fk.parent_object_id) = 'account_mcp_agents'
  AND c.name = 'users_recid';

IF @fk_mcp_agents IS NOT NULL
  EXEC('ALTER TABLE dbo.account_mcp_agents DROP CONSTRAINT [' + @fk_mcp_agents + '];');

-- account_mcp_auth_codes → account_users.recid
DECLARE @fk_mcp_auth_codes NVARCHAR(256);
SELECT @fk_mcp_auth_codes = fk.name
FROM sys.foreign_keys fk
JOIN sys.foreign_key_columns fkc ON fk.object_id = fkc.constraint_object_id
JOIN sys.columns c ON fkc.parent_object_id = c.object_id AND fkc.parent_column_id = c.column_id
WHERE OBJECT_NAME(fk.parent_object_id) = 'account_mcp_auth_codes'
  AND c.name = 'users_recid';

IF @fk_mcp_auth_codes IS NOT NULL
  EXEC('ALTER TABLE dbo.account_mcp_auth_codes DROP CONSTRAINT [' + @fk_mcp_auth_codes + '];');

-- ============================================================================
-- PHASE 3: Drop old index on account_mcp_agents.users_recid
-- ============================================================================

IF EXISTS (
  SELECT 1 FROM sys.indexes
  WHERE name = 'IX_account_mcp_agents_users'
    AND object_id = OBJECT_ID('dbo.account_mcp_agents')
)
  DROP INDEX IX_account_mcp_agents_users ON dbo.account_mcp_agents;

-- ============================================================================
-- PHASE 4: Drop old users_recid columns
-- ============================================================================

-- Check all backfills succeeded (no NULLs in non-nullable scenarios)
IF EXISTS (
  SELECT 1 FROM dbo.account_api_tokens WHERE users_guid IS NULL
)
BEGIN
  RAISERROR('ABORT: account_api_tokens has NULL users_guid after backfill.', 16, 1);
  ROLLBACK TRANSACTION;
  RETURN;
END;

IF EXISTS (
  SELECT 1 FROM dbo.account_mcp_auth_codes WHERE users_guid IS NULL
)
BEGIN
  RAISERROR('ABORT: account_mcp_auth_codes has NULL users_guid after backfill.', 16, 1);
  ROLLBACK TRANSACTION;
  RETURN;
END;

-- Make users_guid NOT NULL where the old column was NOT NULL
ALTER TABLE dbo.account_api_tokens ALTER COLUMN users_guid uniqueidentifier NOT NULL;
ALTER TABLE dbo.account_mcp_auth_codes ALTER COLUMN users_guid uniqueidentifier NOT NULL;
-- account_mcp_agents.users_guid stays nullable (original users_recid was nullable)

-- Drop old columns
IF EXISTS (
  SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS
  WHERE TABLE_NAME = 'account_api_tokens' AND COLUMN_NAME = 'users_recid'
)
  ALTER TABLE dbo.account_api_tokens DROP COLUMN users_recid;

IF EXISTS (
  SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS
  WHERE TABLE_NAME = 'account_mcp_agents' AND COLUMN_NAME = 'users_recid'
)
  ALTER TABLE dbo.account_mcp_agents DROP COLUMN users_recid;

IF EXISTS (
  SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS
  WHERE TABLE_NAME = 'account_mcp_auth_codes' AND COLUMN_NAME = 'users_recid'
)
  ALTER TABLE dbo.account_mcp_auth_codes DROP COLUMN users_recid;

-- ============================================================================
-- PHASE 5: Promote account_users.element_guid to PK, drop recid
-- ============================================================================

-- 5a. Drop all remaining FKs that reference account_users.recid
-- (The three we handled above should be the only ones, but sweep to be safe)
DECLARE @fk_remaining NVARCHAR(256);
DECLARE @fk_parent_table NVARCHAR(256);
DECLARE fk_cursor CURSOR LOCAL FAST_FORWARD FOR
  SELECT fk.name, OBJECT_NAME(fk.parent_object_id)
  FROM sys.foreign_keys fk
  JOIN sys.foreign_key_columns fkc ON fk.object_id = fkc.constraint_object_id
  WHERE fk.referenced_object_id = OBJECT_ID('dbo.account_users')
    AND COL_NAME(fk.referenced_object_id, fkc.referenced_column_id) = 'recid';

OPEN fk_cursor;
FETCH NEXT FROM fk_cursor INTO @fk_remaining, @fk_parent_table;
WHILE @@FETCH_STATUS = 0
BEGIN
  EXEC('ALTER TABLE [' + @fk_parent_table + '] DROP CONSTRAINT [' + @fk_remaining + '];');
  FETCH NEXT FROM fk_cursor INTO @fk_remaining, @fk_parent_table;
END;
CLOSE fk_cursor;
DEALLOCATE fk_cursor;

-- 5b. Drop the existing PK on recid
DECLARE @pk_account_users NVARCHAR(256);
SELECT @pk_account_users = i.name
FROM sys.indexes i
WHERE i.object_id = OBJECT_ID('dbo.account_users')
  AND i.is_primary_key = 1;

IF @pk_account_users IS NOT NULL
  EXEC('ALTER TABLE dbo.account_users DROP CONSTRAINT [' + @pk_account_users + '];');

-- 5c. Drop the UQ on element_guid (it will be redundant once element_guid is PK)
IF EXISTS (
  SELECT 1 FROM sys.indexes
  WHERE name = 'UQ_account_users_guid'
    AND object_id = OBJECT_ID('dbo.account_users')
)
  ALTER TABLE dbo.account_users DROP CONSTRAINT UQ_account_users_guid;

-- Also check for the v080-prefixed variant
IF EXISTS (
  SELECT 1 FROM sys.indexes
  WHERE name = 'UQ_v080_account_users_guid'
    AND object_id = OBJECT_ID('dbo.account_users')
)
  ALTER TABLE dbo.account_users DROP CONSTRAINT UQ_v080_account_users_guid;

-- 5d. Drop recid column
IF EXISTS (
  SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS
  WHERE TABLE_NAME = 'account_users' AND COLUMN_NAME = 'recid'
)
  ALTER TABLE dbo.account_users DROP COLUMN recid;

-- 5e. Add PK on element_guid
IF NOT EXISTS (
  SELECT 1
  FROM sys.key_constraints
  WHERE [type] = 'PK'
    AND parent_object_id = OBJECT_ID('dbo.account_users')
)
  ALTER TABLE dbo.account_users ADD CONSTRAINT PK_account_users PRIMARY KEY (element_guid);

-- ============================================================================
-- PHASE 6: Create new FK constraints with explicit names
-- ============================================================================

IF NOT EXISTS (
  SELECT 1 FROM sys.foreign_keys WHERE name = 'FK_account_api_tokens_users_guid'
)
  ALTER TABLE dbo.account_api_tokens
    ADD CONSTRAINT FK_account_api_tokens_users_guid
    FOREIGN KEY (users_guid) REFERENCES dbo.account_users (element_guid);

IF NOT EXISTS (
  SELECT 1 FROM sys.foreign_keys WHERE name = 'FK_account_mcp_agents_users_guid'
)
  ALTER TABLE dbo.account_mcp_agents
    ADD CONSTRAINT FK_account_mcp_agents_users_guid
    FOREIGN KEY (users_guid) REFERENCES dbo.account_users (element_guid);

IF NOT EXISTS (
  SELECT 1 FROM sys.indexes
  WHERE name = 'IX_account_mcp_agents_users_guid'
    AND object_id = OBJECT_ID('dbo.account_mcp_agents')
)
  CREATE NONCLUSTERED INDEX IX_account_mcp_agents_users_guid
    ON dbo.account_mcp_agents (users_guid);

IF NOT EXISTS (
  SELECT 1 FROM sys.foreign_keys WHERE name = 'FK_account_mcp_auth_codes_users_guid'
)
  ALTER TABLE dbo.account_mcp_auth_codes
    ADD CONSTRAINT FK_account_mcp_auth_codes_users_guid
    FOREIGN KEY (users_guid) REFERENCES dbo.account_users (element_guid);

-- ============================================================================
-- PHASE 7: Re-establish any downstream FKs that were targeting
-- account_users.element_guid via the old UQ constraint.
-- These should automatically resolve to the new PK, but if any were
-- dropped by the UQ removal, recreate them.
-- ============================================================================

-- users_sessions → account_users.element_guid
IF NOT EXISTS (
  SELECT 1 FROM sys.foreign_keys
  WHERE parent_object_id = OBJECT_ID('dbo.users_sessions')
    AND referenced_object_id = OBJECT_ID('dbo.account_users')
)
  ALTER TABLE dbo.users_sessions
    ADD CONSTRAINT FK_users_sessions_users_guid
    FOREIGN KEY (users_guid) REFERENCES dbo.account_users (element_guid)
    ON DELETE CASCADE;

-- users_roles → account_users.element_guid
IF NOT EXISTS (
  SELECT 1 FROM sys.foreign_keys
  WHERE parent_object_id = OBJECT_ID('dbo.users_roles')
    AND referenced_object_id = OBJECT_ID('dbo.account_users')
)
  ALTER TABLE dbo.users_roles
    ADD CONSTRAINT FK_users_roles_users_guid
    FOREIGN KEY (users_guid) REFERENCES dbo.account_users (element_guid)
    ON DELETE CASCADE;

-- users_enablements → account_users.element_guid
IF NOT EXISTS (
  SELECT 1 FROM sys.foreign_keys
  WHERE parent_object_id = OBJECT_ID('dbo.users_enablements')
    AND referenced_object_id = OBJECT_ID('dbo.account_users')
)
  ALTER TABLE dbo.users_enablements
    ADD CONSTRAINT FK_users_enablements_users_guid
    FOREIGN KEY (users_guid) REFERENCES dbo.account_users (element_guid);

-- users_credits → account_users.element_guid
IF NOT EXISTS (
  SELECT 1 FROM sys.foreign_keys
  WHERE parent_object_id = OBJECT_ID('dbo.users_credits')
    AND referenced_object_id = OBJECT_ID('dbo.account_users')
)
  ALTER TABLE dbo.users_credits
    ADD CONSTRAINT FK_users_credits_users_guid
    FOREIGN KEY (users_guid) REFERENCES dbo.account_users (element_guid)
    ON DELETE CASCADE;

-- users_profileimg → account_users.element_guid
IF NOT EXISTS (
  SELECT 1 FROM sys.foreign_keys
  WHERE parent_object_id = OBJECT_ID('dbo.users_profileimg')
    AND referenced_object_id = OBJECT_ID('dbo.account_users')
)
  ALTER TABLE dbo.users_profileimg
    ADD CONSTRAINT FK_users_profileimg_users_guid
    FOREIGN KEY (users_guid) REFERENCES dbo.account_users (element_guid)
    ON DELETE CASCADE;

-- users_auth → account_users.element_guid
IF NOT EXISTS (
  SELECT 1 FROM sys.foreign_keys
  WHERE parent_object_id = OBJECT_ID('dbo.users_auth')
    AND referenced_object_id = OBJECT_ID('dbo.account_users')
)
  ALTER TABLE dbo.users_auth
    ADD CONSTRAINT FK_users_auth_users_guid
    FOREIGN KEY (users_guid) REFERENCES dbo.account_users (element_guid)
    ON DELETE CASCADE;

-- users_storage_cache → account_users.element_guid
IF NOT EXISTS (
  SELECT 1 FROM sys.foreign_keys
  WHERE parent_object_id = OBJECT_ID('dbo.users_storage_cache')
    AND referenced_object_id = OBJECT_ID('dbo.account_users')
)
  ALTER TABLE dbo.users_storage_cache
    ADD CONSTRAINT FK_users_storage_cache_users_guid
    FOREIGN KEY (users_guid) REFERENCES dbo.account_users (element_guid);

-- users_actions_log → account_users.element_guid
IF NOT EXISTS (
  SELECT 1 FROM sys.foreign_keys
  WHERE parent_object_id = OBJECT_ID('dbo.users_actions_log')
    AND referenced_object_id = OBJECT_ID('dbo.account_users')
)
  ALTER TABLE dbo.users_actions_log
    ADD CONSTRAINT FK_users_actions_log_users_guid
    FOREIGN KEY (users_guid) REFERENCES dbo.account_users (element_guid);

-- service_pages (element_created_by, element_modified_by) → account_users.element_guid
IF NOT EXISTS (
  SELECT 1 FROM sys.foreign_keys fk
  JOIN sys.foreign_key_columns fkc ON fk.object_id = fkc.constraint_object_id
  JOIN sys.columns c ON fkc.parent_object_id = c.object_id AND fkc.parent_column_id = c.column_id
  WHERE fk.parent_object_id = OBJECT_ID('dbo.service_pages')
    AND fk.referenced_object_id = OBJECT_ID('dbo.account_users')
    AND c.name = 'element_created_by'
)
  ALTER TABLE dbo.service_pages
    ADD CONSTRAINT FK_service_pages_created_by
    FOREIGN KEY (element_created_by) REFERENCES dbo.account_users (element_guid);

IF NOT EXISTS (
  SELECT 1 FROM sys.foreign_keys fk
  JOIN sys.foreign_key_columns fkc ON fk.object_id = fkc.constraint_object_id
  JOIN sys.columns c ON fkc.parent_object_id = c.object_id AND fkc.parent_column_id = c.column_id
  WHERE fk.parent_object_id = OBJECT_ID('dbo.service_pages')
    AND fk.referenced_object_id = OBJECT_ID('dbo.account_users')
    AND c.name = 'element_modified_by'
)
  ALTER TABLE dbo.service_pages
    ADD CONSTRAINT FK_service_pages_modified_by
    FOREIGN KEY (element_modified_by) REFERENCES dbo.account_users (element_guid);

-- assistant_conversations → account_users.element_guid
-- (This FK may reference users_guid or element_user_id depending on schema version)
IF NOT EXISTS (
  SELECT 1 FROM sys.foreign_keys
  WHERE parent_object_id = OBJECT_ID('dbo.assistant_conversations')
    AND referenced_object_id = OBJECT_ID('dbo.account_users')
)
BEGIN
  IF EXISTS (
    SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_NAME = 'assistant_conversations' AND COLUMN_NAME = 'users_guid'
  )
    ALTER TABLE dbo.assistant_conversations
      ADD CONSTRAINT FK_assistant_conversations_users_guid
      FOREIGN KEY (users_guid) REFERENCES dbo.account_users (element_guid);
END;

-- finance_credit_lots → account_users.element_guid
IF NOT EXISTS (
  SELECT 1 FROM sys.foreign_keys fk
  JOIN sys.foreign_key_columns fkc ON fk.object_id = fkc.constraint_object_id
  JOIN sys.columns c ON fkc.parent_object_id = c.object_id AND fkc.parent_column_id = c.column_id
  WHERE fk.parent_object_id = OBJECT_ID('dbo.finance_credit_lots')
    AND fk.referenced_object_id = OBJECT_ID('dbo.account_users')
    AND c.name = 'users_guid'
)
  ALTER TABLE dbo.finance_credit_lots
    ADD CONSTRAINT FK_finance_credit_lots_users_guid
    FOREIGN KEY (users_guid) REFERENCES dbo.account_users (element_guid);

COMMIT TRANSACTION;

-- ============================================================================
-- PHASE 8: Update reflection tables (run after transaction commits)
-- ============================================================================

-- Update system_schema_columns: remove recid row for account_users
DELETE FROM dbo.system_schema_columns
WHERE tables_recid = (
  SELECT recid FROM dbo.system_schema_tables WHERE element_name = 'account_users'
)
AND element_name = 'recid';

-- Update system_schema_columns: mark element_guid as PK
UPDATE dbo.system_schema_columns
SET element_is_primary_key = 1,
    element_is_identity = 0,
    element_ordinal = 1,
    element_modified_on = SYSUTCDATETIME()
WHERE tables_recid = (
  SELECT recid FROM dbo.system_schema_tables WHERE element_name = 'account_users'
)
AND element_name = 'element_guid';

-- Renumber remaining column ordinals for account_users
;WITH cte AS (
  SELECT recid, ROW_NUMBER() OVER (ORDER BY
    CASE element_name WHEN 'element_guid' THEN 0 ELSE 1 END,
    element_ordinal
  ) AS new_ordinal
  FROM dbo.system_schema_columns
  WHERE tables_recid = (
    SELECT recid FROM dbo.system_schema_tables WHERE element_name = 'account_users'
  )
)
UPDATE cte SET element_ordinal = (SELECT new_ordinal FROM cte c2 WHERE c2.recid = cte.recid);

-- Update reflection: rename users_recid → users_guid in downstream columns
UPDATE dbo.system_schema_columns
SET element_name = 'users_guid',
    edt_recid = (SELECT recid FROM dbo.system_edt_mappings WHERE element_name = 'UUID'),
    element_modified_on = SYSUTCDATETIME()
WHERE element_name = 'users_recid'
AND tables_recid IN (
  SELECT recid FROM dbo.system_schema_tables
  WHERE element_name IN ('account_api_tokens', 'account_mcp_agents', 'account_mcp_auth_codes')
);

-- Update reflection: foreign keys for the three tables
-- Delete old FK entries pointing to account_users.recid
DELETE FROM dbo.system_schema_foreign_keys
WHERE element_column_name = 'users_recid'
AND tables_recid IN (
  SELECT recid FROM dbo.system_schema_tables
  WHERE element_name IN ('account_api_tokens', 'account_mcp_agents', 'account_mcp_auth_codes')
);

-- Insert new FK entries pointing to account_users.element_guid
INSERT INTO dbo.system_schema_foreign_keys (tables_recid, element_column_name, referenced_tables_recid, element_referenced_column)
SELECT
  t.recid,
  'users_guid',
  au.recid,
  'element_guid'
FROM dbo.system_schema_tables t
CROSS JOIN (SELECT recid FROM dbo.system_schema_tables WHERE element_name = 'account_users') au
WHERE t.element_name IN ('account_api_tokens', 'account_mcp_agents', 'account_mcp_auth_codes')
AND NOT EXISTS (
  SELECT 1 FROM dbo.system_schema_foreign_keys fk
  WHERE fk.tables_recid = t.recid AND fk.element_column_name = 'users_guid'
);

-- Update reflection: index rename
UPDATE dbo.system_schema_indexes
SET element_name = 'IX_account_mcp_agents_users_guid',
    element_columns = 'users_guid',
    element_modified_on = SYSUTCDATETIME()
WHERE element_name = 'IX_account_mcp_agents_users'
AND tables_recid = (
  SELECT recid FROM dbo.system_schema_tables WHERE element_name = 'account_mcp_agents'
);

-- Drop the old UQ index reflection for account_users
DELETE FROM dbo.system_schema_indexes
WHERE element_name IN ('UQ_account_users_guid', 'UQ_v080_account_users_guid')
AND tables_recid = (
  SELECT recid FROM dbo.system_schema_tables WHERE element_name = 'account_users'
);

-- Update modified timestamp on account_users reflection
UPDATE dbo.system_schema_tables
SET element_modified_on = SYSUTCDATETIME()
WHERE element_name = 'account_users';

PRINT 'Migration v0.10.1.0 complete: account_users PK migrated to element_guid.';
