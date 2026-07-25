-- ============================================================================
-- elideus-group v0.13.8.0 — Memory Unification: Part A foundation
-- Date: 2026-07-24
-- Implements: FDD-ORACLE-MEM-UNIFY-01 Part A (§3, A1-A10)
--
-- Purpose:
--   Make the memory graph's constraints mechanical and fail-closed: one entry
--   kind enum, a body size cap, a single state field, an accrual ledger,
--   deterministic canonical names, structural edge kinds, a verbatim document
--   store, and a maintenance queue.
--
-- Tables created (4):
--   agent_memory_aliases            — canonical-name near-miss resolution (A5)
--   agent_memory_documents          — verbatim source text, content-addressed (A6)
--   agent_memory_entry_documents    — entry <-> document join (A6, revised)
--   agent_memory_maintenance_queue  — touch-driven operations ledger (A8)
--
-- Columns added to agent_memory_entries (5):
--   pub_accrual, priv_last_ref_on, pub_canonical_name,
--   priv_body_archive, priv_archived_on
-- Column added to agent_memory_references (1):
--   pub_is_structural (computed)
--
-- ---------------------------------------------------------------------------
-- FOUR CORRECTIONS to the FDD as drafted. Each is a live-breakage fix, not a
-- preference; all four were found by measuring the current database, and all
-- four are recorded on memory entry C3278CD3.
--
--  1. A6 CARDINALITY.  The FDD declares agent_memory_documents with
--     PRIMARY KEY (ref_entry_guid) — strictly one document per entry. The real
--     relation is many-to-many in BOTH directions:
--       * ComponentBuilderArchSpec_v0.2.md backs 3 entries; IoServiceGateway.md
--         backs 3; TemplateCMSEngine.md backs 2; DesignComponentBuilderModules.md
--         backs 2; README.md and docs/MEMORY_BANK.md back 2 each.
--       * ~10 entries cite 2+ documents (4B634AAC and AD59F0E9 cite 3 each);
--         PK(ref_entry_guid) cannot express these at all.
--     RESOLUTION (approved): documents are content-addressed — one row per
--     distinct sha256, bytes stored once — and agent_memory_entry_documents
--     carries the relation, with pub_section for the section-level citations
--     that several rules make (PATTERNS.md §2/§3/§4/§5.4/§0/§6).
--
--  2. A1 KIND ENUM omits 'reference', which is in active use (8 entries in
--     project elideus-group alone: AF2D23C5, 7DD2AD4C, 13723699, 42C90192,
--     FB7CC542, 33AA55B6, E7A0831F, ...) and is listed as a valid kind in the
--     memory-bank contract. WITH NOCHECK grandfathers the existing rows, but
--     the constraint IS enforced on UPDATE — so without this fix all 8 entries
--     become permanently un-updatable and memory_store(kind='reference')
--     starts failing. 'reference' is included below.
--
--  3. A3 NODE_STATE ENUM omits 'retired', 'historical' and 'conflict'. All
--     three are written by registered queries shipped in
--     v0.13.3.0_memory_consult_loop.sql (the conflict open/resolve path).
--     Applying the FDD's enum verbatim would break memory_conflict_resolve
--     immediately on deploy — inside the very window §7 claims is safe. The
--     enum below is the union of the FDD's new values and the in-use values.
--
--  4. A7 REF_KIND ENUM omits 'contradicts', which is written by the same
--     v0.13.3.0 queries and is part of the documented link vocabulary.
--     Included below.
--
--  Also: A6 specifies char(64) for the sha256 and char(40) for the commit.
--  system_objects_types registers no fixed-length char EDT (12 types; nearest
--  is STRING/nvarchar), so those are NVARCHAR(64)/NVARCHAR(40) here — the same
--  reasoning v0.13.0.0 applied when it chose DATETIMEOFFSET over DATETIME2,
--  and for the same reason: keep oracle_describe_table accurate.
-- ---------------------------------------------------------------------------
--
-- Safety: additive or WITH NOCHECK throughout. No pub_body is read or written.
--   PHASE 3 drops and re-adds agent_memory_entries.pub_is_active as a computed
--   column. Verified safe before writing this script:
--     * no code path writes entries.pub_is_active (all state transitions
--       already go through pub_node_state) — a PERSISTED computed column
--       would reject such a write;
--     * no SELECT * against agent_memory_* exists, so the resulting column
--       reorder (pub_is_active 9 -> 20) has no positional consumer.
--
-- UUID5 namespace (reflection rows): DECAFBAD-CAFE-FADE-BABE-C0FFEE420B67
--   table:<name> / column:<table>.<column> / index:<table>.<index>
-- This migration is additive and idempotent (safe to re-run).
-- ============================================================================

SET ANSI_NULLS ON;
SET QUOTED_IDENTIFIER ON;
GO


-- ============================================================================
-- PHASE 1: New columns (A4, A5, A9 on entries; A7 on references)
-- ============================================================================

IF COL_LENGTH(N'[dbo].[agent_memory_entries]', N'pub_accrual') IS NULL
  ALTER TABLE [dbo].[agent_memory_entries]
    ADD [pub_accrual] INT NOT NULL CONSTRAINT [DF_ame_accrual] DEFAULT (0);
GO

IF COL_LENGTH(N'[dbo].[agent_memory_entries]', N'priv_last_ref_on') IS NULL
  ALTER TABLE [dbo].[agent_memory_entries] ADD [priv_last_ref_on] DATETIMEOFFSET(7) NULL;
GO

IF COL_LENGTH(N'[dbo].[agent_memory_entries]', N'pub_canonical_name') IS NULL
  ALTER TABLE [dbo].[agent_memory_entries] ADD [pub_canonical_name] NVARCHAR(256) NULL;
GO

IF COL_LENGTH(N'[dbo].[agent_memory_entries]', N'priv_body_archive') IS NULL
  ALTER TABLE [dbo].[agent_memory_entries] ADD [priv_body_archive] NVARCHAR(MAX) NULL;
GO

