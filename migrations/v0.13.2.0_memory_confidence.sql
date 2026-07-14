-- ============================================================================
-- elideus-group v0.13.2.0 — Confidence-Weighted Memory + Contradiction Records
-- Date: 2026-07-13
-- FDD: FDD-ORACLE-MEM-CONFLICT-01 (Phase 1 — schema + weighting foundation)
--
-- Core principle (FDD §1): WEIGHT IS CONFIDENCE, NOT TRUTH. Confidence is a
-- scalar attached to a claim; it gates how loudly the system objects to a
-- contradiction, never whether a claim is correct. A high-confidence claim can
-- be wrong; a human statement is 1.0 as a SOURCE property (a human can typo).
--
-- What this migration builds (Phase 1 — foundation only, no new MCP tools yet):
--   1. agent_memory_entries gains claim-level attributes:
--        pub_confidence (0..1 scalar), pub_confidence_source, pub_node_state
--        (active|conflict|historical|retired), pub_ref_count (inbound authority).
--   2. agent_memory_references — the mind-map edge table. Inbound cites/supports
--        edges are what confer authority (→ pub_ref_count). Authority = confidence.
--   3. agent_memory_contradictions — FIRST-CLASS conflict records (FDD §3). Both
--        claims persist; neither is destroyed; the node enters CONFLICT. Carries
--        the open→resolved lifecycle + the resolution class (FDD §4:
--        correction | new_version | typo | contradiction | misunderstanding).
--   4. Initial weighting: per-kind base confidence backfilled onto existing rows.
--
-- Phase 2 (NOT in this migration) will wire the write/read behaviour:
--   memory_link_add, memory_conflict_open, memory_conflict_resolve,
--   memory_conflicts_list, plus pub_ref_count recompute. The tables/columns here
--   are the substrate those tools operate on.
--
-- Design invariants enforced here (FDD §6):
--   #4 No write path silently overwrites a claim with inbound references — there
--      is NO destructive UPDATE of entry bodies in this schema; a challenge is
--      recorded as a contradiction row (Phase 2), not an overwrite.
--   #5 CONFLICT is a persistent, queryable state (pub_node_state / contradictions
--      table), not a transient exception.
--
-- Conventions (match v0.13.0.0/v0.13.1.0 and the live reflection registry):
--   UUID5 namespace : DECAFBAD-CAFE-FADE-BABE-C0FFEE420B67
--   key formats     : table:<name> · column:<table>.<col> · index:<table>.<name>
--                     · constraint:<table>.<fk_column>
--   timestamps      : DATETIMEOFFSET(7) DEFAULT SYSUTCDATETIME()
--   vocab columns   : documented in comments, NOT DB-CHECK-constrained (matches
--                     pub_kind) so the vocabulary stays tunable while we iterate.
--   This migration is additive and idempotent (safe to re-run).
-- ============================================================================

SET ANSI_NULLS ON;
SET QUOTED_IDENTIFIER ON;
GO


-- ============================================================================
-- PHASE 1: DDL
-- ============================================================================

-- 1a: extend agent_memory_entries with claim-level attributes ----------------
IF COL_LENGTH(N'dbo.agent_memory_entries', N'pub_confidence') IS NULL
  ALTER TABLE [dbo].[agent_memory_entries]
    ADD [pub_confidence] DECIMAL(19,5) NOT NULL
        CONSTRAINT [DF_ame_confidence] DEFAULT 0.70;   -- 0..1 CONFIDENCE, never truth
GO

IF COL_LENGTH(N'dbo.agent_memory_entries', N'pub_confidence_source') IS NULL
  ALTER TABLE [dbo].[agent_memory_entries]
    ADD [pub_confidence_source] NVARCHAR(32) NOT NULL
        CONSTRAINT [DF_ame_confidence_source] DEFAULT N'agent';  -- agent|human|derived|imported
GO

