-- ============================================================================
-- v0.12.28.2 — Properties System
--
-- Three-layer property resolution:
--   1. Property Catalog — universal dictionary of all properties
--   2. Component Defaults — a component's declared default property values
--   3. Instance Overrides — property overrides on a specific tree node
--
-- Resolution chain: instance override → component default → catalog default
--
-- Type GUIDs:
--   STRING  = 0093B404-1EEE-563D-9135-4B9E7EECA7A2
--   INT32   = E3EDE0CE-2A03-501E-A796-3487BEA03B7B
--   BOOL    = 12B2F03B-E315-50A5-B631-E6B1EB961A17
-- ============================================================================


-- ============================================================================
-- 1. Property Catalog — what properties exist
-- ============================================================================

IF NOT EXISTS (SELECT 1 FROM sys.tables WHERE name = 'system_objects_properties')
CREATE TABLE system_objects_properties (
  key_guid            UNIQUEIDENTIFIER NOT NULL PRIMARY KEY,
  pub_name            NVARCHAR(128)    NOT NULL,
  pub_category        NVARCHAR(64)     NOT NULL,  -- 'layout', 'style', 'behavior'
  pub_description     NVARCHAR(512)    NULL,
  ref_type_guid       UNIQUEIDENTIFIER NOT NULL,
  pub_default_value   NVARCHAR(256)    NULL,       -- catalog-level default
  pub_is_active       BIT              NOT NULL DEFAULT 1,
  priv_created_on     DATETIMEOFFSET(7) NOT NULL DEFAULT SYSUTCDATETIME(),
  priv_modified_on    DATETIMEOFFSET(7) NOT NULL DEFAULT SYSUTCDATETIME(),

  CONSTRAINT UQ_sop_name UNIQUE (pub_name),
  CONSTRAINT FK_sop_type FOREIGN KEY (ref_type_guid)
    REFERENCES system_objects_types(key_guid)
);


-- ============================================================================
-- 2. Component Defaults — a component's declared default values
-- ============================================================================

IF NOT EXISTS (SELECT 1 FROM sys.tables WHERE name = 'system_objects_component_properties')
CREATE TABLE system_objects_component_properties (
  key_guid            UNIQUEIDENTIFIER NOT NULL PRIMARY KEY,
  ref_component_guid  UNIQUEIDENTIFIER NOT NULL,
  ref_property_guid   UNIQUEIDENTIFIER NOT NULL,
  pub_value           NVARCHAR(256)    NULL,
  priv_created_on     DATETIMEOFFSET(7) NOT NULL DEFAULT SYSUTCDATETIME(),
  priv_modified_on    DATETIMEOFFSET(7) NOT NULL DEFAULT SYSUTCDATETIME(),

  CONSTRAINT UQ_socp_component_property UNIQUE (ref_component_guid, ref_property_guid),
  CONSTRAINT FK_socp_component FOREIGN KEY (ref_component_guid)
    REFERENCES system_objects_components(key_guid),
  CONSTRAINT FK_socp_property FOREIGN KEY (ref_property_guid)
    REFERENCES system_objects_properties(key_guid)
);


-- ============================================================================
-- 3. Instance Overrides — per-tree-node overrides
-- ============================================================================

IF NOT EXISTS (SELECT 1 FROM sys.tables WHERE name = 'system_objects_tree_node_properties')
CREATE TABLE system_objects_tree_node_properties (
  key_guid            UNIQUEIDENTIFIER NOT NULL PRIMARY KEY,
  ref_tree_node_guid  UNIQUEIDENTIFIER NOT NULL,
  ref_property_guid   UNIQUEIDENTIFIER NOT NULL,
  pub_value           NVARCHAR(256)    NULL,
  priv_created_on     DATETIMEOFFSET(7) NOT NULL DEFAULT SYSUTCDATETIME(),
  priv_modified_on    DATETIMEOFFSET(7) NOT NULL DEFAULT SYSUTCDATETIME(),

  CONSTRAINT UQ_sotnp_node_property UNIQUE (ref_tree_node_guid, ref_property_guid),
  CONSTRAINT FK_sotnp_tree_node FOREIGN KEY (ref_tree_node_guid)
    REFERENCES system_objects_component_tree(key_guid),
  CONSTRAINT FK_sotnp_property FOREIGN KEY (ref_property_guid)
    REFERENCES system_objects_properties(key_guid)
);