IF COL_LENGTH(N'[dbo].[agent_memory_entries]', N'priv_archived_on') IS NULL
  ALTER TABLE [dbo].[agent_memory_entries] ADD [priv_archived_on] DATETIMEOFFSET(7) NULL;
GO

-- A7: structural-vs-semantic is derived, never hand-set.
IF COL_LENGTH(N'[dbo].[agent_memory_references]', N'pub_is_structural') IS NULL
  ALTER TABLE [dbo].[agent_memory_references]
    ADD [pub_is_structural] AS
        CAST(CASE WHEN [pub_ref_kind] IN (N'contains', N'next') THEN 1 ELSE 0 END AS BIT) PERSISTED;
GO


-- ============================================================================
-- PHASE 2: Enum + size constraints (A1, A2, A7)
--   WITH NOCHECK grandfathers existing rows. For A2 that is deliberate:
--   oversized legacy bodies survive but cannot be UPDATEd until decomposed.
-- ============================================================================

IF NOT EXISTS (SELECT 1 FROM sys.check_constraints WHERE name = N'CK_agent_memory_entries_kind')
  ALTER TABLE [dbo].[agent_memory_entries] WITH NOCHECK
    ADD CONSTRAINT [CK_agent_memory_entries_kind] CHECK ([pub_kind] IN (
        N'rule', N'decision', N'invariant', N'spec', N'note',
        N'session_summary', N'snippet', N'reference',      -- 'reference': correction 2
        N'incident', N'concept', N'conflict'));            -- new in A1
GO

IF NOT EXISTS (SELECT 1 FROM sys.check_constraints WHERE name = N'CK_agent_memory_entries_body_len')
  ALTER TABLE [dbo].[agent_memory_entries] WITH NOCHECK
    ADD CONSTRAINT [CK_agent_memory_entries_body_len] CHECK (LEN([pub_body]) <= 15000);
GO

IF NOT EXISTS (SELECT 1 FROM sys.check_constraints WHERE name = N'CK_agent_memory_entries_node_state')
  ALTER TABLE [dbo].[agent_memory_entries] WITH NOCHECK
    ADD CONSTRAINT [CK_agent_memory_entries_node_state] CHECK ([pub_node_state] IN (
        N'active', N'legacy', N'superseded', N'archived', N'draft',   -- A3 as drafted
        N'retired', N'historical', N'conflict'));                     -- correction 3
GO

IF NOT EXISTS (SELECT 1 FROM sys.check_constraints WHERE name = N'CK_agent_memory_references_ref_kind')
  ALTER TABLE [dbo].[agent_memory_references] WITH NOCHECK
    ADD CONSTRAINT [CK_agent_memory_references_ref_kind] CHECK ([pub_ref_kind] IN (
        N'cites', N'supports', N'supersedes', N'derived_from', N'disambiguates',
        N'contradicts',                                    -- correction 4
        N'violates', N'contains', N'next'));               -- new in A7
GO

-- A6: composite-FK target, so a document link cannot drift from the entry's kind.
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'UQ_agent_memory_entries_guid_kind'
               AND object_id = OBJECT_ID(N'[dbo].[agent_memory_entries]'))
  ALTER TABLE [dbo].[agent_memory_entries]
    ADD CONSTRAINT [UQ_agent_memory_entries_guid_kind] UNIQUE ([key_guid], [pub_kind]);
GO

-- A5: canonical names are unique per project where present.
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'UX_agent_memory_entries_canonical'
               AND object_id = OBJECT_ID(N'[dbo].[agent_memory_entries]'))
  CREATE UNIQUE INDEX [UX_agent_memory_entries_canonical]
      ON [dbo].[agent_memory_entries] ([pub_project], [pub_canonical_name])
   WHERE [pub_canonical_name] IS NOT NULL;
GO

-- A7: the traversal index. Semantic edges only, by default, at every depth.
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'IX_amr_from_semantic'
               AND object_id = OBJECT_ID(N'[dbo].[agent_memory_references]'))
  CREATE INDEX [IX_amr_from_semantic]
      ON [dbo].[agent_memory_references] ([ref_from_guid], [pub_is_structural], [pub_is_active])
   INCLUDE ([ref_to_guid], [pub_ref_kind], [pub_weight]);
GO


-- ============================================================================
-- PHASE 3: Collapse the two state fields (A3)
--   pub_node_state becomes canonical; pub_is_active becomes a persisted
--   computed projection of it, so every existing read keeps working.
--   IX_agent_memory_entries_project must be dropped and rebuilt around it.
-- ============================================================================

IF EXISTS (SELECT 1 FROM sys.columns
           WHERE object_id = OBJECT_ID(N'[dbo].[agent_memory_entries]')
             AND name = N'pub_is_active' AND is_computed = 0)
BEGIN
    IF EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'IX_agent_memory_entries_project'
               AND object_id = OBJECT_ID(N'[dbo].[agent_memory_entries]'))
      DROP INDEX [IX_agent_memory_entries_project] ON [dbo].[agent_memory_entries];

    ALTER TABLE [dbo].[agent_memory_entries] DROP CONSTRAINT [DF_ame_is_active];
    ALTER TABLE [dbo].[agent_memory_entries] DROP COLUMN [pub_is_active];

    ALTER TABLE [dbo].[agent_memory_entries]
      ADD [pub_is_active] AS
          CAST(CASE WHEN [pub_node_state] = N'active' THEN 1 ELSE 0 END AS BIT) PERSISTED;
END
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'IX_agent_memory_entries_project'
               AND object_id = OBJECT_ID(N'[dbo].[agent_memory_entries]'))
  CREATE INDEX [IX_agent_memory_entries_project]
      ON [dbo].[agent_memory_entries] ([pub_project], [pub_is_active]);
GO


-- ============================================================================
-- PHASE 4: New tables (A5, A6 revised, A8)
-- ============================================================================