IF COL_LENGTH(N'dbo.agent_memory_entries', N'pub_node_state') IS NULL
  ALTER TABLE [dbo].[agent_memory_entries]
    ADD [pub_node_state] NVARCHAR(24) NOT NULL
        CONSTRAINT [DF_ame_node_state] DEFAULT N'active';  -- active|conflict|historical|retired
GO

IF COL_LENGTH(N'dbo.agent_memory_entries', N'pub_ref_count') IS NULL
  ALTER TABLE [dbo].[agent_memory_entries]
    ADD [pub_ref_count] INT NOT NULL
        CONSTRAINT [DF_ame_ref_count] DEFAULT 0;  -- materialised inbound-authority count (Phase 2 maintains)
GO

-- 1b: agent_memory_references — the mind-map edge table -----------------------
--   ref_from_guid --(pub_ref_kind, pub_weight)--> ref_to_guid
--   Inbound active cites/supports edges to a node ARE its authority/confidence.
IF OBJECT_ID(N'[dbo].[agent_memory_references]', N'U') IS NULL
BEGIN
  CREATE TABLE [dbo].[agent_memory_references] (
    [key_guid]         UNIQUEIDENTIFIER  NOT NULL CONSTRAINT [DF_amr_key_guid]     DEFAULT NEWID(),
    [ref_from_guid]    UNIQUEIDENTIFIER  NOT NULL,   -- referencing node
    [ref_to_guid]      UNIQUEIDENTIFIER  NOT NULL,   -- referenced node (gains authority)
    [pub_ref_kind]     NVARCHAR(32)      NOT NULL CONSTRAINT [DF_amr_ref_kind]     DEFAULT N'cites',
      -- cites|supports|supersedes|derived_from|contradicts|disambiguates
    [pub_weight]       DECIMAL(19,5)     NOT NULL CONSTRAINT [DF_amr_weight]       DEFAULT 1.0,
    [pub_is_active]    BIT               NOT NULL CONSTRAINT [DF_amr_is_active]    DEFAULT 1,
    [priv_created_on]  DATETIMEOFFSET(7) NOT NULL CONSTRAINT [DF_amr_created_on]   DEFAULT SYSUTCDATETIME(),
    [priv_modified_on] DATETIMEOFFSET(7) NOT NULL CONSTRAINT [DF_amr_modified_on]  DEFAULT SYSUTCDATETIME(),
    CONSTRAINT [PK_agent_memory_references] PRIMARY KEY CLUSTERED ([key_guid]),
    CONSTRAINT [FK_agent_memory_references_from] FOREIGN KEY ([ref_from_guid])
      REFERENCES [dbo].[agent_memory_entries] ([key_guid]),
    CONSTRAINT [FK_agent_memory_references_to] FOREIGN KEY ([ref_to_guid])
      REFERENCES [dbo].[agent_memory_entries] ([key_guid])
  );
END
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'IX_agent_memory_references_from'
               AND object_id = OBJECT_ID(N'[dbo].[agent_memory_references]'))
  CREATE INDEX [IX_agent_memory_references_from] ON [dbo].[agent_memory_references] ([ref_from_guid]);
GO
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'IX_agent_memory_references_to'
               AND object_id = OBJECT_ID(N'[dbo].[agent_memory_references]'))
  CREATE INDEX [IX_agent_memory_references_to] ON [dbo].[agent_memory_references] ([ref_to_guid], [pub_is_active]);
GO
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'UQ_agent_memory_references_edge'
               AND object_id = OBJECT_ID(N'[dbo].[agent_memory_references]'))
  CREATE UNIQUE INDEX [UQ_agent_memory_references_edge]
    ON [dbo].[agent_memory_references] ([ref_from_guid], [ref_to_guid], [pub_ref_kind]);
GO

