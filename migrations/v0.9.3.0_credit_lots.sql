SET NOCOUNT ON;
GO

-- ============================================================
-- COA accounts required by finance spec (§2, §6, §9, §10)
-- ============================================================
IF NOT EXISTS (SELECT 1 FROM finance_accounts WHERE element_number = '2100')
BEGIN
  INSERT INTO finance_accounts (element_guid, element_number, element_name, element_type, element_parent, is_posting, element_status)
  VALUES (NEWID(), '2100', 'Deferred Revenue', 1, '7C1FA400-6DF0-4F86-9282-184DA2DDB0E4', 1, 1);
END;

IF NOT EXISTS (SELECT 1 FROM finance_accounts WHERE element_number = '2200')
BEGIN
  INSERT INTO finance_accounts (element_guid, element_number, element_name, element_type, element_parent, is_posting, element_status)
  VALUES (NEWID(), '2200', 'Accounts Payable', 1, '7C1FA400-6DF0-4F86-9282-184DA2DDB0E4', 1, 1);
END;

IF NOT EXISTS (SELECT 1 FROM finance_accounts WHERE element_number = '2300')
BEGIN
  INSERT INTO finance_accounts (element_guid, element_number, element_name, element_type, element_parent, is_posting, element_status)
  VALUES (NEWID(), '2300', 'Accrued Expenses', 1, '7C1FA400-6DF0-4F86-9282-184DA2DDB0E4', 1, 1);
END;
GO

IF NOT EXISTS (SELECT 1 FROM finance_accounts WHERE element_number = '1300')
BEGIN
  INSERT INTO finance_accounts (element_guid, element_number, element_name, element_type, element_parent, is_posting, element_status)
  VALUES (NEWID(), '1300', 'Payment Processor Clearing', 0, '31A28AA0-BA53-4370-BCCF-632E8238735E', 1, 1);
END;
GO

IF NOT EXISTS (SELECT 1 FROM finance_accounts WHERE element_number = '4010')
BEGIN
  INSERT INTO finance_accounts (element_guid, element_number, element_name, element_type, element_parent, is_posting, element_status)
  VALUES (NEWID(), '4010', 'Recognized Revenue', 3, '911CE6FF-ED49-4841-B42E-89973FC8D7C9', 1, 1);
END;

IF NOT EXISTS (SELECT 1 FROM finance_accounts WHERE element_number = '4020')
BEGIN
  INSERT INTO finance_accounts (element_guid, element_number, element_name, element_type, element_parent, is_posting, element_status)
  VALUES (NEWID(), '4020', 'Breakage Revenue', 3, '911CE6FF-ED49-4841-B42E-89973FC8D7C9', 1, 1);
END;

IF NOT EXISTS (SELECT 1 FROM finance_accounts WHERE element_number = '4030')
BEGIN
  INSERT INTO finance_accounts (element_guid, element_number, element_name, element_type, element_parent, is_posting, element_status)
  VALUES (NEWID(), '4030', 'Contra-Revenue / Refunds', 3, '911CE6FF-ED49-4841-B42E-89973FC8D7C9', 1, 1);
END;
GO

IF NOT EXISTS (SELECT 1 FROM finance_accounts WHERE element_number = '3100')
BEGIN
  INSERT INTO finance_accounts (element_guid, element_number, element_name, element_type, element_parent, is_posting, element_status)
  VALUES (NEWID(), '3100', 'Owner''s Equity', 2, 'D20171F3-DB09-4E41-8ABA-9E1F12DA714B', 1, 1);
END;

IF NOT EXISTS (SELECT 1 FROM finance_accounts WHERE element_number = '3200')
BEGIN
  INSERT INTO finance_accounts (element_guid, element_number, element_name, element_type, element_parent, is_posting, element_status)
  VALUES (NEWID(), '3200', 'Retained Earnings', 2, 'D20171F3-DB09-4E41-8ABA-9E1F12DA714B', 1, 1);
END;
GO