-- A5 — alias table: what makes canonicalisation tractable. The sleep cycle
-- records the names it has collapsed onto a node, so the next write of a
-- near-miss name resolves to the existing node instead of creating a sibling.
IF OBJECT_ID(N'[dbo].[agent_memory_aliases]', N'U') IS NULL
BEGIN
  CREATE TABLE [dbo].[agent_memory_aliases] (
    [key_guid]        UNIQUEIDENTIFIER  NOT NULL  CONSTRAINT [DF_ama_key_guid]   DEFAULT NEWID(),
    [ref_entry_guid]  UNIQUEIDENTIFIER  NOT NULL,
    [pub_project]     NVARCHAR(128)     NOT NULL,
    [pub_alias]       NVARCHAR(256)     NOT NULL,
    [pub_source]      NVARCHAR(32)      NOT NULL  CONSTRAINT [DF_ama_source]     DEFAULT (N'sleep'),
    [pub_is_active]   BIT               NOT NULL  CONSTRAINT [DF_ama_is_active]  DEFAULT 1,
    [priv_created_on] DATETIMEOFFSET(7) NOT NULL  CONSTRAINT [DF_ama_created_on] DEFAULT SYSUTCDATETIME(),
    CONSTRAINT [PK_agent_memory_aliases] PRIMARY KEY CLUSTERED ([key_guid]),
    CONSTRAINT [FK_agent_memory_aliases_entry] FOREIGN KEY ([ref_entry_guid])
      REFERENCES [dbo].[agent_memory_entries] ([key_guid])
  );
END
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'UX_agent_memory_aliases_alias'
               AND object_id = OBJECT_ID(N'[dbo].[agent_memory_aliases]'))
  CREATE UNIQUE INDEX [UX_agent_memory_aliases_alias]
      ON [dbo].[agent_memory_aliases] ([pub_project], [pub_alias]) WHERE [pub_is_active] = 1;
GO

-- A6 (revised) — the durable artifact, CONTENT-ADDRESSED.
--   key_guid is UUID5(namespace, 'document:' + sha256) so identical bytes
--   always resolve to the same row: the 4 source files that back multiple
--   entries are stored exactly once.
--   pub_fidelity is the honesty column:
--     verbatim      — recovered from git, hash matches the blob at pub_source_commit
--     reconstructed — assembled from prose because the source was unrecoverable
--     unrecovered   — source known, bytes not yet obtained (a work queue)
--   IMMUTABILITY: pub_document is write-once per recovery. No sleep-cycle
--   operation, stripper, decomposition pass or agent update may modify it;
--   corrections insert a new row with a new pub_source_commit. Enforce with a
--   DB principal holding SELECT-only on this table (FDD §D3).
IF OBJECT_ID(N'[dbo].[agent_memory_documents]', N'U') IS NULL
BEGIN
  CREATE TABLE [dbo].[agent_memory_documents] (
    [key_guid]           UNIQUEIDENTIFIER  NOT NULL,   -- UUID5('document:' + sha256)
    [pub_content_sha256] NVARCHAR(64)      NOT NULL,   -- the content address
    [pub_document]       NVARCHAR(MAX)     NOT NULL,   -- verbatim bytes, never rewritten
    [pub_byte_length]    INT               NOT NULL,
    [pub_format]         NVARCHAR(16)      NOT NULL  CONSTRAINT [DF_amd_format]      DEFAULT (N'markdown'),
    [pub_source_path]    NVARCHAR(512)     NULL,       -- original repo path
    [pub_source_repo]    NVARCHAR(256)     NULL,
    [pub_source_commit]  NVARCHAR(40)      NULL,       -- commit the bytes came from
    [pub_source_branch]  NVARCHAR(128)     NULL,
    [pub_fidelity]       NVARCHAR(16)      NOT NULL  CONSTRAINT [DF_amd_fidelity]    DEFAULT (N'verbatim'),
    [priv_created_on]    DATETIMEOFFSET(7) NOT NULL  CONSTRAINT [DF_amd_created_on]  DEFAULT SYSUTCDATETIME(),
    [priv_modified_on]   DATETIMEOFFSET(7) NOT NULL  CONSTRAINT [DF_amd_modified_on] DEFAULT SYSUTCDATETIME(),
    CONSTRAINT [PK_agent_memory_documents] PRIMARY KEY CLUSTERED ([key_guid]),
    CONSTRAINT [CK_amd_fidelity] CHECK ([pub_fidelity] IN (N'verbatim', N'reconstructed', N'unrecovered')),
    CONSTRAINT [CK_amd_byte_length] CHECK ([pub_byte_length] >= 0)
  );
END
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'UX_amd_sha256'
               AND object_id = OBJECT_ID(N'[dbo].[agent_memory_documents]'))
  CREATE UNIQUE INDEX [UX_amd_sha256] ON [dbo].[agent_memory_documents] ([pub_content_sha256]);
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'IX_amd_source_path'
               AND object_id = OBJECT_ID(N'[dbo].[agent_memory_documents]'))
  CREATE INDEX [IX_amd_source_path] ON [dbo].[agent_memory_documents] ([pub_source_path]);
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'IX_amd_fidelity'
               AND object_id = OBJECT_ID(N'[dbo].[agent_memory_documents]'))
  CREATE INDEX [IX_amd_fidelity] ON [dbo].[agent_memory_documents] ([pub_fidelity]);
GO