-- 1c: agent_memory_contradictions — first-class conflict records --------------
--   Ties two competing claims (both persist). pub_state carries the conflict
--   lifecycle; pub_resolution carries the classified transition once resolved.
IF OBJECT_ID(N'[dbo].[agent_memory_contradictions]', N'U') IS NULL
BEGIN
  CREATE TABLE [dbo].[agent_memory_contradictions] (
    [key_guid]            UNIQUEIDENTIFIER  NOT NULL CONSTRAINT [DF_amc_key_guid]    DEFAULT NEWID(),
    [pub_project]         NVARCHAR(128)     NOT NULL,
    [ref_claim_a_guid]    UNIQUEIDENTIFIER  NOT NULL,   -- incumbent claim (usually the higher-authority one)
    [ref_claim_b_guid]    UNIQUEIDENTIFIER  NOT NULL,   -- challenger claim
    [pub_state]           NVARCHAR(16)      NOT NULL CONSTRAINT [DF_amc_state]       DEFAULT N'open',
      -- open|resolved
    [pub_resolution]      NVARCHAR(24)      NULL,        -- NULL while open; on resolve:
      -- correction|new_version|typo|contradiction|misunderstanding  (FDD §4)
    [pub_resolution_note] NVARCHAR(MAX)     NULL,
    [pub_resolved_source] NVARCHAR(128)     NULL,        -- who/what resolved (human authority)
    [priv_created_on]     DATETIMEOFFSET(7) NOT NULL CONSTRAINT [DF_amc_created_on]  DEFAULT SYSUTCDATETIME(),
    [priv_resolved_on]    DATETIMEOFFSET(7) NULL,
    [priv_modified_on]    DATETIMEOFFSET(7) NOT NULL CONSTRAINT [DF_amc_modified_on] DEFAULT SYSUTCDATETIME(),
    CONSTRAINT [PK_agent_memory_contradictions] PRIMARY KEY CLUSTERED ([key_guid]),
    CONSTRAINT [FK_agent_memory_contradictions_a] FOREIGN KEY ([ref_claim_a_guid])
      REFERENCES [dbo].[agent_memory_entries] ([key_guid]),
    CONSTRAINT [FK_agent_memory_contradictions_b] FOREIGN KEY ([ref_claim_b_guid])
      REFERENCES [dbo].[agent_memory_entries] ([key_guid])
  );
END
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'IX_agent_memory_contradictions_state'
               AND object_id = OBJECT_ID(N'[dbo].[agent_memory_contradictions]'))
  CREATE INDEX [IX_agent_memory_contradictions_state]
    ON [dbo].[agent_memory_contradictions] ([pub_state], [pub_project]);  -- the "interrupt the human" queue
GO
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'IX_agent_memory_contradictions_a'
               AND object_id = OBJECT_ID(N'[dbo].[agent_memory_contradictions]'))
  CREATE INDEX [IX_agent_memory_contradictions_a] ON [dbo].[agent_memory_contradictions] ([ref_claim_a_guid]);
GO
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'IX_agent_memory_contradictions_b'
               AND object_id = OBJECT_ID(N'[dbo].[agent_memory_contradictions]'))
  CREATE INDEX [IX_agent_memory_contradictions_b] ON [dbo].[agent_memory_contradictions] ([ref_claim_b_guid]);
GO


-- ============================================================================
-- PHASE 2: Initial weighting ("what is considered important at the start")
--   Per-kind base confidence, applied to pre-existing rows. These numbers MIRROR
--   _BASE_CONFIDENCE in server/modules/memory_module.py (single logical policy;
--   keep the two in sync). Guarded to pub_confidence_source='agent' so a human-
--   set confidence is never clobbered on re-run.
-- ============================================================================

UPDATE [dbo].[agent_memory_entries]
SET [pub_confidence] = CASE [pub_kind]
      WHEN N'invariant'       THEN 0.90
      WHEN N'decision'        THEN 0.85
      WHEN N'spec'            THEN 0.80
      WHEN N'reference'       THEN 0.75
      WHEN N'snippet'         THEN 0.70
      WHEN N'note'            THEN 0.60
      WHEN N'session_summary' THEN 0.55
      ELSE 0.70
    END