IF NOT EXISTS (SELECT 1 FROM finance_accounts WHERE element_number = '5010')
BEGIN
  INSERT INTO finance_accounts (element_guid, element_number, element_name, element_type, element_parent, is_posting, element_status)
  VALUES (NEWID(), '5010', 'Merchant Fee Expense', 4, '7C3B3F89-E616-45E1-B1A3-E392F3B5ABDF', 1, 1);
END;

IF NOT EXISTS (SELECT 1 FROM finance_accounts WHERE element_number = '6100')
BEGIN
  INSERT INTO finance_accounts (element_guid, element_number, element_name, element_type, element_parent, is_posting, element_status)
  VALUES (NEWID(), '6100', 'Owner Usage', 4, '7C3B3F89-E616-45E1-B1A3-E392F3B5ABDF', 1, 1);
END;

IF NOT EXISTS (SELECT 1 FROM finance_accounts WHERE element_number = '6200')
BEGIN
  INSERT INTO finance_accounts (element_guid, element_number, element_name, element_type, element_parent, is_posting, element_status)
  VALUES (NEWID(), '6200', 'Marketing Expense', 4, '7C3B3F89-E616-45E1-B1A3-E392F3B5ABDF', 1, 1);
END;
GO

IF NOT EXISTS (SELECT 1 FROM finance_accounts WHERE element_number = '5600')
BEGIN
  INSERT INTO finance_accounts (element_guid, element_number, element_name, element_type, element_parent, is_posting, element_status)
  VALUES (NEWID(), '5600', 'Number Sequences', 4, '7C3B3F89-E616-45E1-B1A3-E392F3B5ABDF', 0, 1);
END;
GO

DECLARE @seq_parent_guid UNIQUEIDENTIFIER = (SELECT element_guid FROM finance_accounts WHERE element_number = '5600');
IF NOT EXISTS (SELECT 1 FROM finance_accounts WHERE element_number = '5610')
BEGIN
  INSERT INTO finance_accounts (element_guid, element_number, element_name, element_type, element_parent, is_posting, element_status)
  VALUES (NEWID(), '5610', 'Journal Sequences', 4, @seq_parent_guid, 0, 1);
END;

IF NOT EXISTS (SELECT 1 FROM finance_accounts WHERE element_number = '5620')
BEGIN
  INSERT INTO finance_accounts (element_guid, element_number, element_name, element_type, element_parent, is_posting, element_status)
  VALUES (NEWID(), '5620', 'Lot Sequences', 4, @seq_parent_guid, 0, 1);
END;
GO

IF NOT EXISTS (SELECT 1 FROM finance_numbers WHERE element_prefix = 'JRN' AND element_account_number = 'JRN-SEQ')
BEGIN
  INSERT INTO finance_numbers (
    accounts_guid,
    element_prefix,
    element_account_number,
    element_last_number,
    element_allocation_size,
    element_reset_policy,
    element_pattern,
    element_display_format
  )
  VALUES (
    (SELECT element_guid FROM finance_accounts WHERE element_number = '5610'),
    'JRN',
    'JRN-SEQ',
    0,
    1,
    'Never',
    'JRN-{number:06d}',
    'JRN-######'
  );
END;

IF NOT EXISTS (SELECT 1 FROM finance_numbers WHERE element_prefix = 'LOT' AND element_account_number = 'LOT-SEQ')
BEGIN
  INSERT INTO finance_numbers (
    accounts_guid,
    element_prefix,
    element_account_number,
    element_last_number,
    element_allocation_size,
    element_reset_policy,
    element_pattern,
    element_display_format
  )
  VALUES (
    (SELECT element_guid FROM finance_accounts WHERE element_number = '5620'),
    'LOT',
    'LOT-SEQ',
    0,
    1,
    'Never',
    'LOT-{number:06d}',
    'LOT-######'
  );
END;
GO

-- ============================================================
-- Dimensions required by finance spec (§3)
-- ============================================================
IF NOT EXISTS (SELECT 1 FROM finance_dimensions WHERE element_name = 'ServiceType' AND element_value = 'IMG')
  INSERT INTO finance_dimensions (element_name, element_value, element_description, element_status)
  VALUES ('ServiceType', 'IMG', 'Image generation service', 1);