-- A6 (revised) — the entry <-> document relation.
--   The composite FK (ref_entry_guid, pub_entry_kind) -> entries(key_guid, pub_kind)
--   guarantees declaratively that the denormalised kind can never drift from the
--   entry's actual kind. No trigger, no application-layer invariant.
--   pub_section carries the section-level citations (e.g. N'§5.4').
--   pub_role distinguishes the entry's primary source from supporting ones.
--   SCOPE (resolves FDD open decision §9.6): the kind list is permissive rather
--   than 'spec'-only, because the measured data has 8 rules and several
--   references citing source documents (PATTERNS.md, the AGENTS.md set).
--   Bounded traversal is unaffected — documents are never returned unless
--   memory_get is called with include_document=true. To narrow this back to
--   specs only, this CHECK is the single line to change.
IF OBJECT_ID(N'[dbo].[agent_memory_entry_documents]', N'U') IS NULL
BEGIN
  CREATE TABLE [dbo].[agent_memory_entry_documents] (
    [key_guid]          UNIQUEIDENTIFIER  NOT NULL  CONSTRAINT [DF_amed_key_guid]   DEFAULT NEWID(),
    [ref_entry_guid]    UNIQUEIDENTIFIER  NOT NULL,
    [pub_entry_kind]    NVARCHAR(32)      NOT NULL,
    [ref_document_guid] UNIQUEIDENTIFIER  NOT NULL,
    [pub_role]          NVARCHAR(24)      NOT NULL  CONSTRAINT [DF_amed_role]       DEFAULT (N'primary'),
    [pub_section]       NVARCHAR(128)     NULL,
    [pub_is_active]     BIT               NOT NULL  CONSTRAINT [DF_amed_is_active]  DEFAULT 1,
    [priv_created_on]   DATETIMEOFFSET(7) NOT NULL  CONSTRAINT [DF_amed_created_on] DEFAULT SYSUTCDATETIME(),
    CONSTRAINT [PK_agent_memory_entry_documents] PRIMARY KEY CLUSTERED ([key_guid]),
    CONSTRAINT [CK_amed_role] CHECK ([pub_role] IN (N'primary', N'supporting')),
    CONSTRAINT [CK_amed_kind] CHECK ([pub_entry_kind] IN (
        N'spec', N'rule', N'reference', N'decision', N'note', N'invariant',
        N'session_summary', N'snippet', N'incident', N'concept', N'conflict')),
    CONSTRAINT [FK_amed_entry] FOREIGN KEY ([ref_entry_guid], [pub_entry_kind])
      REFERENCES [dbo].[agent_memory_entries] ([key_guid], [pub_kind]),
    CONSTRAINT [FK_amed_document] FOREIGN KEY ([ref_document_guid])
      REFERENCES [dbo].[agent_memory_documents] ([key_guid])
  );
END
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'UX_amed_link'
               AND object_id = OBJECT_ID(N'[dbo].[agent_memory_entry_documents]'))
  CREATE UNIQUE INDEX [UX_amed_link]
      ON [dbo].[agent_memory_entry_documents] ([ref_entry_guid], [ref_document_guid], [pub_section])
   WHERE [pub_is_active] = 1;
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'IX_amed_document'
               AND object_id = OBJECT_ID(N'[dbo].[agent_memory_entry_documents]'))
  CREATE INDEX [IX_amed_document] ON [dbo].[agent_memory_entry_documents] ([ref_document_guid], [pub_is_active]);
GO

-- A8 — operations ledger (NOT a memory store; a distinct noun, hence a table).
--   There is no batch runner: rows are written when a node is touched and a
--   deferred operation is identified, and drained by an agent reviewing the
--   queue. The filtered unique index is load-bearing — without a scheduler the
--   same node may be touched many times a day, and every touch would otherwise
--   enqueue a duplicate proposal.
IF OBJECT_ID(N'[dbo].[agent_memory_maintenance_queue]', N'U') IS NULL
BEGIN
  CREATE TABLE [dbo].[agent_memory_maintenance_queue] (
    [key_guid]         UNIQUEIDENTIFIER  NOT NULL  CONSTRAINT [DF_ammq_key_guid]    DEFAULT NEWID(),
    [pub_op]           NVARCHAR(48)      NOT NULL,
    [pub_state]        NVARCHAR(16)      NOT NULL  CONSTRAINT [DF_ammq_state]       DEFAULT (N'pending'),
    [ref_subject_guid] UNIQUEIDENTIFIER  NULL,
    [ref_object_guid]  UNIQUEIDENTIFIER  NULL,
    [pub_trigger]      NVARCHAR(32)      NOT NULL,
    [pub_rationale]    NVARCHAR(2000)    NULL,
    [pub_payload]      NVARCHAR(MAX)     NULL,
    [priv_created_on]  DATETIMEOFFSET(7) NOT NULL  CONSTRAINT [DF_ammq_created_on]  DEFAULT SYSUTCDATETIME(),
    [priv_decided_on]  DATETIMEOFFSET(7) NULL,
    CONSTRAINT [PK_agent_memory_maintenance_queue] PRIMARY KEY CLUSTERED ([key_guid]),
    CONSTRAINT [CK_ammq_state]   CHECK ([pub_state] IN (N'pending', N'applied', N'rejected', N'expired')),
    CONSTRAINT [CK_ammq_op]      CHECK ([pub_op] IN (
        N'decompose', N'dedup', N'abstract', N'merge', N'strip', N'orphan', N'missing_document')),
    CONSTRAINT [CK_ammq_trigger] CHECK ([pub_trigger] IN (N'read', N'write', N'link', N'validate'))
  );
END
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'UX_ammq_open'
               AND object_id = OBJECT_ID(N'[dbo].[agent_memory_maintenance_queue]'))
  CREATE UNIQUE INDEX [UX_ammq_open]
      ON [dbo].[agent_memory_maintenance_queue] ([pub_op], [ref_subject_guid], [ref_object_guid])
   WHERE [pub_state] = N'pending';
GO


-- ============================================================================
-- PHASE 5: Reflection registration (so the oracle_* tools see the new schema)
--   Re-runnable: child rows deleted (FK-safe order) then re-inserted.
--   agent_memory_entries is re-registered in full because PHASE 3 moved
--   pub_is_active from ordinal 9 to ordinal 20.
-- ============================================================================

DECLARE @T_UUID UNIQUEIDENTIFIER = N'4D2EB10B-363E-5AF4-826A-9294146244E4'; -- uniqueidentifier
DECLARE @T_STR  UNIQUEIDENTIFIER = N'0093B404-1EEE-563D-9135-4B9E7EECA7A2'; -- nvarchar
DECLARE @T_TEXT UNIQUEIDENTIFIER = N'DCA18974-D648-5DFF-AEFB-122C081145AA'; -- nvarchar(max)
DECLARE @T_BOOL UNIQUEIDENTIFIER = N'12B2F03B-E315-50A5-B631-E6B1EB961A17'; -- bit
DECLARE @T_DTZ  UNIQUEIDENTIFIER = N'70F890D3-5AB5-5250-860E-4F7F9624190C'; -- datetimeoffset(7)
DECLARE @T_INT  UNIQUEIDENTIFIER = N'E3EDE0CE-2A03-501E-A796-3487BEA03B7B'; -- int
DECLARE @T_DEC  UNIQUEIDENTIFIER = N'A79190A1-FB3B-580C-8A24-445D590715BD'; -- decimal(19,5)