-- ============================================================================
-- 4. Seed Property Catalog — initial layout/style/behavior properties
-- ============================================================================

MERGE INTO system_objects_properties AS target
USING (VALUES
  -- Layout properties
  (N'EBB1E225-658F-5BA3-8701-89C49FEDCD6D', N'layout_direction',   N'layout',   N'Child arrangement direction: row or column.',                                N'0093B404-1EEE-563D-9135-4B9E7EECA7A2', N'column'),
  (N'D023E361-58D8-5672-95F6-0042051A093C', N'layout_group',       N'layout',   N'Siblings sharing a group number form an implicit row container.',             N'E3EDE0CE-2A03-501E-A796-3487BEA03B7B', NULL),
  (N'E0E6EA55-16D6-5E40-BB8A-DB18100E431C', N'layout_size',        N'layout',   N'Sizing mode: flex, fixed, or auto.',                                          N'0093B404-1EEE-563D-9135-4B9E7EECA7A2', N'auto'),
  (N'E77E898D-85EE-5330-89EF-AE6AF66778E1', N'layout_width',       N'layout',   N'Fixed width in pixels. Only applies when layout_size = fixed.',               N'E3EDE0CE-2A03-501E-A796-3487BEA03B7B', NULL),
  (N'0008367D-32A9-5A88-9BEE-07DFA5D91A90', N'layout_height',      N'layout',   N'Fixed height in pixels.',                                                     N'E3EDE0CE-2A03-501E-A796-3487BEA03B7B', NULL),
  (N'EF5A5912-51C9-56F5-8474-48939BFC67AE', N'layout_min_height',  N'layout',   N'Minimum height in pixels.',                                                   N'E3EDE0CE-2A03-501E-A796-3487BEA03B7B', NULL),
  (N'86AE8BEE-2E59-5AA2-85A0-2EB07CFE54E9', N'layout_min_width',   N'layout',   N'Minimum width in pixels.',                                                    N'E3EDE0CE-2A03-501E-A796-3487BEA03B7B', NULL),
  (N'CD77D1F6-68B2-5DAF-B09C-C3E322D0ABA1', N'layout_flex',        N'layout',   N'Flex grow factor. Default 1 for flex-sized children.',                         N'E3EDE0CE-2A03-501E-A796-3487BEA03B7B', N'1'),
  (N'8621A661-890F-5D05-8B2E-04B0EE60A5E8', N'layout_collapsible', N'layout',   N'Whether this node wraps in a collapsible section.',                            N'12B2F03B-E315-50A5-B631-E6B1EB961A17', N'false'),
  (N'2800B8A8-45E4-52D4-BB35-56C1134DD483', N'layout_gap',         N'layout',   N'Gap between children in pixels.',                                              N'E3EDE0CE-2A03-501E-A796-3487BEA03B7B', N'4'),
  (N'D9DAED31-32A6-5095-9CB4-2C0B5CB4C81A', N'layout_padding',     N'layout',   N'Inner padding in pixels or CSS shorthand.',                                    N'0093B404-1EEE-563D-9135-4B9E7EECA7A2', NULL),
  (N'20416202-39FC-5E0F-9962-5D68B1BBCE44', N'layout_overflow',    N'layout',   N'Overflow behavior: visible, hidden, scroll, auto.',                            N'0093B404-1EEE-563D-9135-4B9E7EECA7A2', N'visible'),

  -- Style properties
  (N'D9B82418-B3A4-5B16-AA6F-9FDD75848E27', N'style_background',   N'style',    N'Background color or gradient.',                                               N'0093B404-1EEE-563D-9135-4B9E7EECA7A2', NULL),
  (N'0006269B-63CF-56F0-A70E-C71988069F88', N'style_border',       N'style',    N'Border CSS shorthand.',                                                        N'0093B404-1EEE-563D-9135-4B9E7EECA7A2', NULL),
  (N'6CC34BE7-20A9-5F17-B2AE-53E377D3CEFC', N'style_border_radius',N'style',    N'Border radius in pixels.',                                                     N'E3EDE0CE-2A03-501E-A796-3487BEA03B7B', NULL),
  (N'675493A0-998E-5229-A240-DFF63404C12C', N'style_color',        N'style',    N'Text color.',                                                                  N'0093B404-1EEE-563D-9135-4B9E7EECA7A2', NULL),
  (N'50E5A78A-C6E5-5C76-99C0-23E2FDD51D15', N'style_opacity',      N'style',    N'Opacity from 0.0 to 1.0.',                                                     N'0093B404-1EEE-563D-9135-4B9E7EECA7A2', N'1'),

  -- Behavior properties
  (N'7E5FB4CB-2D88-5D13-839A-DA6BDD646779', N'behavior_visible',   N'behavior', N'Whether this node is visible.',                                                N'12B2F03B-E315-50A5-B631-E6B1EB961A17', N'true'),
  (N'7124E58D-166C-57E3-BDE3-6E20DC6D3E02', N'behavior_disabled',  N'behavior', N'Whether this node is disabled for interaction.',                               N'12B2F03B-E315-50A5-B631-E6B1EB961A17', N'false'),
  (N'39469448-7AD1-54A5-99B3-BCC426740FBE', N'behavior_tooltip',   N'behavior', N'Tooltip text on hover.',                                                       N'0093B404-1EEE-563D-9135-4B9E7EECA7A2', NULL)
) AS src (key_guid, pub_name, pub_category, pub_description, ref_type_guid, pub_default_value)
ON target.key_guid = TRY_CAST(src.key_guid AS UNIQUEIDENTIFIER)
WHEN MATCHED THEN UPDATE SET
  pub_name = src.pub_name,
  pub_category = src.pub_category,
  pub_description = src.pub_description,
  ref_type_guid = TRY_CAST(src.ref_type_guid AS UNIQUEIDENTIFIER),
  pub_default_value = src.pub_default_value,
  priv_modified_on = SYSUTCDATETIME()