IF NOT EXISTS (SELECT 1 FROM finance_dimensions WHERE element_name = 'ServiceType' AND element_value = 'VID')
  INSERT INTO finance_dimensions (element_name, element_value, element_description, element_status)
  VALUES ('ServiceType', 'VID', 'Video generation service', 1);
IF NOT EXISTS (SELECT 1 FROM finance_dimensions WHERE element_name = 'ServiceType' AND element_value = 'TTS')
  INSERT INTO finance_dimensions (element_name, element_value, element_description, element_status)
  VALUES ('ServiceType', 'TTS', 'Text-to-speech service', 1);
IF NOT EXISTS (SELECT 1 FROM finance_dimensions WHERE element_name = 'ServiceType' AND element_value = 'CHAT')
  INSERT INTO finance_dimensions (element_name, element_value, element_description, element_status)
  VALUES ('ServiceType', 'CHAT', 'Chat/conversation service', 1);
IF NOT EXISTS (SELECT 1 FROM finance_dimensions WHERE element_name = 'Vendor' AND element_value = 'Azure')
  INSERT INTO finance_dimensions (element_name, element_value, element_description, element_status)
  VALUES ('Vendor', 'Azure', 'Microsoft Azure', 1);
IF NOT EXISTS (SELECT 1 FROM finance_dimensions WHERE element_name = 'Vendor' AND element_value = 'OpenAI')
  INSERT INTO finance_dimensions (element_name, element_value, element_description, element_status)
  VALUES ('Vendor', 'OpenAI', 'OpenAI API', 1);
IF NOT EXISTS (SELECT 1 FROM finance_dimensions WHERE element_name = 'Vendor' AND element_value = 'Luma')
  INSERT INTO finance_dimensions (element_name, element_value, element_description, element_status)
  VALUES ('Vendor', 'Luma', 'Luma Labs API', 1);
IF NOT EXISTS (SELECT 1 FROM finance_dimensions WHERE element_name = 'LotSource' AND element_value = 'purchase')
  INSERT INTO finance_dimensions (element_name, element_value, element_description, element_status)
  VALUES ('LotSource', 'purchase', 'Customer credit purchase', 1);
IF NOT EXISTS (SELECT 1 FROM finance_dimensions WHERE element_name = 'LotSource' AND element_value = 'grant_owner')
  INSERT INTO finance_dimensions (element_name, element_value, element_description, element_status)
  VALUES ('LotSource', 'grant_owner', 'Owner/admin credit grant', 1);
IF NOT EXISTS (SELECT 1 FROM finance_dimensions WHERE element_name = 'LotSource' AND element_value = 'grant_promo')
  INSERT INTO finance_dimensions (element_name, element_value, element_description, element_status)
  VALUES ('LotSource', 'grant_promo', 'Promotional credit grant', 1);
IF NOT EXISTS (SELECT 1 FROM finance_dimensions WHERE element_name = 'LotSource' AND element_value = 'grant_signup')
  INSERT INTO finance_dimensions (element_name, element_value, element_description, element_status)
  VALUES ('LotSource', 'grant_signup', 'Signup bonus credits', 1);
GO

