-- ============================================================================
-- v0.10.1.0 — Migrate account_users PK from recid to element_guid
-- ============================================================================
-- CORRECTED VERSION — fixes:
--   1. Phase 1 UPDATE backfills wrapped in EXEC() for deferred compilation
--   2. Phase 4 NULL checks use sp_executesql, ALTER COLUMN wrapped in EXEC()
--   3. Phase 5 drops ALL FKs referencing account_users (both recid and
--      element_guid via UQ) before dropping constraints
--   4. Phase 8 CTE replaced with JOIN-based UPDATE
--
-- Prerequisites: Backup databases before running.
-- ============================================================================

SET XACT_ABORT ON;
BEGIN TRANSACTION;

-- ============================================================================
-- PHASE 1: Add users_guid columns to downstream tables, backfill from JOIN
-- ============================================================================
-- NOTE: UPDATE statements use EXEC() because SQL Server compiles all
-- statements in a batch before executing. The new column added by
-- ALTER TABLE ADD doesn't exist at compile time, so direct references fail.

-- 1a. account_api_tokens
IF NOT EXISTS (
  SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS
  WHERE TABLE_NAME = 'account_api_tokens' AND COLUMN_NAME = 'users_guid'
)
BEGIN
  ALTER TABLE dbo.account_api_tokens ADD users_guid uniqueidentifier NULL;
END;