DECLARE @TBL_ENTRIES   UNIQUEIDENTIFIER = N'07B0D4B9-4D3B-569E-926D-551035A6357B';
DECLARE @TBL_REFS      UNIQUEIDENTIFIER = N'0D52ACB1-CE0F-5878-908E-314AD41A0A12';
DECLARE @TBL_ALIASES   UNIQUEIDENTIFIER = N'573687D1-9AA4-554F-AC8A-4D860DA47D1D';
DECLARE @TBL_DOCUMENTS UNIQUEIDENTIFIER = N'967654FF-FEA1-5FEB-BD8C-B37EF64D08E8';
DECLARE @TBL_ENTRY_DOCUMENTS UNIQUEIDENTIFIER = N'3C436176-90FD-5D01-A0F3-D1CA01E4C1E8';
DECLARE @TBL_MAINTENANCE_QUEUE UNIQUEIDENTIFIER = N'3227BE00-5890-5D53-A40B-52CCB284A548';

-- Idempotent cleanup (FK-safe order: constraints -> indexes -> columns -> tables)
DELETE FROM [dbo].[system_objects_database_constraints]
 WHERE [ref_table_guid] IN (@TBL_ALIASES, @TBL_DOCUMENTS, @TBL_ENTRY_DOCUMENTS, @TBL_MAINTENANCE_QUEUE);
DELETE FROM [dbo].[system_objects_database_indexes]
 WHERE [ref_table_guid] IN (@TBL_ALIASES, @TBL_DOCUMENTS, @TBL_ENTRY_DOCUMENTS, @TBL_MAINTENANCE_QUEUE);
-- NOTE: agent_memory_entries columns are NOT deleted wholesale. Three rows in
-- system_objects_database_constraints point at them via FK_sodcon_column /
-- FK_sodcon_ref_column (ON DELETE NO_ACTION):
--   constraint:agent_memory_entries.ref_thread_guid    -> entries.ref_thread_guid
--   constraint:agent_memory_references.ref_from_guid   -> entries.key_guid
--   constraint:agent_memory_references.ref_to_guid     -> entries.key_guid
-- A blanket DELETE would raise a foreign-key violation. The entries table is
-- therefore patched in place below (5b-i / 5b-ii) rather than re-registered.
DELETE FROM [dbo].[system_objects_database_columns]
 WHERE [ref_table_guid] IN (@TBL_ALIASES, @TBL_DOCUMENTS, @TBL_ENTRY_DOCUMENTS, @TBL_MAINTENANCE_QUEUE)
    OR ([ref_table_guid] = @TBL_REFS     AND [pub_name] = N'pub_is_structural')
    OR ([ref_table_guid] = @TBL_ENTRIES  AND [pub_name] IN (
          N'pub_accrual', N'priv_last_ref_on', N'pub_canonical_name',
          N'priv_body_archive', N'priv_archived_on'));
DELETE FROM [dbo].[system_objects_database_tables]
 WHERE [key_guid] IN (@TBL_ALIASES, @TBL_DOCUMENTS, @TBL_ENTRY_DOCUMENTS, @TBL_MAINTENANCE_QUEUE);

-- 5a: tables
INSERT INTO [dbo].[system_objects_database_tables] ([key_guid], [pub_name], [pub_schema]) VALUES
(@TBL_ALIASES,           N'agent_memory_aliases',           N'dbo'),
(@TBL_DOCUMENTS,         N'agent_memory_documents',         N'dbo'),
(@TBL_ENTRY_DOCUMENTS,   N'agent_memory_entry_documents',   N'dbo'),
(@TBL_MAINTENANCE_QUEUE, N'agent_memory_maintenance_queue', N'dbo');

-- 5b: columns
-- 5b-i: agent_memory_entries — patch in place (see NOTE above).
--   PHASE 3 moved pub_is_active from ordinal 9 to 20; the columns that sat
--   below it each shift up by one.
UPDATE [dbo].[system_objects_database_columns] SET [pub_ordinal] = 9  WHERE [ref_table_guid] = @TBL_ENTRIES AND [pub_name] = N'priv_created_on';
UPDATE [dbo].[system_objects_database_columns] SET [pub_ordinal] = 10 WHERE [ref_table_guid] = @TBL_ENTRIES AND [pub_name] = N'priv_modified_on';
UPDATE [dbo].[system_objects_database_columns] SET [pub_ordinal] = 11 WHERE [ref_table_guid] = @TBL_ENTRIES AND [pub_name] = N'pub_confidence';
UPDATE [dbo].[system_objects_database_columns] SET [pub_ordinal] = 12 WHERE [ref_table_guid] = @TBL_ENTRIES AND [pub_name] = N'pub_confidence_source';
UPDATE [dbo].[system_objects_database_columns] SET [pub_ordinal] = 13 WHERE [ref_table_guid] = @TBL_ENTRIES AND [pub_name] = N'pub_node_state';
UPDATE [dbo].[system_objects_database_columns] SET [pub_ordinal] = 14 WHERE [ref_table_guid] = @TBL_ENTRIES AND [pub_name] = N'pub_ref_count';
UPDATE [dbo].[system_objects_database_columns]
   SET [pub_ordinal] = 20, [pub_default] = N'COMPUTED: pub_node_state = active'
 WHERE [ref_table_guid] = @TBL_ENTRIES AND [pub_name] = N'pub_is_active';