-- ============================================================
-- Credit lots (FIFO subledger per spec §5)
-- ============================================================
IF OBJECT_ID(N'[dbo].[finance_credit_lots]', N'U') IS NULL
BEGIN
  CREATE TABLE [dbo].[finance_credit_lots] (
    [recid]                     BIGINT IDENTITY(1,1) NOT NULL,
    [users_guid]                UNIQUEIDENTIFIER NOT NULL,
    [element_lot_number]        NVARCHAR(64) NOT NULL,
    [element_source_type]       NVARCHAR(64) NOT NULL,
    [element_credits_original]  INT NOT NULL,
    [element_credits_remaining] INT NOT NULL,
    [element_unit_price]        DECIMAL(19,5) NOT NULL DEFAULT (0),
    [element_total_paid]        DECIMAL(19,5) NOT NULL DEFAULT (0),
    [element_currency]          NVARCHAR(3) NOT NULL DEFAULT ('USD'),
    [element_expires_at]        DATETIMEOFFSET(7) NULL,
    [element_expired]           BIT NOT NULL DEFAULT (0),
    [element_source_id]         NVARCHAR(256) NULL,
    [numbers_recid]             BIGINT NULL,
    [element_status]            TINYINT NOT NULL DEFAULT (1),
    [element_created_on]        DATETIMEOFFSET(7) NOT NULL DEFAULT (SYSUTCDATETIME()),
    [element_modified_on]       DATETIMEOFFSET(7) NOT NULL DEFAULT (SYSUTCDATETIME()),
    CONSTRAINT [PK_finance_credit_lots] PRIMARY KEY ([recid]),
    CONSTRAINT [FK_credit_lots_users] FOREIGN KEY ([users_guid])
      REFERENCES [dbo].[account_users] ([element_guid]),
    CONSTRAINT [FK_credit_lots_numbers] FOREIGN KEY ([numbers_recid])
      REFERENCES [dbo].[finance_numbers] ([recid])
  );
END;
GO

IF NOT EXISTS (
  SELECT 1 FROM sys.indexes
  WHERE object_id = OBJECT_ID(N'[dbo].[finance_credit_lots]')
    AND name = N'UQ_credit_lots_lot_number'
)
BEGIN
  CREATE UNIQUE INDEX [UQ_credit_lots_lot_number] ON [dbo].[finance_credit_lots] ([element_lot_number]);
END;
GO

IF NOT EXISTS (
  SELECT 1 FROM sys.indexes
  WHERE object_id = OBJECT_ID(N'[dbo].[finance_credit_lots]')
    AND name = N'IX_credit_lots_users_guid'
)
BEGIN
  CREATE INDEX [IX_credit_lots_users_guid] ON [dbo].[finance_credit_lots] ([users_guid]);
END;
GO

IF NOT EXISTS (
  SELECT 1 FROM sys.indexes
  WHERE object_id = OBJECT_ID(N'[dbo].[finance_credit_lots]')
    AND name = N'IX_credit_lots_fifo'
)
BEGIN
  CREATE INDEX [IX_credit_lots_fifo] ON [dbo].[finance_credit_lots]
    ([users_guid], [element_expired], [element_credits_remaining])
    WHERE [element_expired] = 0 AND [element_credits_remaining] > 0;
END;
GO

IF OBJECT_ID(N'[dbo].[finance_credit_lot_events]', N'U') IS NULL
BEGIN
  CREATE TABLE [dbo].[finance_credit_lot_events] (
    [recid]                BIGINT IDENTITY(1,1) NOT NULL,
    [lots_recid]           BIGINT NOT NULL,
    [element_event_type]   NVARCHAR(32) NOT NULL,
    [element_credits]      INT NOT NULL,
    [element_unit_price]   DECIMAL(19,5) NOT NULL DEFAULT (0),
    [element_description]  NVARCHAR(512) NULL,
    [element_actor_guid]   UNIQUEIDENTIFIER NULL,
    [journals_recid]       BIGINT NULL,
    [element_created_on]   DATETIMEOFFSET(7) NOT NULL DEFAULT (SYSUTCDATETIME()),
    CONSTRAINT [PK_finance_credit_lot_events] PRIMARY KEY ([recid]),
    CONSTRAINT [FK_lot_events_lots] FOREIGN KEY ([lots_recid])
      REFERENCES [dbo].[finance_credit_lots] ([recid]),
    CONSTRAINT [FK_lot_events_journals] FOREIGN KEY ([journals_recid])
      REFERENCES [dbo].[finance_journals] ([recid])
  );
END;
GO

