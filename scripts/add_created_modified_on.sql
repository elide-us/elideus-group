-- Script to add created_on/modified_on timestamps and update keys for sessions and devices
-- Adds NOT NULL columns with default SYSUTCDATETIME()
-- Ensures cascade deletes for session/device relationships

-- 1. account_users: add created_on, modified_on
IF COL_LENGTH('dbo.account_users', 'created_on') IS NULL
BEGIN
    ALTER TABLE dbo.account_users
        ADD created_on datetimeoffset NOT NULL CONSTRAINT DF_account_users_created_on DEFAULT (SYSUTCDATETIME());
END;
IF COL_LENGTH('dbo.account_users', 'modified_on') IS NULL
BEGIN
    ALTER TABLE dbo.account_users
        ADD modified_on datetimeoffset NOT NULL CONSTRAINT DF_account_users_modified_on DEFAULT (SYSUTCDATETIME());
END;

-- 2. users_sessions: add token and timestamps
IF COL_LENGTH('dbo.users_sessions', 'element_token') IS NULL
BEGIN
    ALTER TABLE dbo.users_sessions
        ADD element_token nvarchar(MAX) NOT NULL CONSTRAINT DF_users_sessions_token DEFAULT (CONVERT(nvarchar(64), NEWID()));
END;
IF COL_LENGTH('dbo.users_sessions', 'element_token_iat') IS NULL
BEGIN
    ALTER TABLE dbo.users_sessions
        ADD element_token_iat datetimeoffset NOT NULL CONSTRAINT DF_users_sessions_token_iat DEFAULT (SYSUTCDATETIME());
END;
IF COL_LENGTH('dbo.users_sessions', 'element_token_exp') IS NULL
BEGIN
    ALTER TABLE dbo.users_sessions
        ADD element_token_exp datetimeoffset NOT NULL CONSTRAINT DF_users_sessions_token_exp DEFAULT (SYSUTCDATETIME());
END;
IF COL_LENGTH('dbo.users_sessions', 'created_on') IS NULL
BEGIN
    ALTER TABLE dbo.users_sessions
        ADD created_on datetimeoffset NOT NULL CONSTRAINT DF_users_sessions_created_on DEFAULT (SYSUTCDATETIME());
END;
IF COL_LENGTH('dbo.users_sessions', 'modified_on') IS NULL
BEGIN
    ALTER TABLE dbo.users_sessions
        ADD modified_on datetimeoffset NOT NULL CONSTRAINT DF_users_sessions_modified_on DEFAULT (SYSUTCDATETIME());
END;

-- Ensure FK to account_users cascades deletes
DECLARE @fk_us_sessions NVARCHAR(128);
SELECT @fk_us_sessions = fk.name
FROM sys.foreign_keys fk
WHERE fk.parent_object_id = OBJECT_ID('dbo.users_sessions')
  AND fk.referenced_object_id = OBJECT_ID('dbo.account_users');
IF @fk_us_sessions IS NOT NULL
BEGIN
    EXEC('ALTER TABLE dbo.users_sessions DROP CONSTRAINT ' + QUOTENAME(@fk_us_sessions));
END;
ALTER TABLE dbo.users_sessions
    ADD CONSTRAINT FK_users_sessions_account_users
        FOREIGN KEY (users_guid) REFERENCES dbo.account_users(element_guid) ON DELETE CASCADE;

-- 3. sessions_devices: add created_on, modified_on, default for token_exp
IF COL_LENGTH('dbo.sessions_devices', 'created_on') IS NULL
BEGIN
    ALTER TABLE dbo.sessions_devices
        ADD created_on datetimeoffset NOT NULL CONSTRAINT DF_sessions_devices_created_on DEFAULT (SYSUTCDATETIME());
END;
IF COL_LENGTH('dbo.sessions_devices', 'modified_on') IS NULL
BEGIN
    ALTER TABLE dbo.sessions_devices
        ADD modified_on datetimeoffset NOT NULL CONSTRAINT DF_sessions_devices_modified_on DEFAULT (SYSUTCDATETIME());
END;
IF OBJECT_ID('DF_sessions_devices_token_exp', 'D') IS NULL
BEGIN
    ALTER TABLE dbo.sessions_devices
        ADD CONSTRAINT DF_sessions_devices_token_exp DEFAULT (SYSUTCDATETIME()) FOR element_token_exp;
END;