-- 5b-ii: agent_memory_entries — the five new columns (ordinals 15-19)
INSERT INTO [dbo].[system_objects_database_columns] ([key_guid],[ref_table_guid],[ref_type_guid],[pub_name],[pub_ordinal],[pub_is_nullable],[pub_is_primary_key],[pub_is_identity],[pub_default],[pub_max_length]) VALUES
(N'1D0B9266-36FD-58BD-8AAD-0A8C19443410',@TBL_ENTRIES,@T_INT, N'pub_accrual',       15,0,0,0,N'0', NULL),
(N'F2A0FFA1-9360-53B1-A7D5-F6DA5F9CD355',@TBL_ENTRIES,@T_DTZ, N'priv_last_ref_on',  16,1,0,0,NULL, NULL),
(N'B98DE492-D380-5948-8890-A67CB163D0AC',@TBL_ENTRIES,@T_STR, N'pub_canonical_name',17,1,0,0,NULL, 256),
(N'E3A43192-6788-50FF-83EE-144FB6747849',@TBL_ENTRIES,@T_TEXT,N'priv_body_archive', 18,1,0,0,NULL, NULL),
(N'9CD9BAB2-27D7-5D40-B0C6-1DC3DF3CECF5',@TBL_ENTRIES,@T_DTZ, N'priv_archived_on',  19,1,0,0,NULL, NULL);

-- agent_memory_aliases
INSERT INTO [dbo].[system_objects_database_columns] ([key_guid],[ref_table_guid],[ref_type_guid],[pub_name],[pub_ordinal],[pub_is_nullable],[pub_is_primary_key],[pub_is_identity],[pub_default],[pub_max_length]) VALUES
(N'4967850F-51F6-5465-AF19-182AA9C47728',@TBL_ALIASES,@T_UUID,N'key_guid',1,0,1,0,N'NEWID()',NULL),
(N'0BBCDB36-5190-5E16-9F3A-34972EC5FCB3',@TBL_ALIASES,@T_UUID,N'ref_entry_guid',2,0,0,0,NULL,NULL),
(N'226C91A6-180B-5113-9936-F3185CDEC0C9',@TBL_ALIASES,@T_STR,N'pub_project',3,0,0,0,NULL,128),
(N'64F36157-3FA2-5B0A-B0CE-379F354C8D3A',@TBL_ALIASES,@T_STR,N'pub_alias',4,0,0,0,NULL,256),
(N'170E8136-9B2E-575F-8C9F-2768638F9D49',@TBL_ALIASES,@T_STR,N'pub_source',5,0,0,0,N'sleep',32),
(N'37B58440-2E0B-5D9C-9D72-C92BAFC4E0A4',@TBL_ALIASES,@T_BOOL,N'pub_is_active',6,0,0,0,N'1',NULL),
(N'BF12F2D7-257B-51F6-8A6E-747165F42CA0',@TBL_ALIASES,@T_DTZ,N'priv_created_on',7,0,0,0,N'SYSUTCDATETIME()',NULL);

-- agent_memory_documents
INSERT INTO [dbo].[system_objects_database_columns] ([key_guid],[ref_table_guid],[ref_type_guid],[pub_name],[pub_ordinal],[pub_is_nullable],[pub_is_primary_key],[pub_is_identity],[pub_default],[pub_max_length]) VALUES
(N'4AED8A14-996A-57FB-9F01-AF089975B4A0',@TBL_DOCUMENTS,@T_UUID,N'key_guid',1,0,1,0,NULL,NULL),
(N'F0F4D601-E7E0-5B50-BB22-744E1F484831',@TBL_DOCUMENTS,@T_STR,N'pub_content_sha256',2,0,0,0,NULL,64),
(N'B696FC8A-890F-580C-80B1-C0A6FB830241',@TBL_DOCUMENTS,@T_TEXT,N'pub_document',3,0,0,0,NULL,NULL),
(N'7D8E96C1-83A0-5EE2-8B1C-218D56953F7B',@TBL_DOCUMENTS,@T_INT,N'pub_byte_length',4,0,0,0,NULL,NULL),
(N'4B9B585E-7FE2-53A4-B46F-31C90B9769BE',@TBL_DOCUMENTS,@T_STR,N'pub_format',5,0,0,0,N'markdown',16),
(N'A172C485-80A0-54E3-BD37-66F8C7E909A9',@TBL_DOCUMENTS,@T_STR,N'pub_source_path',6,1,0,0,NULL,512),
(N'74D1EB79-DC02-5578-A6E7-F3B098B75BDA',@TBL_DOCUMENTS,@T_STR,N'pub_source_repo',7,1,0,0,NULL,256),
(N'8DF20740-3F79-596A-B7F4-21692C947627',@TBL_DOCUMENTS,@T_STR,N'pub_source_commit',8,1,0,0,NULL,40),
(N'5F178A0C-C56F-592D-8AFB-DF9278DD6796',@TBL_DOCUMENTS,@T_STR,N'pub_source_branch',9,1,0,0,NULL,128),
(N'CC64BDD1-6F36-52CC-AFB2-2D1918DEC108',@TBL_DOCUMENTS,@T_STR,N'pub_fidelity',10,0,0,0,N'verbatim',16),
(N'CDD31ABF-518C-549C-8AB6-9FF358EC3C44',@TBL_DOCUMENTS,@T_DTZ,N'priv_created_on',11,0,0,0,N'SYSUTCDATETIME()',NULL),
(N'DE0DD2D0-23AE-563C-BE3A-58D9E6697B3E',@TBL_DOCUMENTS,@T_DTZ,N'priv_modified_on',12,0,0,0,N'SYSUTCDATETIME()',NULL);

