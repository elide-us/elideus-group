-- ============================================================================
-- v0.12.21.0 — Placeholder Content Pages
--
-- Creates page definitions and component tree subtrees for the three public
-- content routes that currently render empty ContentPanels:
--   /gallery  → SimplePage with "Gallery — Coming soon" placeholder
--   /products → SimplePage with "Products — Coming soon" placeholder
--   /wiki     → SimplePage with "Wiki — Coming soon" placeholder
--
-- FK constraint chain requires this insertion order:
--   1. Component tree root nodes (no parent, no page ref yet)
--   2. Page definitions (ref_root_component_guid → tree nodes from step 1)
--   3. Component tree child nodes (ref_parent_guid → roots, ref_page_guid → pages)
--   4. Update root nodes to set ref_page_guid (back-fill after pages exist)
--   5. Update routes (ref_root_node_guid → roots, ref_page_guid → pages)
--
-- Idempotent: uses MERGE for inserts. Safe to re-run.
-- ============================================================================

SET NOCOUNT ON;

-- Reference GUIDs (from live system_objects_components):
-- SimplePage:   B501C466-0ADD-5BCF-9BBB-8B7607DDBBEC
-- LabelElement: E2D54B31-291F-586B-98E6-BAC7DCE58C2A

-- New GUIDs for this migration:
-- Gallery page:    A1A2A3A4-B1B2-5C1C-D1D2-E1E2F1F2A1A2
-- Gallery root:    D1D2D3D4-E1E2-5F1F-A1A2-B1B2C1C2D1D2
-- Gallery label:   E1E2E3E4-F1F2-5A1A-B1B2-C1C2D1D2E1E2
-- Products page:   A2A3A4A5-B2B3-5C2C-D2D3-E2E3F2F3A2A3
-- Products root:   D2D3D4D5-E2E3-5F2F-A2A3-B2B3C2C3D2D3
-- Products label:  E2E3E4E5-F2F3-5A2A-B2B3-C2C3D2D3E2E3
-- Wiki page:       A3A4A5A6-B3B4-5C3C-D3D4-E3E4F3F4A3A4
-- Wiki root:       D3D4D5D6-E3E4-5F3F-A3A4-B3B4C3C4D3D4
-- Wiki label:      E3E4E5E6-F3F4-5A3A-B3B4-C3C4D3D4E3E4


-- ============================================================================
-- STEP 1: Create component tree ROOT nodes (no parent, no page ref)
-- Pages FK to these, so they must exist first.
-- ============================================================================

MERGE [dbo].[system_objects_component_tree] AS target
USING (VALUES
  (N'D1D2D3D4-E1E2-5F1F-A1A2-B1B2C1C2D1D2',
   NULL, N'B501C466-0ADD-5BCF-9BBB-8B7607DDBBEC', 0),
  (N'D2D3D4D5-E2E3-5F2F-A2A3-B2B3C2C3D2D3',
   NULL, N'B501C466-0ADD-5BCF-9BBB-8B7607DDBBEC', 0),
  (N'D3D4D5D6-E3E4-5F3F-A3A4-B3B4C3C4D3D4',
   NULL, N'B501C466-0ADD-5BCF-9BBB-8B7607DDBBEC', 0)
) AS src ([key_guid], [ref_parent_guid], [ref_component_guid], [pub_sequence])
ON target.[key_guid] = src.[key_guid]
WHEN NOT MATCHED THEN INSERT
  ([key_guid], [ref_parent_guid], [ref_component_guid], [pub_sequence])
VALUES
  (src.[key_guid], src.[ref_parent_guid], src.[ref_component_guid], src.[pub_sequence]);

PRINT 'Step 1: Created 3 component tree root nodes (SimplePage)';
GO


-- ============================================================================
-- STEP 2: Create page definitions
-- ref_root_component_guid points at the tree roots created in Step 1.
-- ============================================================================