-- Ensure FK to users_sessions cascades deletes
DECLARE @fk_sd_sessions NVARCHAR(128);
SELECT @fk_sd_sessions = fk.name
FROM sys.foreign_keys fk
WHERE fk.parent_object_id = OBJECT_ID('dbo.sessions_devices')
  AND fk.referenced_object_id = OBJECT_ID('dbo.users_sessions');
IF @fk_sd_sessions IS NOT NULL
BEGIN
    EXEC('ALTER TABLE dbo.sessions_devices DROP CONSTRAINT ' + QUOTENAME(@fk_sd_sessions));
END;
ALTER TABLE dbo.sessions_devices
    ADD CONSTRAINT FK_sessions_devices_sessions
        FOREIGN KEY (sessions_guid) REFERENCES dbo.users_sessions(element_guid) ON DELETE CASCADE;

-- 4. users_auth: add created_on, modified_on, cascade delete
IF COL_LENGTH('dbo.users_auth', 'created_on') IS NULL
BEGIN
    ALTER TABLE dbo.users_auth
        ADD created_on datetimeoffset NOT NULL CONSTRAINT DF_users_auth_created_on DEFAULT (SYSUTCDATETIME());
END;
IF COL_LENGTH('dbo.users_auth', 'modified_on') IS NULL
BEGIN
    ALTER TABLE dbo.users_auth
        ADD modified_on datetimeoffset NOT NULL CONSTRAINT DF_users_auth_modified_on DEFAULT (SYSUTCDATETIME());
END;

DECLARE @fk_users_auth NVARCHAR(128);
SELECT @fk_users_auth = fk.name
FROM sys.foreign_keys fk
WHERE fk.parent_object_id = OBJECT_ID('dbo.users_auth')
  AND fk.referenced_object_id = OBJECT_ID('dbo.account_users');
IF @fk_users_auth IS NOT NULL
BEGIN
    EXEC('ALTER TABLE dbo.users_auth DROP CONSTRAINT ' + QUOTENAME(@fk_users_auth));
END;
ALTER TABLE dbo.users_auth
    ADD CONSTRAINT FK_users_auth_account_users
        FOREIGN KEY (users_guid) REFERENCES dbo.account_users(element_guid) ON DELETE CASCADE;

-- 5. users_credits: add created_on, modified_on, cascade delete
IF COL_LENGTH('dbo.users_credits', 'created_on') IS NULL
BEGIN
    ALTER TABLE dbo.users_credits
        ADD created_on datetimeoffset NOT NULL CONSTRAINT DF_users_credits_created_on DEFAULT (SYSUTCDATETIME());
END;
IF COL_LENGTH('dbo.users_credits', 'modified_on') IS NULL
BEGIN
    ALTER TABLE dbo.users_credits
        ADD modified_on datetimeoffset NOT NULL CONSTRAINT DF_users_credits_modified_on DEFAULT (SYSUTCDATETIME());
END;

DECLARE @fk_users_credits NVARCHAR(128);
SELECT @fk_users_credits = fk.name
FROM sys.foreign_keys fk
WHERE fk.parent_object_id = OBJECT_ID('dbo.users_credits')
  AND fk.referenced_object_id = OBJECT_ID('dbo.account_users');
IF @fk_users_credits IS NOT NULL
BEGIN
    EXEC('ALTER TABLE dbo.users_credits DROP CONSTRAINT ' + QUOTENAME(@fk_users_credits));
END;
ALTER TABLE dbo.users_credits
    ADD CONSTRAINT FK_users_credits_account_users
        FOREIGN KEY (users_guid) REFERENCES dbo.account_users(element_guid) ON DELETE CASCADE;

-- 6. users_enablements: add created_on, modified_on, cascade delete
IF COL_LENGTH('dbo.users_enablements', 'created_on') IS NULL
BEGIN
    ALTER TABLE dbo.users_enablements
        ADD created_on datetimeoffset NOT NULL CONSTRAINT DF_users_enablements_created_on DEFAULT (SYSUTCDATETIME());
END;
IF COL_LENGTH('dbo.users_enablements', 'modified_on') IS NULL
BEGIN
    ALTER TABLE dbo.users_enablements
        ADD modified_on datetimeoffset NOT NULL CONSTRAINT DF_users_enablements_modified_on DEFAULT (SYSUTCDATETIME());
END;