WHERE [pub_confidence_source] = N'agent';
GO


-- ============================================================================
-- PHASE 3: Reflection registration (system_objects_database_* mirror)
--   oracle_* now reads the LIVE sys.* catalog, so it sees these tables/columns
--   without this block — but the web CMS / object-tree / query-builder still
--   read the mirror, and migrations/AGENTS.md requires registration. Idempotent:
--   scoped DELETE (FK-safe order) then INSERT. Only NEW objects are touched;
--   the existing agent_memory_entries rows (ordinals 1..11) are left intact.
-- ============================================================================

-- EDT type GUIDs (system_objects_types)
DECLARE @T_UUID UNIQUEIDENTIFIER = N'4D2EB10B-363E-5AF4-826A-9294146244E4'; -- uniqueidentifier
DECLARE @T_STR  UNIQUEIDENTIFIER = N'0093B404-1EEE-563D-9135-4B9E7EECA7A2'; -- nvarchar
DECLARE @T_TEXT UNIQUEIDENTIFIER = N'DCA18974-D648-5DFF-AEFB-122C081145AA'; -- nvarchar(max)
DECLARE @T_BOOL UNIQUEIDENTIFIER = N'12B2F03B-E315-50A5-B631-E6B1EB961A17'; -- bit
DECLARE @T_DTZ  UNIQUEIDENTIFIER = N'70F890D3-5AB5-5250-860E-4F7F9624190C'; -- datetimeoffset(7)
DECLARE @T_INT  UNIQUEIDENTIFIER = N'E3EDE0CE-2A03-501E-A796-3487BEA03B7B'; -- int
DECLARE @T_DEC  UNIQUEIDENTIFIER = N'A79190A1-FB3B-580C-8A24-445D590715BD'; -- decimal(19,5)

-- Table GUIDs (uuid5 'table:<name>')
DECLARE @TBL_ENTRIES UNIQUEIDENTIFIER = N'07B0D4B9-4D3B-569E-926D-551035A6357B'; -- existing
DECLARE @TBL_REFS    UNIQUEIDENTIFIER = N'0D52ACB1-CE0F-5878-908E-314AD41A0A12'; -- agent_memory_references
DECLARE @TBL_CONTRA  UNIQUEIDENTIFIER = N'FB897F33-8EC5-543F-B0D6-DB9C7B34104B'; -- agent_memory_contradictions

-- Cross-referenced column GUID for the FKs (agent_memory_entries.key_guid)
DECLARE @COL_ENTRIES_PK UNIQUEIDENTIFIER = N'13814960-BD02-5C7A-8FF7-2F49762C33B0';

-- New agent_memory_entries column GUIDs (uuid5 'column:agent_memory_entries.<col>')
DECLARE @COL_E_CONF   UNIQUEIDENTIFIER = N'7FCABB1B-5941-57C5-AB5A-69F162DB8E6A';
DECLARE @COL_E_CSRC   UNIQUEIDENTIFIER = N'C79B15D8-C527-5D2D-9F07-F45ECF05D797';
DECLARE @COL_E_STATE  UNIQUEIDENTIFIER = N'1D5530AD-BDA3-56E9-8C8C-6291B5151F32';
DECLARE @COL_E_REFCNT UNIQUEIDENTIFIER = N'78D4F71A-0A75-5A23-88E4-F37BE8DB7D2E';

-- Idempotent cleanup (FK-safe order). New tables: full child sweep. Entries: only the 4 new columns.
DELETE FROM [dbo].[system_objects_database_constraints] WHERE [ref_table_guid] IN (@TBL_REFS, @TBL_CONTRA);
DELETE FROM [dbo].[system_objects_database_indexes]     WHERE [ref_table_guid] IN (@TBL_REFS, @TBL_CONTRA);
DELETE FROM [dbo].[system_objects_database_columns]     WHERE [ref_table_guid] IN (@TBL_REFS, @TBL_CONTRA);
DELETE FROM [dbo].[system_objects_database_columns]     WHERE [key_guid] IN (@COL_E_CONF, @COL_E_CSRC, @COL_E_STATE, @COL_E_REFCNT);
DELETE FROM [dbo].[system_objects_database_tables]      WHERE [key_guid] IN (@TBL_REFS, @TBL_CONTRA);