WHEN NOT MATCHED THEN INSERT
  (key_guid, pub_name, pub_category, pub_description, ref_type_guid, pub_default_value)
VALUES
  (TRY_CAST(src.key_guid AS UNIQUEIDENTIFIER), src.pub_name, src.pub_category,
   src.pub_description, TRY_CAST(src.ref_type_guid AS UNIQUEIDENTIFIER), src.pub_default_value);


-- ============================================================================
-- 5. Seed Component Defaults — PropertyPanel declares width=280
-- ============================================================================

-- PropertyPanel default: layout_size = fixed, layout_width = 280
MERGE INTO system_objects_component_properties AS target
USING (VALUES
  -- PropertyPanel (CE8C2A85): fixed width 280
  (N'CE8C2A85-BD51-5994-8278-005D0D4A4C1D', N'E0E6EA55-16D6-5E40-BB8A-DB18100E431C', N'fixed'),
  (N'CE8C2A85-BD51-5994-8278-005D0D4A4C1D', N'E77E898D-85EE-5330-89EF-AE6AF66778E1', N'280'),

  -- ComponentPreview (3181D03C): flex, min-height 200
  (N'3181D03C-15F6-554D-841C-623CD51635AA', N'E0E6EA55-16D6-5E40-BB8A-DB18100E431C', N'flex'),
  (N'3181D03C-15F6-554D-841C-623CD51635AA', N'EF5A5912-51C9-56F5-8474-48939BFC67AE', N'200'),

  -- ComponentTreePanel (BE00786B): collapsible
  (N'BE00786B-C289-5963-A8C8-3D0AFFC6D6A7', N'8621A661-890F-5D05-8B2E-04B0EE60A5E8', N'true'),

  -- QueryPreviewPanel (4475FF51): collapsible
  (N'4475FF51-0E31-5CE6-AFDA-DB3EC760200D', N'8621A661-890F-5D05-8B2E-04B0EE60A5E8', N'true'),

  -- ContractPanel (0FB4B481): collapsible
  (N'0FB4B481-AEB9-504D-AAEC-1B37650DC722', N'8621A661-890F-5D05-8B2E-04B0EE60A5E8', N'true')
) AS src (ref_component_guid, ref_property_guid, pub_value)
ON target.ref_component_guid = TRY_CAST(src.ref_component_guid AS UNIQUEIDENTIFIER)
  AND target.ref_property_guid = TRY_CAST(src.ref_property_guid AS UNIQUEIDENTIFIER)