-- agent_memory_entry_documents
INSERT INTO [dbo].[system_objects_database_columns] ([key_guid],[ref_table_guid],[ref_type_guid],[pub_name],[pub_ordinal],[pub_is_nullable],[pub_is_primary_key],[pub_is_identity],[pub_default],[pub_max_length]) VALUES
(N'1989D536-BD41-58B6-A87C-5EFC641CDCBE',@TBL_ENTRY_DOCUMENTS,@T_UUID,N'key_guid',1,0,1,0,N'NEWID()',NULL),
(N'41E79D24-169E-5FF6-A354-3BAD7E0F6E0F',@TBL_ENTRY_DOCUMENTS,@T_UUID,N'ref_entry_guid',2,0,0,0,NULL,NULL),
(N'BA45A7D9-2120-58A8-8FBB-36E1E06E6231',@TBL_ENTRY_DOCUMENTS,@T_STR,N'pub_entry_kind',3,0,0,0,NULL,32),
(N'FFF39CD1-6F19-589E-A876-D348069EDA30',@TBL_ENTRY_DOCUMENTS,@T_UUID,N'ref_document_guid',4,0,0,0,NULL,NULL),
(N'E81E58A1-A6D0-5BFD-9F29-137B1EC9B653',@TBL_ENTRY_DOCUMENTS,@T_STR,N'pub_role',5,0,0,0,N'primary',24),
(N'13CF637A-0950-5956-A4D5-9420C731F0B3',@TBL_ENTRY_DOCUMENTS,@T_STR,N'pub_section',6,1,0,0,NULL,128),
(N'97054B72-7AD6-5DD1-A096-7CD590129397',@TBL_ENTRY_DOCUMENTS,@T_BOOL,N'pub_is_active',7,0,0,0,N'1',NULL),
(N'0CCFCEAA-2A57-55EB-8FCD-D639B0108620',@TBL_ENTRY_DOCUMENTS,@T_DTZ,N'priv_created_on',8,0,0,0,N'SYSUTCDATETIME()',NULL);

-- agent_memory_maintenance_queue
INSERT INTO [dbo].[system_objects_database_columns] ([key_guid],[ref_table_guid],[ref_type_guid],[pub_name],[pub_ordinal],[pub_is_nullable],[pub_is_primary_key],[pub_is_identity],[pub_default],[pub_max_length]) VALUES
(N'35B7E9A8-E716-5FA5-A9E1-5011787D0933',@TBL_MAINTENANCE_QUEUE,@T_UUID,N'key_guid',1,0,1,0,N'NEWID()',NULL),
(N'05CEB40E-A7BB-58BA-A6AD-59EAEDC187B4',@TBL_MAINTENANCE_QUEUE,@T_STR,N'pub_op',2,0,0,0,NULL,48),
(N'0EFBEB5D-9D07-52ED-93CC-61C560A670AB',@TBL_MAINTENANCE_QUEUE,@T_STR,N'pub_state',3,0,0,0,N'pending',16),
(N'8125F72C-8074-5C9F-84E1-765D6E54003B',@TBL_MAINTENANCE_QUEUE,@T_UUID,N'ref_subject_guid',4,1,0,0,NULL,NULL),
(N'3948EFF9-33A6-5C92-9041-321EF6F89FEC',@TBL_MAINTENANCE_QUEUE,@T_UUID,N'ref_object_guid',5,1,0,0,NULL,NULL),
(N'B8D6471D-ED62-5655-93EB-1D295DC5D38F',@TBL_MAINTENANCE_QUEUE,@T_STR,N'pub_trigger',6,0,0,0,NULL,32),
(N'E9C1A6FC-A946-5075-AA56-3A1A5EE10E32',@TBL_MAINTENANCE_QUEUE,@T_STR,N'pub_rationale',7,1,0,0,NULL,2000),
(N'FFC5AE0C-800A-5E97-95A8-9C209BA9E1AC',@TBL_MAINTENANCE_QUEUE,@T_TEXT,N'pub_payload',8,1,0,0,NULL,NULL),
(N'163D2A70-EBC9-5B8A-9909-DA32CF3B866D',@TBL_MAINTENANCE_QUEUE,@T_DTZ,N'priv_created_on',9,0,0,0,N'SYSUTCDATETIME()',NULL),
(N'04886172-4842-5AAA-8DAA-D137848C6D18',@TBL_MAINTENANCE_QUEUE,@T_DTZ,N'priv_decided_on',10,1,0,0,NULL,NULL);

-- agent_memory_references: new computed column only (ordinal 9)
INSERT INTO [dbo].[system_objects_database_columns] ([key_guid],[ref_table_guid],[ref_type_guid],[pub_name],[pub_ordinal],[pub_is_nullable],[pub_is_primary_key],[pub_is_identity],[pub_default],[pub_max_length]) VALUES
(N'6C001A40-514E-5A4A-8AC5-D4D928EE0F2A',@TBL_REFS,@T_BOOL,N'pub_is_structural',9,0,0,0,N'COMPUTED: ref_kind IN (contains,next)',NULL);

-- 5c: indexes
INSERT INTO [dbo].[system_objects_database_indexes] ([key_guid],[ref_table_guid],[pub_name],[pub_columns],[pub_is_unique]) VALUES
(N'7F768D2D-3DD7-5C3B-8632-95F63F2274BA',   @TBL_ALIASES,         N'UX_agent_memory_aliases_alias', N'pub_project,pub_alias',                          1),
(N'B111E85C-BDFA-5711-B2B5-CD34FFD70972',     @TBL_DOCUMENTS,       N'UX_amd_sha256',                 N'pub_content_sha256',                             1),
(N'722FF367-E786-58C7-99E8-32BB60D80953',    @TBL_DOCUMENTS,       N'IX_amd_source_path',            N'pub_source_path',                                0),
(N'695F965F-3761-501F-8E23-D99C6FB7F36C',     @TBL_DOCUMENTS,       N'IX_amd_fidelity',               N'pub_fidelity',                                   0),
(N'6E3AD493-98B3-5619-A583-67063A05684F',    @TBL_ENTRY_DOCUMENTS, N'UX_amed_link',                  N'ref_entry_guid,ref_document_guid,pub_section',    1),
(N'E7FF5D63-8DD6-59CF-A44D-40DDE53FB104',    @TBL_ENTRY_DOCUMENTS, N'IX_amed_document',              N'ref_document_guid,pub_is_active',                 0),
(N'1A817A18-6CA2-5494-9AB0-BBF17A88C465',   @TBL_MAINTENANCE_QUEUE, N'UX_ammq_open',                N'pub_op,ref_subject_guid,ref_object_guid',         1);