-- 3a: tables
INSERT INTO [dbo].[system_objects_database_tables] ([key_guid], [pub_name], [pub_schema]) VALUES
(@TBL_REFS,   N'agent_memory_references',     N'dbo'),
(@TBL_CONTRA, N'agent_memory_contradictions', N'dbo');

-- 3b: agent_memory_entries — the 4 NEW columns (ordinals continue at 12)
INSERT INTO [dbo].[system_objects_database_columns] ([key_guid],[ref_table_guid],[ref_type_guid],[pub_name],[pub_ordinal],[pub_is_nullable],[pub_is_primary_key],[pub_is_identity],[pub_default],[pub_max_length]) VALUES
(@COL_E_CONF,  @TBL_ENTRIES,@T_DEC,N'pub_confidence',        12,0,0,0,N'0.70', NULL),
(@COL_E_CSRC,  @TBL_ENTRIES,@T_STR,N'pub_confidence_source', 13,0,0,0,N'agent',32),
(@COL_E_STATE, @TBL_ENTRIES,@T_STR,N'pub_node_state',        14,0,0,0,N'active',24),
(@COL_E_REFCNT,@TBL_ENTRIES,@T_INT,N'pub_ref_count',         15,0,0,0,N'0',    NULL);

-- 3c: agent_memory_references columns
INSERT INTO [dbo].[system_objects_database_columns] ([key_guid],[ref_table_guid],[ref_type_guid],[pub_name],[pub_ordinal],[pub_is_nullable],[pub_is_primary_key],[pub_is_identity],[pub_default],[pub_max_length]) VALUES
(N'5D1D26A2-F969-5101-B41F-76521B3F6B88',@TBL_REFS,@T_UUID,N'key_guid',        1,0,1,0,N'NEWID()',          NULL),
(N'37A13229-EC04-51B2-88DD-652FCCB7B357',@TBL_REFS,@T_UUID,N'ref_from_guid',   2,0,0,0,NULL,               NULL),
(N'E6AC4C78-22F5-5CB9-9C87-541107B38DF5',@TBL_REFS,@T_UUID,N'ref_to_guid',     3,0,0,0,NULL,               NULL),
(N'F133AF9F-0863-5582-AECD-FA7473F0FE1D',@TBL_REFS,@T_STR, N'pub_ref_kind',    4,0,0,0,N'cites',           32),
(N'012A0C41-6EB0-5136-969A-1F6E57297561',@TBL_REFS,@T_DEC, N'pub_weight',      5,0,0,0,N'1.0',             NULL),
(N'AA9DCE7D-7DA3-50F4-9758-3C4DC2034FCD',@TBL_REFS,@T_BOOL,N'pub_is_active',   6,0,0,0,N'1',               NULL),
(N'60F001EF-DE2D-533B-87D6-D7F2238B21B0',@TBL_REFS,@T_DTZ, N'priv_created_on', 7,0,0,0,N'SYSUTCDATETIME()',NULL),
(N'CABA1021-0D02-5B9D-BF47-4E31FD361A0B',@TBL_REFS,@T_DTZ, N'priv_modified_on',8,0,0,0,N'SYSUTCDATETIME()',NULL);