MERGE [dbo].[system_objects_pages] AS target
USING (VALUES
  (N'A1A2A3A4-B1B2-5C1C-D1D2-E1E2F1F2A1A2',
   N'gallery', N'Gallery',
   N'Image gallery and media showcase.',
   N'PhotoLibrary',
   N'D1D2D3D4-E1E2-5F1F-A1A2-B1B2C1C2D1D2',
   NULL, NULL),
  (N'A2A3A4A5-B2B3-5C2C-D2D3-E2E3F2F3A2A3',
   N'products', N'Products',
   N'Products and services offered by The Elideus Group.',
   N'Store',
   N'D2D3D4D5-E2E3-5F2F-A2A3-B2B3C2C3D2D3',
   NULL, NULL),
  (N'A3A4A5A6-B3B4-5C3C-D3D4-E3E4F3F4A3A4',
   N'wiki', N'Wiki',
   N'Knowledge base and documentation.',
   N'MenuBook',
   N'D3D4D5D6-E3E4-5F3F-A3A4-B3B4C3C4D3D4',
   NULL, NULL)
) AS src (
  [key_guid], [pub_slug], [pub_title], [pub_description], [pub_icon],
  [ref_root_component_guid], [ref_required_role_guid], [ref_required_entitlement_guid]
)
ON target.[key_guid] = src.[key_guid]
WHEN MATCHED THEN UPDATE SET
  [pub_slug]                  = src.[pub_slug],
  [pub_title]                 = src.[pub_title],
  [pub_description]           = src.[pub_description],
  [pub_icon]                  = src.[pub_icon],
  [ref_root_component_guid]   = src.[ref_root_component_guid],
  [priv_modified_on]          = SYSUTCDATETIME()
WHEN NOT MATCHED THEN INSERT
  ([key_guid], [pub_slug], [pub_title], [pub_description], [pub_icon], [ref_root_component_guid])
VALUES
  (src.[key_guid], src.[pub_slug], src.[pub_title], src.[pub_description], src.[pub_icon], src.[ref_root_component_guid]);

PRINT 'Step 2: Created 3 page definitions (gallery, products, wiki)';
GO


-- ============================================================================
-- STEP 3: Create component tree CHILD nodes (label placeholders)
-- These reference parent roots from Step 1 and pages from Step 2.
-- ============================================================================

MERGE [dbo].[system_objects_component_tree] AS target
USING (VALUES
  (N'E1E2E3E4-F1F2-5A1A-B1B2-C1C2D1D2E1E2',
   N'D1D2D3D4-E1E2-5F1F-A1A2-B1B2C1C2D1D2',
   N'E2D54B31-291F-586B-98E6-BAC7DCE58C2A',
   N'Gallery — Coming soon', 1,
   N'A1A2A3A4-B1B2-5C1C-D1D2-E1E2F1F2A1A2'),
  (N'E2E3E4E5-F2F3-5A2A-B2B3-C2C3D2D3E2E3',
   N'D2D3D4D5-E2E3-5F2F-A2A3-B2B3C2C3D2D3',
   N'E2D54B31-291F-586B-98E6-BAC7DCE58C2A',
   N'Products — Coming soon', 1,
   N'A2A3A4A5-B2B3-5C2C-D2D3-E2E3F2F3A2A3'),
  (N'E3E4E5E6-F3F4-5A3A-B3B4-C3C4D3D4E3E4',
   N'D3D4D5D6-E3E4-5F3F-A3A4-B3B4C3C4D3D4',
   N'E2D54B31-291F-586B-98E6-BAC7DCE58C2A',
   N'Wiki — Coming soon', 1,
   N'A3A4A5A6-B3B4-5C3C-D3D4-E3E4F3F4A3A4')
) AS src ([key_guid], [ref_parent_guid], [ref_component_guid], [pub_label], [pub_sequence], [ref_page_guid])
ON target.[key_guid] = src.[key_guid]
WHEN NOT MATCHED THEN INSERT
  ([key_guid], [ref_parent_guid], [ref_component_guid], [pub_label], [pub_sequence], [ref_page_guid])
VALUES
  (src.[key_guid], src.[ref_parent_guid], src.[ref_component_guid], src.[pub_label], src.[pub_sequence], src.[ref_page_guid]);

PRINT 'Step 3: Created 3 label child nodes';
GO