DECLARE @fk_users_enablements NVARCHAR(128);
SELECT @fk_users_enablements = fk.name
FROM sys.foreign_keys fk
WHERE fk.parent_object_id = OBJECT_ID('dbo.users_enablements')
  AND fk.referenced_object_id = OBJECT_ID('dbo.account_users');
IF @fk_users_enablements IS NOT NULL
BEGIN
    EXEC('ALTER TABLE dbo.users_enablements DROP CONSTRAINT ' + QUOTENAME(@fk_users_enablements));
END;
ALTER TABLE dbo.users_enablements
    ADD CONSTRAINT FK_users_enablements_account_users
        FOREIGN KEY (users_guid) REFERENCES dbo.account_users(element_guid) ON DELETE CASCADE;

-- 7. users_profileimg: add created_on, modified_on, cascade delete
IF COL_LENGTH('dbo.users_profileimg', 'created_on') IS NULL
BEGIN
    ALTER TABLE dbo.users_profileimg
        ADD created_on datetimeoffset NOT NULL CONSTRAINT DF_users_profileimg_created_on DEFAULT (SYSUTCDATETIME());
END;
IF COL_LENGTH('dbo.users_profileimg', 'modified_on') IS NULL
BEGIN
    ALTER TABLE dbo.users_profileimg
        ADD modified_on datetimeoffset NOT NULL CONSTRAINT DF_users_profileimg_modified_on DEFAULT (SYSUTCDATETIME());
END;

DECLARE @fk_users_profileimg NVARCHAR(128);
SELECT @fk_users_profileimg = fk.name
FROM sys.foreign_keys fk
WHERE fk.parent_object_id = OBJECT_ID('dbo.users_profileimg')
  AND fk.referenced_object_id = OBJECT_ID('dbo.account_users');
IF @fk_users_profileimg IS NOT NULL
BEGIN
    EXEC('ALTER TABLE dbo.users_profileimg DROP CONSTRAINT ' + QUOTENAME(@fk_users_profileimg));
END;
ALTER TABLE dbo.users_profileimg
    ADD CONSTRAINT FK_users_profileimg_account_users
        FOREIGN KEY (users_guid) REFERENCES dbo.account_users(element_guid) ON DELETE CASCADE;

-- 8. users_roles: add created_on, modified_on, cascade delete
IF COL_LENGTH('dbo.users_roles', 'created_on') IS NULL
BEGIN
    ALTER TABLE dbo.users_roles
        ADD created_on datetimeoffset NOT NULL CONSTRAINT DF_users_roles_created_on DEFAULT (SYSUTCDATETIME());
END;
IF COL_LENGTH('dbo.users_roles', 'modified_on') IS NULL
BEGIN
    ALTER TABLE dbo.users_roles
        ADD modified_on datetimeoffset NOT NULL CONSTRAINT DF_users_roles_modified_on DEFAULT (SYSUTCDATETIME());
END;

DECLARE @fk_users_roles NVARCHAR(128);
SELECT @fk_users_roles = fk.name
FROM sys.foreign_keys fk
WHERE fk.parent_object_id = OBJECT_ID('dbo.users_roles')
  AND fk.referenced_object_id = OBJECT_ID('dbo.account_users');
IF @fk_users_roles IS NOT NULL
BEGIN
    EXEC('ALTER TABLE dbo.users_roles DROP CONSTRAINT ' + QUOTENAME(@fk_users_roles));
END;
ALTER TABLE dbo.users_roles
    ADD CONSTRAINT FK_users_roles_account_users
        FOREIGN KEY (users_guid) REFERENCES dbo.account_users(element_guid) ON DELETE CASCADE;

-- 9. View for bearer tokens
IF OBJECT_ID('dbo.vw_user_security_keys', 'V') IS NOT NULL
    DROP VIEW dbo.vw_user_security_keys;

CREATE VIEW dbo.vw_user_security_keys AS
SELECT
    au.element_guid AS user_guid,
    au.element_rotkey,
    au.element_rotkey_iat,
    au.element_rotkey_exp,
    us.element_token AS session_key,
    us.element_token_iat AS session_iat,
    us.element_token_exp AS session_exp,
    sd.element_token AS device_key,
    sd.element_token_iat AS device_iat,
    sd.element_token_exp AS device_exp
FROM dbo.account_users au
JOIN dbo.users_sessions us ON au.element_guid = us.users_guid
JOIN dbo.sessions_devices sd ON us.element_guid = sd.sessions_guid;