IF NOT EXISTS (
  SELECT 1 FROM sys.indexes
  WHERE object_id = OBJECT_ID(N'[dbo].[finance_credit_lot_events]')
    AND name = N'IX_lot_events_lots_recid'
)
BEGIN
  CREATE INDEX [IX_lot_events_lots_recid] ON [dbo].[finance_credit_lot_events] ([lots_recid]);
END;
GO

-- ============================================================
-- Schema reflection metadata for credit lots tables
-- ============================================================
IF NOT EXISTS (
  SELECT 1 FROM system_schema_tables WHERE element_name = 'finance_credit_lots' AND element_schema = 'dbo'
)
BEGIN
  INSERT INTO system_schema_tables (element_name, element_schema)
  VALUES ('finance_credit_lots', 'dbo');
END;

IF NOT EXISTS (
  SELECT 1 FROM system_schema_tables WHERE element_name = 'finance_credit_lot_events' AND element_schema = 'dbo'
)
BEGIN
  INSERT INTO system_schema_tables (element_name, element_schema)
  VALUES ('finance_credit_lot_events', 'dbo');
END;
GO

DELETE FROM system_schema_columns
WHERE tables_recid IN (
  (SELECT recid FROM system_schema_tables WHERE element_name = 'finance_credit_lots' AND element_schema = 'dbo'),
  (SELECT recid FROM system_schema_tables WHERE element_name = 'finance_credit_lot_events' AND element_schema = 'dbo')
);
GO