WHEN MATCHED THEN UPDATE SET
  pub_value = src.pub_value,
  priv_modified_on = SYSUTCDATETIME()
WHEN NOT MATCHED THEN INSERT
  (key_guid, ref_component_guid, ref_property_guid, pub_value)
VALUES
  (NEWID(), TRY_CAST(src.ref_component_guid AS UNIQUEIDENTIFIER),
   TRY_CAST(src.ref_property_guid AS UNIQUEIDENTIFIER), src.pub_value);


-- ============================================================================
-- 6. Seed Instance Overrides — ComponentBuilder's tree node overrides
--
-- These are what ComponentBuilder says about how its children render
-- in this specific composition. These override the component defaults
-- only in this context.
-- ============================================================================

MERGE INTO system_objects_tree_node_properties AS target
USING (VALUES
  -- ComponentPreview node (38FD4EA5): group 1
  (N'38FD4EA5-53BA-543F-A24B-2D2B2269D136', N'D023E361-58D8-5672-95F6-0042051A093C', N'1'),

  -- PropertyPanel node (4B1E71A4): group 1
  (N'4B1E71A4-511B-574C-B4BE-C397A6412D84', N'D023E361-58D8-5672-95F6-0042051A093C', N'1')

  -- Note: collapsible is already a component default for the bottom 3,
  -- no instance override needed unless ComponentBuilder wants to
  -- override it to non-collapsible in this context.
) AS src (ref_tree_node_guid, ref_property_guid, pub_value)
ON target.ref_tree_node_guid = TRY_CAST(src.ref_tree_node_guid AS UNIQUEIDENTIFIER)
  AND target.ref_property_guid = TRY_CAST(src.ref_property_guid AS UNIQUEIDENTIFIER)
WHEN MATCHED THEN UPDATE SET
  pub_value = src.pub_value,
  priv_modified_on = SYSUTCDATETIME()
WHEN NOT MATCHED THEN INSERT
  (key_guid, ref_tree_node_guid, ref_property_guid, pub_value)
VALUES
  (NEWID(), TRY_CAST(src.ref_tree_node_guid AS UNIQUEIDENTIFIER),
   TRY_CAST(src.ref_property_guid AS UNIQUEIDENTIFIER), src.pub_value);


-- ============================================================================
-- 7. Verify
-- ============================================================================

-- Property catalog
SELECT pub_name, pub_category, pub_default_value, t.pub_name AS type_name
FROM system_objects_properties p
JOIN system_objects_types t ON t.key_guid = p.ref_type_guid
ORDER BY pub_category, p.pub_name;

-- Component defaults
SELECT c.pub_name AS component, p.pub_name AS property, cp.pub_value
FROM system_objects_component_properties cp
JOIN system_objects_components c ON c.key_guid = cp.ref_component_guid
JOIN system_objects_properties p ON p.key_guid = cp.ref_property_guid
ORDER BY c.pub_name, p.pub_name;

-- Instance overrides
SELECT
  comp.pub_name AS component,
  tn.pub_label AS node_label,
  p.pub_name AS property,
  tnp.pub_value
FROM system_objects_tree_node_properties tnp
JOIN system_objects_component_tree tn ON tn.key_guid = tnp.ref_tree_node_guid
JOIN system_objects_components comp ON comp.key_guid = tn.ref_component_guid
JOIN system_objects_properties p ON p.key_guid = tnp.ref_property_guid
ORDER BY comp.pub_name, p.pub_name;