-- 3d: agent_memory_contradictions columns
INSERT INTO [dbo].[system_objects_database_columns] ([key_guid],[ref_table_guid],[ref_type_guid],[pub_name],[pub_ordinal],[pub_is_nullable],[pub_is_primary_key],[pub_is_identity],[pub_default],[pub_max_length]) VALUES
(N'30D78724-6FE1-5924-9649-3EBC28C927A0',@TBL_CONTRA,@T_UUID,N'key_guid',            1, 0,1,0,N'NEWID()',          NULL),
(N'08D0A9D1-44D7-576D-9A44-4AE0886C00E5',@TBL_CONTRA,@T_STR, N'pub_project',         2, 0,0,0,NULL,               128),
(N'2ADF2D84-4A5F-5473-AA10-4CFFCC8D79CC',@TBL_CONTRA,@T_UUID,N'ref_claim_a_guid',    3, 0,0,0,NULL,               NULL),
(N'7CECFE23-975C-56C6-AF3E-0456F4B59A54',@TBL_CONTRA,@T_UUID,N'ref_claim_b_guid',    4, 0,0,0,NULL,               NULL),
(N'06648512-4339-5BC4-8048-27C4C0E03C25',@TBL_CONTRA,@T_STR, N'pub_state',           5, 0,0,0,N'open',            16),
(N'58A37FB8-4402-5D23-8FC0-2CED78B12072',@TBL_CONTRA,@T_STR, N'pub_resolution',      6, 1,0,0,NULL,               24),
(N'5FCC36FB-EEFD-59AE-91E2-C1BF92EBDFAA',@TBL_CONTRA,@T_TEXT,N'pub_resolution_note', 7, 1,0,0,NULL,               NULL),
(N'8D6A45EF-5BA3-5A83-B088-B4D622D65A80',@TBL_CONTRA,@T_STR, N'pub_resolved_source', 8, 1,0,0,NULL,               128),
(N'31B04F11-662D-5524-9732-BEC68A03B394',@TBL_CONTRA,@T_DTZ, N'priv_created_on',     9, 0,0,0,N'SYSUTCDATETIME()',NULL),
(N'4FBD7194-C529-588C-94B6-44F38C154079',@TBL_CONTRA,@T_DTZ, N'priv_resolved_on',    10,1,0,0,NULL,               NULL),
(N'F3D478D5-D998-5842-A5A4-D67B1128F1C4',@TBL_CONTRA,@T_DTZ, N'priv_modified_on',    11,0,0,0,N'SYSUTCDATETIME()',NULL);

-- 3e: indexes
INSERT INTO [dbo].[system_objects_database_indexes] ([key_guid],[ref_table_guid],[pub_name],[pub_columns],[pub_is_unique]) VALUES
(N'448801CE-E609-50B0-AB42-38FC6680C468',@TBL_REFS,  N'IX_agent_memory_references_from',      N'ref_from_guid',                     0),
(N'22576CC8-0453-5977-A152-03118B992D1D',@TBL_REFS,  N'IX_agent_memory_references_to',        N'ref_to_guid,pub_is_active',         0),
(N'DADED843-E308-5E8C-ADE2-F58279EF036A',@TBL_REFS,  N'UQ_agent_memory_references_edge',      N'ref_from_guid,ref_to_guid,pub_ref_kind',1),
(N'98408E05-379F-549C-A0ED-02FD083C6028',@TBL_CONTRA,N'IX_agent_memory_contradictions_state', N'pub_state,pub_project',             0),
(N'7CC4EAEC-A34A-5E26-8D34-853B439384BD',@TBL_CONTRA,N'IX_agent_memory_contradictions_a',     N'ref_claim_a_guid',                  0),
(N'69EB535F-7EF6-57A3-B975-FFE36725668D',@TBL_CONTRA,N'IX_agent_memory_contradictions_b',     N'ref_claim_b_guid',                  0);

