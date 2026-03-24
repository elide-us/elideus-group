SET NOCOUNT ON;
GO

IF COL_LENGTH('dbo.system_roles', 'element_rpc_domain') IS NULL
BEGIN
  ALTER TABLE [dbo].[system_roles]
    ADD [element_rpc_domain] NVARCHAR(64) NULL;
END;
GO

UPDATE [dbo].[system_roles]
SET [element_rpc_domain] = 'finance'
WHERE [element_name] = 'ROLE_FINANCE_ADMIN';
GO

UPDATE [dbo].[system_roles]
SET [element_rpc_domain] = 'system'
WHERE [element_name] = 'ROLE_SYSTEM_ADMIN';
GO

UPDATE [dbo].[system_roles]
SET [element_rpc_domain] = 'account'
WHERE [element_name] = 'ROLE_ACCOUNT_ADMIN';
GO

UPDATE [dbo].[system_roles]
SET [element_rpc_domain] = 'service'
WHERE [element_name] = 'ROLE_SERVICE_ADMIN';
GO

UPDATE [dbo].[system_roles]
SET [element_rpc_domain] = 'moderation'
WHERE [element_name] = 'ROLE_MODERATOR';
GO

UPDATE [dbo].[system_roles]
SET [element_rpc_domain] = 'support'
WHERE [element_name] = 'ROLE_SUPPORT';
GO

UPDATE [dbo].[system_roles]
SET [element_rpc_domain] = 'storage'
WHERE [element_name] = 'ROLE_STORAGE';
GO

UPDATE [dbo].[system_roles]
SET [element_rpc_domain] = 'users'
WHERE [element_name] = 'ROLE_REGISTERED';
GO

UPDATE [dbo].[system_roles]
SET [element_rpc_domain] = 'discord'
WHERE [element_name] = 'ROLE_DISCORD_ADMIN';
GO

UPDATE [dbo].[system_roles]
SET [element_rpc_domain] = NULL
WHERE [element_name] IN (
  'ROLE_OPENAI_API',
  'ROLE_LUMAAI_API',
  'ROLE_MCP_ACCESS',
  'ROLE_DISCORD_BOT',
  'ROLE_FINANCE_ACCT',
  'ROLE_FINANCE_APPR'
);
GO

DECLARE @system_roles_table_recid BIGINT;
SELECT @system_roles_table_recid = [recid]
FROM [dbo].[system_schema_tables]
WHERE [element_name] = 'system_roles'
  AND [element_schema] = 'dbo';

IF NOT EXISTS (
  SELECT 1
  FROM [dbo].[system_schema_columns]
  WHERE [tables_recid] = @system_roles_table_recid
    AND [element_name] = 'element_rpc_domain'
)
BEGIN
  INSERT INTO [dbo].[system_schema_columns] (
    [tables_recid],
    [edt_recid],
    [element_name],
    [element_ordinal],
    [element_nullable],
    [element_default],
    [element_max_length],
    [element_is_primary_key],
    [element_is_identity]
  )
  VALUES (
    @system_roles_table_recid,
    8,
    'element_rpc_domain',
    6,
    1,
    NULL,
    64,
    0,
    0
  );
END;
GO