EXEC('
  UPDATE t
  SET t.users_guid = au.element_guid
  FROM dbo.account_api_tokens t
  JOIN dbo.account_users au ON au.recid = t.users_recid
  WHERE t.users_guid IS NULL;
');

-- 1b. account_mcp_agents
IF NOT EXISTS (
  SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS
  WHERE TABLE_NAME = 'account_mcp_agents' AND COLUMN_NAME = 'users_guid'
)
BEGIN
  ALTER TABLE dbo.account_mcp_agents ADD users_guid uniqueidentifier NULL;
END;

EXEC('
  UPDATE t
  SET t.users_guid = au.element_guid
  FROM dbo.account_mcp_agents t
  JOIN dbo.account_users au ON au.recid = t.users_recid
  WHERE t.users_guid IS NULL AND t.users_recid IS NOT NULL;
');

-- 1c. account_mcp_auth_codes
IF NOT EXISTS (
  SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS
  WHERE TABLE_NAME = 'account_mcp_auth_codes' AND COLUMN_NAME = 'users_guid'
)
BEGIN
  ALTER TABLE dbo.account_mcp_auth_codes ADD users_guid uniqueidentifier NULL;
END;

EXEC('
  UPDATE t
  SET t.users_guid = au.element_guid
  FROM dbo.account_mcp_auth_codes t
  JOIN dbo.account_users au ON au.recid = t.users_recid
  WHERE t.users_guid IS NULL;
');

-- ============================================================================
-- PHASE 2: Drop old FK constraints on downstream tables referencing
--          account_users.recid (the three MCP/API tables)
-- ============================================================================

DECLARE @fk_api_tokens NVARCHAR(256);
SELECT @fk_api_tokens = fk.name
FROM sys.foreign_keys fk
JOIN sys.foreign_key_columns fkc ON fk.object_id = fkc.constraint_object_id
JOIN sys.columns c ON fkc.parent_object_id = c.object_id AND fkc.parent_column_id = c.column_id
WHERE OBJECT_NAME(fk.parent_object_id) = 'account_api_tokens'
  AND c.name = 'users_recid';

IF @fk_api_tokens IS NOT NULL
  EXEC('ALTER TABLE dbo.account_api_tokens DROP CONSTRAINT [' + @fk_api_tokens + '];');

DECLARE @fk_mcp_agents NVARCHAR(256);
SELECT @fk_mcp_agents = fk.name
FROM sys.foreign_keys fk
JOIN sys.foreign_key_columns fkc ON fk.object_id = fkc.constraint_object_id
JOIN sys.columns c ON fkc.parent_object_id = c.object_id AND fkc.parent_column_id = c.column_id
WHERE OBJECT_NAME(fk.parent_object_id) = 'account_mcp_agents'
  AND c.name = 'users_recid';

IF @fk_mcp_agents IS NOT NULL
  EXEC('ALTER TABLE dbo.account_mcp_agents DROP CONSTRAINT [' + @fk_mcp_agents + '];');

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
-- PHASE 4: Validate backfills, enforce NOT NULL, drop old columns
-- ============================================================================

DECLARE @has_null_api BIT = 0;
EXEC sp_executesql
  N'SELECT @out = CASE WHEN EXISTS (SELECT 1 FROM dbo.account_api_tokens WHERE users_guid IS NULL) THEN 1 ELSE 0 END',
  N'@out BIT OUTPUT',
  @out = @has_null_api OUTPUT;
IF @has_null_api = 1
BEGIN
  RAISERROR('ABORT: account_api_tokens has NULL users_guid after backfill.', 16, 1);
  ROLLBACK TRANSACTION;
  RETURN;
END;

DECLARE @has_null_auth BIT = 0;
EXEC sp_executesql
  N'SELECT @out = CASE WHEN EXISTS (SELECT 1 FROM dbo.account_mcp_auth_codes WHERE users_guid IS NULL) THEN 1 ELSE 0 END',
  N'@out BIT OUTPUT',
  @out = @has_null_auth OUTPUT;
IF @has_null_auth = 1
BEGIN
  RAISERROR('ABORT: account_mcp_auth_codes has NULL users_guid after backfill.', 16, 1);
  ROLLBACK TRANSACTION;
  RETURN;
END;

EXEC('ALTER TABLE dbo.account_api_tokens ALTER COLUMN users_guid uniqueidentifier NOT NULL;');
EXEC('ALTER TABLE dbo.account_mcp_auth_codes ALTER COLUMN users_guid uniqueidentifier NOT NULL;');

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
-- PHASE 5: Drop ALL FKs referencing account_users, drop PK and UQ,
--          drop recid, promote element_guid to PK
-- ============================================================================

-- 5a. Drop ALL foreign keys that reference account_users — both those
--     targeting recid AND those targeting element_guid via the UQ constraint.
--     This is required because the UQ constraint cannot be dropped while
--     FKs still reference it.
DECLARE @fk_name NVARCHAR(256);
DECLARE @fk_parent NVARCHAR(256);
DECLARE fk_cursor CURSOR LOCAL FAST_FORWARD FOR
  SELECT fk.name, OBJECT_NAME(fk.parent_object_id)
  FROM sys.foreign_keys fk
  WHERE fk.referenced_object_id = OBJECT_ID('dbo.account_users');

OPEN fk_cursor;
FETCH NEXT FROM fk_cursor INTO @fk_name, @fk_parent;
WHILE @@FETCH_STATUS = 0
BEGIN
  EXEC('ALTER TABLE dbo.[' + @fk_parent + '] DROP CONSTRAINT [' + @fk_name + '];');
  FETCH NEXT FROM fk_cursor INTO @fk_name, @fk_parent;
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

-- 5c. Drop UQ on element_guid (now safe — all dependent FKs removed above)
IF EXISTS (
  SELECT 1 FROM sys.indexes
  WHERE name = 'UQ_account_users_guid'
    AND object_id = OBJECT_ID('dbo.account_users')
)
  ALTER TABLE dbo.account_users DROP CONSTRAINT UQ_account_users_guid;

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
  SELECT 1 FROM sys.key_constraints
  WHERE [type] = 'PK'
    AND parent_object_id = OBJECT_ID('dbo.account_users')
)
  ALTER TABLE dbo.account_users ADD CONSTRAINT PK_account_users PRIMARY KEY (element_guid);

-- ============================================================================
-- PHASE 6: Create new FK constraints for the three migrated tables
-- ============================================================================

EXEC('
  ALTER TABLE dbo.account_api_tokens
    ADD CONSTRAINT FK_account_api_tokens_users_guid
    FOREIGN KEY (users_guid) REFERENCES dbo.account_users (element_guid);
');

EXEC('
  ALTER TABLE dbo.account_mcp_agents
    ADD CONSTRAINT FK_account_mcp_agents_users_guid
    FOREIGN KEY (users_guid) REFERENCES dbo.account_users (element_guid);
');

IF NOT EXISTS (
  SELECT 1 FROM sys.indexes
  WHERE name = 'IX_account_mcp_agents_users_guid'
    AND object_id = OBJECT_ID('dbo.account_mcp_agents')
)
  CREATE NONCLUSTERED INDEX IX_account_mcp_agents_users_guid
    ON dbo.account_mcp_agents (users_guid);

EXEC('
  ALTER TABLE dbo.account_mcp_auth_codes
    ADD CONSTRAINT FK_account_mcp_auth_codes_users_guid
    FOREIGN KEY (users_guid) REFERENCES dbo.account_users (element_guid);
');

-- ============================================================================
-- PHASE 7: Re-establish all downstream FKs with explicit names.
--          Phase 5a dropped every FK referencing account_users.
--          Now recreate them all pointing at the new PK.
-- ============================================================================

ALTER TABLE dbo.users_sessions
  ADD CONSTRAINT FK_users_sessions_users_guid
  FOREIGN KEY (users_guid) REFERENCES dbo.account_users (element_guid)
  ON DELETE CASCADE;

ALTER TABLE dbo.users_roles
  ADD CONSTRAINT FK_users_roles_users_guid
  FOREIGN KEY (users_guid) REFERENCES dbo.account_users (element_guid)
  ON DELETE CASCADE;

ALTER TABLE dbo.users_enablements
  ADD CONSTRAINT FK_users_enablements_users_guid
  FOREIGN KEY (users_guid) REFERENCES dbo.account_users (element_guid);

ALTER TABLE dbo.users_credits
  ADD CONSTRAINT FK_users_credits_users_guid
  FOREIGN KEY (users_guid) REFERENCES dbo.account_users (element_guid)
  ON DELETE CASCADE;

ALTER TABLE dbo.users_profileimg
  ADD CONSTRAINT FK_users_profileimg_users_guid
  FOREIGN KEY (users_guid) REFERENCES dbo.account_users (element_guid)
  ON DELETE CASCADE;

ALTER TABLE dbo.users_auth
  ADD CONSTRAINT FK_users_auth_users_guid
  FOREIGN KEY (users_guid) REFERENCES dbo.account_users (element_guid)
  ON DELETE CASCADE;

ALTER TABLE dbo.users_storage_cache
  ADD CONSTRAINT FK_users_storage_cache_users_guid
  FOREIGN KEY (users_guid) REFERENCES dbo.account_users (element_guid);

ALTER TABLE dbo.users_actions_log
  ADD CONSTRAINT FK_users_actions_log_users_guid
  FOREIGN KEY (users_guid) REFERENCES dbo.account_users (element_guid);

ALTER TABLE dbo.service_pages
  ADD CONSTRAINT FK_service_pages_created_by
  FOREIGN KEY (element_created_by) REFERENCES dbo.account_users (element_guid);

ALTER TABLE dbo.service_pages
  ADD CONSTRAINT FK_service_pages_modified_by
  FOREIGN KEY (element_modified_by) REFERENCES dbo.account_users (element_guid);

-- assistant_conversations
IF EXISTS (
  SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS
  WHERE TABLE_NAME = 'assistant_conversations' AND COLUMN_NAME = 'users_guid'
)
  ALTER TABLE dbo.assistant_conversations
    ADD CONSTRAINT FK_assistant_conversations_users_guid
    FOREIGN KEY (users_guid) REFERENCES dbo.account_users (element_guid);

-- finance_credit_lots
ALTER TABLE dbo.finance_credit_lots
  ADD CONSTRAINT FK_finance_credit_lots_users_guid
  FOREIGN KEY (users_guid) REFERENCES dbo.account_users (element_guid);

COMMIT TRANSACTION;

-- ============================================================================
-- PHASE 8: Update reflection tables (runs after commit)
-- ============================================================================

-- Remove recid row for account_users
DELETE FROM dbo.system_schema_columns
WHERE tables_recid = (
  SELECT recid FROM dbo.system_schema_tables WHERE element_name = 'account_users'
)
AND element_name = 'recid';

-- Mark element_guid as PK
UPDATE dbo.system_schema_columns
SET element_is_primary_key = 1,
    element_is_identity = 0,
    element_ordinal = 1,
    element_modified_on = SYSUTCDATETIME()
WHERE tables_recid = (
  SELECT recid FROM dbo.system_schema_tables WHERE element_name = 'account_users'
)
AND element_name = 'element_guid';

-- Renumber ordinals
UPDATE sc
SET sc.element_ordinal = sub.new_ordinal
FROM dbo.system_schema_columns sc
JOIN (
  SELECT recid, ROW_NUMBER() OVER (ORDER BY
    CASE element_name WHEN 'element_guid' THEN 0 ELSE 1 END,
    element_ordinal
  ) AS new_ordinal
  FROM dbo.system_schema_columns
  WHERE tables_recid = (
    SELECT recid FROM dbo.system_schema_tables WHERE element_name = 'account_users'
  )
) sub ON sub.recid = sc.recid;

-- Rename users_recid → users_guid in reflection columns
UPDATE dbo.system_schema_columns
SET element_name = 'users_guid',
    edt_recid = (SELECT recid FROM dbo.system_edt_mappings WHERE element_name = 'UUID'),
    element_modified_on = SYSUTCDATETIME()
WHERE element_name = 'users_recid'
AND tables_recid IN (
  SELECT recid FROM dbo.system_schema_tables
  WHERE element_name IN ('account_api_tokens', 'account_mcp_agents', 'account_mcp_auth_codes')
);

-- Delete old FK reflection entries
DELETE FROM dbo.system_schema_foreign_keys
WHERE element_column_name = 'users_recid'
AND tables_recid IN (
  SELECT recid FROM dbo.system_schema_tables
  WHERE element_name IN ('account_api_tokens', 'account_mcp_agents', 'account_mcp_auth_codes')
);

-- Insert new FK reflection entries
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

-- Update index reflection
UPDATE dbo.system_schema_indexes
SET element_name = 'IX_account_mcp_agents_users_guid',
    element_columns = 'users_guid',
    element_modified_on = SYSUTCDATETIME()
WHERE element_name = 'IX_account_mcp_agents_users'
AND tables_recid = (
  SELECT recid FROM dbo.system_schema_tables WHERE element_name = 'account_mcp_agents'
);

-- Drop old UQ index reflection
DELETE FROM dbo.system_schema_indexes
WHERE element_name IN ('UQ_account_users_guid', 'UQ_v080_account_users_guid')
AND tables_recid = (
  SELECT recid FROM dbo.system_schema_tables WHERE element_name = 'account_users'
);

-- Timestamp
UPDATE dbo.system_schema_tables
SET element_modified_on = SYSUTCDATETIME()
WHERE element_name = 'account_users';

PRINT 'Migration v0.10.1.0 complete: account_users PK migrated to element_guid.';