-- 5d: foreign keys
INSERT INTO [dbo].[system_objects_database_constraints] ([key_guid],[ref_table_guid],[ref_column_guid],[ref_referenced_table_guid],[ref_referenced_column_guid]) VALUES
(N'0E04608C-A15C-57C2-A142-E135D76944CB', @TBL_ALIASES,         N'0BBCDB36-5190-5E16-9F3A-34972EC5FCB3', @TBL_ENTRIES,   N'13814960-BD02-5C7A-8FF7-2F49762C33B0'),
(N'0EBFCCE4-CB5C-5EF1-BAC2-E8AEA53D19D0',@TBL_ENTRY_DOCUMENTS, N'41E79D24-169E-5FF6-A354-3BAD7E0F6E0F',  @TBL_ENTRIES,   N'13814960-BD02-5C7A-8FF7-2F49762C33B0'),
(N'F4E97721-9F75-5F79-ACAE-F4933DC1BCD3',@TBL_ENTRY_DOCUMENTS, N'FFF39CD1-6F19-589E-A876-D348069EDA30',    @TBL_DOCUMENTS, N'4AED8A14-996A-57FB-9F01-AF089975B4A0');
GO


-- ============================================================================
-- PHASE 6: Verification  (all rows below must return the expected values)
-- ============================================================================

-- 6a: the four new tables exist and are empty
SELECT N'agent_memory_aliases'           AS [table], COUNT(*) AS [rows] FROM [dbo].[agent_memory_aliases]
UNION ALL SELECT N'agent_memory_documents',          COUNT(*) FROM [dbo].[agent_memory_documents]
UNION ALL SELECT N'agent_memory_entry_documents',    COUNT(*) FROM [dbo].[agent_memory_entry_documents]
UNION ALL SELECT N'agent_memory_maintenance_queue',  COUNT(*) FROM [dbo].[agent_memory_maintenance_queue];

-- 6b: pub_is_active is now computed+persisted and agrees with pub_node_state on every row
-- is_persisted lives on sys.computed_columns, not sys.columns.
SELECT N'is_active_computed' AS [check],
       CASE WHEN EXISTS (SELECT 1 FROM sys.computed_columns
                          WHERE object_id = OBJECT_ID(N'[dbo].[agent_memory_entries]')
                            AND name = N'pub_is_active' AND is_persisted = 1)
            THEN N'PASS' ELSE N'FAIL' END AS [result]
UNION ALL
SELECT N'is_structural_computed',
       CASE WHEN EXISTS (SELECT 1 FROM sys.computed_columns
                          WHERE object_id = OBJECT_ID(N'[dbo].[agent_memory_references]')
                            AND name = N'pub_is_structural' AND is_persisted = 1)
            THEN N'PASS' ELSE N'FAIL' END;

SELECT N'is_active_agrees_with_node_state' AS [check], COUNT(*) AS [mismatches]   -- expect 0
  FROM [dbo].[agent_memory_entries]
 WHERE [pub_is_active] <> CASE WHEN [pub_node_state] = N'active' THEN 1 ELSE 0 END;

-- 6c: NO existing row violates the new enums (proves the corrections were needed
--     and are sufficient — each of these must be 0, not merely grandfathered)
SELECT N'kind_outside_enum' AS [check], COUNT(*) AS [violations] FROM [dbo].[agent_memory_entries]
 WHERE [pub_kind] NOT IN (N'rule',N'decision',N'invariant',N'spec',N'note',N'session_summary',
                          N'snippet',N'reference',N'incident',N'concept',N'conflict');

SELECT N'node_state_outside_enum' AS [check], COUNT(*) AS [violations] FROM [dbo].[agent_memory_entries]
 WHERE [pub_node_state] NOT IN (N'active',N'legacy',N'superseded',N'archived',N'draft',
                                N'retired',N'historical',N'conflict');

SELECT N'ref_kind_outside_enum' AS [check], COUNT(*) AS [violations] FROM [dbo].[agent_memory_references]
 WHERE [pub_ref_kind] NOT IN (N'cites',N'supports',N'supersedes',N'derived_from',N'disambiguates',
                              N'contradicts',N'violates',N'contains',N'next');

-- 6d: bodies already over the cap — these become 'legacy' in Part B (B4).
--     Reported, not blocking: WITH NOCHECK lets them survive until decomposed.
SELECT N'bodies_over_cap' AS [check], COUNT(*) AS [count] FROM [dbo].[agent_memory_entries]
 WHERE LEN([pub_body]) > 15000;

-- 6e: structural edges are derived correctly (expect 0 rows today — no
--     contains/next edges exist until spec chaining lands in Part B)
SELECT N'structural_edges' AS [check], COUNT(*) AS [count]
  FROM [dbo].[agent_memory_references] WHERE [pub_is_structural] = 1;

-- 6f: reflection registration is complete and accurate
SELECT t.pub_name AS [table], c.pub_ordinal, c.pub_name AS [column],
       ty.pub_mssql_type, c.pub_is_nullable, c.pub_is_primary_key
  FROM system_objects_database_tables t
  JOIN system_objects_database_columns c ON c.ref_table_guid = t.key_guid
  JOIN system_objects_types ty           ON ty.key_guid      = c.ref_type_guid
 WHERE t.pub_name IN (N'agent_memory_entries', N'agent_memory_aliases', N'agent_memory_documents',
                      N'agent_memory_entry_documents', N'agent_memory_maintenance_queue')
 ORDER BY t.pub_name, c.pub_ordinal;

-- 6g: reflection matches the live catalogue (expect 0 rows = no drift)
SELECT N'reflection_drift' AS [check], t.pub_name AS [table], c.pub_name AS [column]
  FROM system_objects_database_tables t
  JOIN system_objects_database_columns c ON c.ref_table_guid = t.key_guid
  LEFT JOIN sys.columns sc ON sc.object_id = OBJECT_ID(N'[dbo].' + QUOTENAME(t.pub_name))
                          AND sc.name = c.pub_name
 WHERE t.pub_name IN (N'agent_memory_entries', N'agent_memory_aliases', N'agent_memory_documents',
                      N'agent_memory_entry_documents', N'agent_memory_maintenance_queue')
   AND sc.name IS NULL;