-- 3f: foreign keys (all reference agent_memory_entries.key_guid)
INSERT INTO [dbo].[system_objects_database_constraints] ([key_guid],[ref_table_guid],[ref_column_guid],[ref_referenced_table_guid],[ref_referenced_column_guid]) VALUES
(N'E39FA2D7-DD72-570C-9F38-4A46B7F246FF',@TBL_REFS,  N'37A13229-EC04-51B2-88DD-652FCCB7B357',@TBL_ENTRIES,@COL_ENTRIES_PK),
(N'6AF5CC49-D1A0-52F3-A2F6-577B3C73A406',@TBL_REFS,  N'E6AC4C78-22F5-5CB9-9C87-541107B38DF5',@TBL_ENTRIES,@COL_ENTRIES_PK),
(N'7BEEBD8E-CB21-5EFB-A9D1-F773C7F4A484',@TBL_CONTRA,N'2ADF2D84-4A5F-5473-AA10-4CFFCC8D79CC',@TBL_ENTRIES,@COL_ENTRIES_PK),
(N'2CD39435-3AB2-5E50-BEE0-9EE2709B3F60',@TBL_CONTRA,N'7CECFE23-975C-56C6-AF3E-0456F4B59A54',@TBL_ENTRIES,@COL_ENTRIES_PK);
GO


-- ============================================================================
-- PHASE 4: Query re-seed (system_objects_queries, namespace memory.*)
--   Surgical UPDATEs of the existing registered queries so:
--     - memory.entries.insert accepts confidence + confidence_source
--     - the read queries surface the 4 new columns
--   Method/binding rows are unchanged (no new tools this phase). MemoryModule
--   reloads these at startup, so apply this migration BEFORE redeploying code.
-- ============================================================================

-- 4a: insert now writes pub_confidence + pub_confidence_source (2 new trailing params)
UPDATE [dbo].[system_objects_queries] SET
  [pub_query_text] = N'SET NOCOUNT ON;
DECLARE @guid UNIQUEIDENTIFIER = NEWID();
INSERT INTO [dbo].[agent_memory_entries]
  ([key_guid], [ref_thread_guid], [pub_project], [pub_kind], [pub_title], [pub_body], [pub_tags], [pub_source], [pub_confidence], [pub_confidence_source])
VALUES
  (@guid, TRY_CAST(? AS UNIQUEIDENTIFIER), ?, ?, ?, ?, ?, ?, TRY_CAST(? AS DECIMAL(19,5)), ?);
SELECT @guid AS key_guid FOR JSON PATH, WITHOUT_ARRAY_WRAPPER;',
  [pub_parameter_names] = N'thread_guid,project,kind,title,body,tags,source,confidence,confidence_source'
WHERE [pub_name] = N'memory.entries.insert';

-- 4b: get surfaces the new columns
UPDATE [dbo].[system_objects_queries] SET
  [pub_query_text] = N'SELECT key_guid, ref_thread_guid, pub_project, pub_kind, pub_title, pub_body,
       pub_tags, pub_source, pub_confidence, pub_confidence_source, pub_node_state, pub_ref_count,
       pub_is_active, priv_created_on, priv_modified_on
FROM [dbo].[agent_memory_entries]
WHERE key_guid = TRY_CAST(? AS UNIQUEIDENTIFIER)
FOR JSON PATH, WITHOUT_ARRAY_WRAPPER, INCLUDE_NULL_VALUES;'
WHERE [pub_name] = N'memory.entries.get';

-- 4c: search surfaces the new columns (params unchanged)
UPDATE [dbo].[system_objects_queries] SET
  [pub_query_text] = N'SELECT key_guid, ref_thread_guid, pub_project, pub_kind, pub_title, pub_body,
       pub_tags, pub_source, pub_confidence, pub_confidence_source, pub_node_state, pub_ref_count,
       pub_is_active, priv_created_on, priv_modified_on,
       COUNT(*) OVER() AS total
FROM [dbo].[agent_memory_entries]
WHERE pub_is_active = 1
  AND (? IS NULL OR pub_title LIKE ? OR pub_body LIKE ? OR pub_tags LIKE ?)
  AND (? IS NULL OR pub_project = ?)
  AND (? IS NULL OR pub_kind = ?)
  AND (? IS NULL OR pub_tags LIKE ?)