-- ============================================================================
-- STEP 4: Back-fill ref_page_guid on root nodes
-- Root nodes were created without page refs (pages didn't exist yet).
-- ============================================================================

UPDATE [dbo].[system_objects_component_tree]
SET [ref_page_guid] = N'A1A2A3A4-B1B2-5C1C-D1D2-E1E2F1F2A1A2',
    [priv_modified_on] = SYSUTCDATETIME()
WHERE [key_guid] = N'D1D2D3D4-E1E2-5F1F-A1A2-B1B2C1C2D1D2';

UPDATE [dbo].[system_objects_component_tree]
SET [ref_page_guid] = N'A2A3A4A5-B2B3-5C2C-D2D3-E2E3F2F3A2A3',
    [priv_modified_on] = SYSUTCDATETIME()
WHERE [key_guid] = N'D2D3D4D5-E2E3-5F2F-A2A3-B2B3C2C3D2D3';

UPDATE [dbo].[system_objects_component_tree]
SET [ref_page_guid] = N'A3A4A5A6-B3B4-5C3C-D3D4-E3E4F3F4A3A4',
    [priv_modified_on] = SYSUTCDATETIME()
WHERE [key_guid] = N'D3D4D5D6-E3E4-5F3F-A3A4-B3B4C3C4D3D4';

PRINT 'Step 4: Back-filled ref_page_guid on root nodes';
GO


-- ============================================================================
-- STEP 5: Update routes to point at new page roots
-- Using pub_path for matching (safer than GUIDs across environments).
-- ============================================================================

UPDATE [dbo].[system_objects_routes]
SET [ref_root_node_guid] = N'D1D2D3D4-E1E2-5F1F-A1A2-B1B2C1C2D1D2',
    [ref_page_guid]      = N'A1A2A3A4-B1B2-5C1C-D1D2-E1E2F1F2A1A2',
    [priv_modified_on]   = SYSUTCDATETIME()
WHERE [pub_path] = N'/gallery';

UPDATE [dbo].[system_objects_routes]
SET [ref_root_node_guid] = N'D2D3D4D5-E2E3-5F2F-A2A3-B2B3C2C3D2D3',
    [ref_page_guid]      = N'A2A3A4A5-B2B3-5C2C-D2D3-E2E3F2F3A2A3',
    [priv_modified_on]   = SYSUTCDATETIME()
WHERE [pub_path] = N'/products';

UPDATE [dbo].[system_objects_routes]
SET [ref_root_node_guid] = N'D3D4D5D6-E3E4-5F3F-A3A4-B3B4C3C4D3D4',
    [ref_page_guid]      = N'A3A4A5A6-B3B4-5C3C-D3D4-E3E4F3F4A3A4',
    [priv_modified_on]   = SYSUTCDATETIME()
WHERE [pub_path] = N'/wiki';

PRINT 'Step 5: Updated routes /gallery, /products, /wiki';
GO


-- ============================================================================
-- VERIFICATION
-- ============================================================================

PRINT '--- Page definitions (should be 5) ---';
SELECT pub_slug, pub_title, pub_icon,
  CASE WHEN ref_root_component_guid IS NOT NULL THEN 'YES' ELSE 'NO' END AS has_root
FROM [dbo].[system_objects_pages]
ORDER BY pub_slug;

PRINT '--- Routes with page bindings ---';
SELECT pub_path, pub_title,
  CASE WHEN ref_page_guid IS NOT NULL THEN 'YES' ELSE 'NO' END AS has_page,
  CASE WHEN ref_root_node_guid = N'EE3B1A30-83A2-5990-96FE-99F8154138E3'
    THEN 'SHELL' ELSE 'PAGE' END AS root_type
FROM [dbo].[system_objects_routes]
ORDER BY pub_sequence;

PRINT '--- New component tree nodes (should be 6) ---';
SELECT
  c.pub_name AS component,
  ct.pub_label AS label,
  ct.pub_sequence AS seq,
  CASE WHEN ct.ref_parent_guid IS NULL THEN 'ROOT' ELSE 'CHILD' END AS node_type,
  CASE WHEN ct.ref_page_guid IS NOT NULL THEN 'YES' ELSE 'NO' END AS has_page_ref
FROM [dbo].[system_objects_component_tree] ct
JOIN [dbo].[system_objects_components] c ON c.key_guid = ct.ref_component_guid
WHERE ct.key_guid IN (
  N'D1D2D3D4-E1E2-5F1F-A1A2-B1B2C1C2D1D2',
  N'D2D3D4D5-E2E3-5F2F-A2A3-B2B3C2C3D2D3',
  N'D3D4D5D6-E3E4-5F3F-A3A4-B3B4C3C4D3D4',
  N'E1E2E3E4-F1F2-5A1A-B1B2-C1C2D1D2E1E2',
  N'E2E3E4E5-F2F3-5A2A-B2B3-C2C3D2D3E2E3',
  N'E3E4E5E6-F3F4-5A3A-B3B4-C3C4D3D4E3E4'
)
ORDER BY ct.ref_page_guid, ct.pub_sequence;

PRINT 'v0.12.21.0 seed complete.';
GO