INSERT INTO system_schema_columns (
  tables_recid,
  edt_mappings_recid,
  element_name,
  element_ordinal,
  element_nullable,
  element_default,
  element_max_length,
  element_is_primary_key,
  element_is_identity
)
VALUES
  ((SELECT recid FROM system_schema_tables WHERE element_name = 'finance_credit_lots' AND element_schema = 'dbo'), (SELECT recid FROM system_edt_mappings WHERE element_name = 'INT64_IDENTITY'), 'recid', 1, 0, NULL, NULL, 1, 1),
  ((SELECT recid FROM system_schema_tables WHERE element_name = 'finance_credit_lots' AND element_schema = 'dbo'), (SELECT recid FROM system_edt_mappings WHERE element_name = 'UUID'), 'users_guid', 2, 0, NULL, NULL, 0, 0),
  ((SELECT recid FROM system_schema_tables WHERE element_name = 'finance_credit_lots' AND element_schema = 'dbo'), (SELECT recid FROM system_edt_mappings WHERE element_name = 'STRING'), 'element_lot_number', 3, 0, NULL, 64, 0, 0),
  ((SELECT recid FROM system_schema_tables WHERE element_name = 'finance_credit_lots' AND element_schema = 'dbo'), (SELECT recid FROM system_edt_mappings WHERE element_name = 'STRING'), 'element_source_type', 4, 0, NULL, 64, 0, 0),
  ((SELECT recid FROM system_schema_tables WHERE element_name = 'finance_credit_lots' AND element_schema = 'dbo'), (SELECT recid FROM system_edt_mappings WHERE element_name = 'INT32'), 'element_credits_original', 5, 0, NULL, NULL, 0, 0),
  ((SELECT recid FROM system_schema_tables WHERE element_name = 'finance_credit_lots' AND element_schema = 'dbo'), (SELECT recid FROM system_edt_mappings WHERE element_name = 'INT32'), 'element_credits_remaining', 6, 0, NULL, NULL, 0, 0),
  ((SELECT recid FROM system_schema_tables WHERE element_name = 'finance_credit_lots' AND element_schema = 'dbo'), (SELECT recid FROM system_edt_mappings WHERE element_name = 'DECIMAL_19_5'), 'element_unit_price', 7, 0, '((0))', NULL, 0, 0),
  ((SELECT recid FROM system_schema_tables WHERE element_name = 'finance_credit_lots' AND element_schema = 'dbo'), (SELECT recid FROM system_edt_mappings WHERE element_name = 'DECIMAL_19_5'), 'element_total_paid', 8, 0, '((0))', NULL, 0, 0),
  ((SELECT recid FROM system_schema_tables WHERE element_name = 'finance_credit_lots' AND element_schema = 'dbo'), (SELECT recid FROM system_edt_mappings WHERE element_name = 'STRING'), 'element_currency', 9, 0, '(''USD'')', 3, 0, 0),
  ((SELECT recid FROM system_schema_tables WHERE element_name = 'finance_credit_lots' AND element_schema = 'dbo'), (SELECT recid FROM system_edt_mappings WHERE element_name = 'DATETIME_TZ'), 'element_expires_at', 10, 1, NULL, NULL, 0, 0),
  ((SELECT recid FROM system_schema_tables WHERE element_name = 'finance_credit_lots' AND element_schema = 'dbo'), (SELECT recid FROM system_edt_mappings WHERE element_name = 'BOOL'), 'element_expired', 11, 0, '((0))', NULL, 0, 0),
  ((SELECT recid FROM system_schema_tables WHERE element_name = 'finance_credit_lots' AND element_schema = 'dbo'), (SELECT recid FROM system_edt_mappings WHERE element_name = 'STRING'), 'element_source_id', 12, 1, NULL, 256, 0, 0),
  ((SELECT recid FROM system_schema_tables WHERE element_name = 'finance_credit_lots' AND element_schema = 'dbo'), (SELECT recid FROM system_edt_mappings WHERE element_name = 'INT64'), 'numbers_recid', 13, 1, NULL, NULL, 0, 0),
  ((SELECT recid FROM system_schema_tables WHERE element_name = 'finance_credit_lots' AND element_schema = 'dbo'), (SELECT recid FROM system_edt_mappings WHERE element_name = 'INT8'), 'element_status', 14, 0, '((1))', NULL, 0, 0),
  ((SELECT recid FROM system_schema_tables WHERE element_name = 'finance_credit_lots' AND element_schema = 'dbo'), (SELECT recid FROM system_edt_mappings WHERE element_name = 'DATETIME_TZ'), 'element_created_on', 15, 0, '(sysutcdatetime())', NULL, 0, 0),
  ((SELECT recid FROM system_schema_tables WHERE element_name = 'finance_credit_lots' AND element_schema = 'dbo'), (SELECT recid FROM system_edt_mappings WHERE element_name = 'DATETIME_TZ'), 'element_modified_on', 16, 0, '(sysutcdatetime())', NULL, 0, 0),

  ((SELECT recid FROM system_schema_tables WHERE element_name = 'finance_credit_lot_events' AND element_schema = 'dbo'), (SELECT recid FROM system_edt_mappings WHERE element_name = 'INT64_IDENTITY'), 'recid', 1, 0, NULL, NULL, 1, 1),
  ((SELECT recid FROM system_schema_tables WHERE element_name = 'finance_credit_lot_events' AND element_schema = 'dbo'), (SELECT recid FROM system_edt_mappings WHERE element_name = 'INT64'), 'lots_recid', 2, 0, NULL, NULL, 0, 0),
  ((SELECT recid FROM system_schema_tables WHERE element_name = 'finance_credit_lot_events' AND element_schema = 'dbo'), (SELECT recid FROM system_edt_mappings WHERE element_name = 'STRING'), 'element_event_type', 3, 0, NULL, 32, 0, 0),
  ((SELECT recid FROM system_schema_tables WHERE element_name = 'finance_credit_lot_events' AND element_schema = 'dbo'), (SELECT recid FROM system_edt_mappings WHERE element_name = 'INT32'), 'element_credits', 4, 0, NULL, NULL, 0, 0),
  ((SELECT recid FROM system_schema_tables WHERE element_name = 'finance_credit_lot_events' AND element_schema = 'dbo'), (SELECT recid FROM system_edt_mappings WHERE element_name = 'DECIMAL_19_5'), 'element_unit_price', 5, 0, '((0))', NULL, 0, 0),
  ((SELECT recid FROM system_schema_tables WHERE element_name = 'finance_credit_lot_events' AND element_schema = 'dbo'), (SELECT recid FROM system_edt_mappings WHERE element_name = 'STRING'), 'element_description', 6, 1, NULL, 512, 0, 0),
  ((SELECT recid FROM system_schema_tables WHERE element_name = 'finance_credit_lot_events' AND element_schema = 'dbo'), (SELECT recid FROM system_edt_mappings WHERE element_name = 'UUID'), 'element_actor_guid', 7, 1, NULL, NULL, 0, 0),
  ((SELECT recid FROM system_schema_tables WHERE element_name = 'finance_credit_lot_events' AND element_schema = 'dbo'), (SELECT recid FROM system_edt_mappings WHERE element_name = 'INT64'), 'journals_recid', 8, 1, NULL, NULL, 0, 0),
  ((SELECT recid FROM system_schema_tables WHERE element_name = 'finance_credit_lot_events' AND element_schema = 'dbo'), (SELECT recid FROM system_edt_mappings WHERE element_name = 'DATETIME_TZ'), 'element_created_on', 9, 0, '(sysutcdatetime())', NULL, 0, 0);