ORDER BY priv_modified_on DESC
OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
FOR JSON PATH, INCLUDE_NULL_VALUES;'
WHERE [pub_name] = N'memory.entries.search';

-- 4d: recent surfaces the new columns
UPDATE [dbo].[system_objects_queries] SET
  [pub_query_text] = N'SELECT TOP (?) key_guid, ref_thread_guid, pub_project, pub_kind, pub_title, pub_body,
       pub_tags, pub_source, pub_confidence, pub_confidence_source, pub_node_state, pub_ref_count,
       pub_is_active, priv_created_on, priv_modified_on
FROM [dbo].[agent_memory_entries]
WHERE pub_is_active = 1
  AND (? IS NULL OR pub_project = ?)
ORDER BY priv_modified_on DESC
FOR JSON PATH, INCLUDE_NULL_VALUES;'
WHERE [pub_name] = N'memory.entries.recent';

-- 4e: thread.get nested entries surface the new columns
UPDATE [dbo].[system_objects_queries] SET
  [pub_query_text] = N'SELECT t.key_guid, t.pub_project, t.pub_title, t.pub_summary, t.pub_is_active,
       t.priv_created_on, t.priv_modified_on,
       (SELECT e.key_guid, e.ref_thread_guid, e.pub_project, e.pub_kind, e.pub_title,
               e.pub_body, e.pub_tags, e.pub_source, e.pub_confidence, e.pub_confidence_source,
               e.pub_node_state, e.pub_ref_count, e.pub_is_active,
               e.priv_created_on, e.priv_modified_on
        FROM [dbo].[agent_memory_entries] e
        WHERE e.ref_thread_guid = t.key_guid AND e.pub_is_active = 1
        ORDER BY e.priv_modified_on DESC
        FOR JSON PATH, INCLUDE_NULL_VALUES) AS entries
FROM [dbo].[agent_memory_threads] t
WHERE t.key_guid = TRY_CAST(? AS UNIQUEIDENTIFIER)
FOR JSON PATH, WITHOUT_ARRAY_WRAPPER, INCLUDE_NULL_VALUES;'
WHERE [pub_name] = N'memory.threads.get';
GO


-- ============================================================================
-- PHASE 5: Verification
-- ============================================================================

-- New columns on agent_memory_entries + backfilled confidence per kind
SELECT pub_kind, pub_confidence, pub_confidence_source, pub_node_state, pub_ref_count, COUNT(*) AS [rows]
FROM [dbo].[agent_memory_entries]
GROUP BY pub_kind, pub_confidence, pub_confidence_source, pub_node_state, pub_ref_count
ORDER BY pub_kind;

-- New tables exist + are empty (Phase 2 tools populate them)
SELECT 'agent_memory_references'     AS [table], COUNT(*) AS [rows] FROM [dbo].[agent_memory_references]
UNION ALL
SELECT 'agent_memory_contradictions' AS [table], COUNT(*) AS [rows] FROM [dbo].[agent_memory_contradictions];

-- Reflection: the 2 new tables + all columns (should list refs=8, contra=11, entries 15 total)
SELECT t.pub_name AS [table], c.pub_ordinal, c.pub_name AS [column], ty.pub_mssql_type,
       c.pub_is_nullable, c.pub_is_primary_key
FROM system_objects_database_tables t
JOIN system_objects_database_columns c ON c.ref_table_guid = t.key_guid
JOIN system_objects_types ty ON ty.key_guid = c.ref_type_guid
WHERE t.pub_name IN (N'agent_memory_references', N'agent_memory_contradictions', N'agent_memory_entries')
ORDER BY t.pub_name, c.pub_ordinal;

-- Registered queries reflect the new columns/params
SELECT pub_name, pub_parameter_names
FROM system_objects_queries
WHERE pub_name IN (N'memory.entries.insert', N'memory.entries.get', N'memory.entries.search',
                   N'memory.entries.recent', N'memory.threads.get')
ORDER BY pub_name;