GO

DELETE FROM system_schema_indexes
WHERE tables_recid IN (
  (SELECT recid FROM system_schema_tables WHERE element_name = 'finance_credit_lots' AND element_schema = 'dbo'),
  (SELECT recid FROM system_schema_tables WHERE element_name = 'finance_credit_lot_events' AND element_schema = 'dbo')
);
GO

INSERT INTO system_schema_indexes (tables_recid, element_name, element_columns, element_is_unique)
VALUES
  ((SELECT recid FROM system_schema_tables WHERE element_name = 'finance_credit_lots' AND element_schema = 'dbo'), 'UQ_credit_lots_lot_number', 'element_lot_number', 1),
  ((SELECT recid FROM system_schema_tables WHERE element_name = 'finance_credit_lots' AND element_schema = 'dbo'), 'IX_credit_lots_users_guid', 'users_guid', 0),
  ((SELECT recid FROM system_schema_tables WHERE element_name = 'finance_credit_lots' AND element_schema = 'dbo'), 'IX_credit_lots_fifo', 'users_guid,element_expired,element_credits_remaining', 0),
  ((SELECT recid FROM system_schema_tables WHERE element_name = 'finance_credit_lot_events' AND element_schema = 'dbo'), 'IX_lot_events_lots_recid', 'lots_recid', 0);
GO

DELETE FROM system_schema_foreign_keys
WHERE tables_recid IN (
  (SELECT recid FROM system_schema_tables WHERE element_name = 'finance_credit_lots' AND element_schema = 'dbo'),
  (SELECT recid FROM system_schema_tables WHERE element_name = 'finance_credit_lot_events' AND element_schema = 'dbo')
);
GO

INSERT INTO system_schema_foreign_keys (tables_recid, element_column_name, referenced_tables_recid, element_referenced_column)
VALUES
  ((SELECT recid FROM system_schema_tables WHERE element_name = 'finance_credit_lots' AND element_schema = 'dbo'), 'users_guid', (SELECT recid FROM system_schema_tables WHERE element_name = 'account_users' AND element_schema = 'dbo'), 'element_guid'),
  ((SELECT recid FROM system_schema_tables WHERE element_name = 'finance_credit_lots' AND element_schema = 'dbo'), 'numbers_recid', (SELECT recid FROM system_schema_tables WHERE element_name = 'finance_numbers' AND element_schema = 'dbo'), 'recid'),
  ((SELECT recid FROM system_schema_tables WHERE element_name = 'finance_credit_lot_events' AND element_schema = 'dbo'), 'lots_recid', (SELECT recid FROM system_schema_tables WHERE element_name = 'finance_credit_lots' AND element_schema = 'dbo'), 'recid'),
  ((SELECT recid FROM system_schema_tables WHERE element_name = 'finance_credit_lot_events' AND element_schema = 'dbo'), 'journals_recid', (SELECT recid FROM system_schema_tables WHERE element_name = 'finance_journals' AND element_schema = 'dbo'), 'recid');
GO
