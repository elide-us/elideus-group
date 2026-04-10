-- ============================================================================
-- TheOracleRPC v0.12.4.0 — CMS Engine Seed Data
-- Date: 2026-04-09
-- Purpose:
--   Populate the CMS engine tables created in v0.12.3.0 with:
--     1. Component registrations (21 components)
--     2. Workbench component tree (13 tree nodes)
--     3. Type-to-control default mappings (12 mappings)
--     4. Route registrations (17 routes)
--
-- All GUIDs are deterministic UUID5 from namespace DECAFBAD-CAFE-FADE-BABE-C0FFEE420B67.
-- Same script, same data, every environment. No drift.
--
-- Key formulas:
--   Components:    uuid5(NS, 'component:{pub_name}')
--   Tree nodes:    uuid5(NS, 'tree:{full.dot.path}')
--   Type controls: uuid5(NS, 'typecontrol:{type_name}.{component_name}')
--   Routes:        uuid5(NS, 'route:{pub_path}')
--
-- NOTE: This seeds component headers only — the name, category, description,
--       and default type binding for each component. The rendering contracts,
--       module API surface, and implementation code are defined separately.
-- ============================================================================


-- ============================================================================
-- 1. Component Registry — 21 registrations
--    1 page + 9 section + 11 control
-- ============================================================================

INSERT INTO [dbo].[system_objects_components]
  ([key_guid], [pub_name], [pub_category], [pub_description], [ref_default_type_guid])
VALUES
-- Page (1)
(N'1850A30E-D4F3-5437-87B2-4C39B33B56E5', N'Workbench',          N'page',    N'Root application shell. Contains NavigationSidebar and ContentPanel. Manages mode state (standard/dev).', NULL),

-- Section (9)
(N'9315F484-9EC0-56EA-9720-20676B3742C1', N'NavigationSidebar',  N'section', N'Vertical sidebar with header, content, and footer slots.',                                                NULL),
(N'794E91C4-AF73-58F5-823E-924465A5F62B', N'SidebarHeader',      N'section', N'Top-pinned container within the sidebar.',                                                                NULL),
(N'8145D3C6-8417-5731-A243-DDBAC5B05771', N'SidebarContent',     N'section', N'Scrollable middle container. Renders NavigationTreeView or ObjectTreeView based on mode.',                 NULL),
(N'DB3E7A4F-E769-5058-95C4-6A47FEB8E377', N'SidebarFooter',      N'section', N'Bottom-pinned container within the sidebar.',                                                              NULL),
(N'F0554091-5683-553E-B55F-162610002798', N'NavigationTreeView', N'section', N'Hierarchical tree of navigable routes. Role-masked. Standard mode.',                                       NULL),
(N'44AC851E-CE61-56A8-88B8-AD76A7D66606', N'ObjectTreeView',     N'section', N'Live editable view of system_objects tree. Dev mode.',                                                     NULL),
(N'091A6979-C04A-5816-A896-7B0C61AE6361', N'ContentPanel',       N'section', N'Main content area. Hosts CMS-rendered pages (standard) or ObjectEditor (dev).',                            NULL),
(N'B99BD3E1-8267-5775-91C5-88F75EB038F2', N'ObjectEditor',       N'section', N'Object detail editor rendered inside ContentPanel in dev mode.',                                            NULL),
(N'A8CECA1D-A140-5181-A6DB-775A2FF73D26', N'CollapsibleSection', N'section', N'Expandable/collapsible container with header label.',                                                      NULL),

-- Control (11)
(N'0A365B2D-843F-5EC4-9FBB-88D349C6DEB4', N'NavigationItem',    N'control', N'Clickable route item in navigation tree. Icon and label.',                                                 NULL),
(N'BB6DDFFF-44C4-5D74-B1F8-14298D37FC08', N'ObjectTreeNode',    N'control', N'Node in the object tree. Icon and name, expand/collapse.',                                                 NULL),
(N'2406E984-BED7-5E4A-B844-EE4977F2F9F1', N'LoginControl',      N'control', N'Authentication widget. Login/user state.',                                                                 NULL),
(N'CAB5888A-9F06-5608-9A0E-C9D197605EA2', N'UserProfileControl',N'control', N'User avatar, name, logout action.',                                                                        NULL),
(N'1E78CE96-0BBA-57EA-AD67-D71775EF7A67', N'DevModeToggle',     N'control', N'Toggle for switching between standard and dev mode. ROLE_SERVICE_ADMIN only.',                              N'12B2F03B-E315-50A5-B631-E6B1EB961A17'),
(N'B9A629DB-ECD0-536F-80B3-D580CC13F549', N'HamburgerToggle',   N'control', N'Sidebar drawer expand/collapse button.',                                                                   NULL),
(N'64D2E77E-74A0-5D88-9138-46CF848F5017', N'StringControl',     N'control', N'Single-line text input/display.',                                                                          N'0093B404-1EEE-563D-9135-4B9E7EECA7A2'),
(N'3013D91D-9A96-536C-A76D-A8F18DC7EDAC', N'BoolToggle',        N'control', N'Toggle switch or checkbox.',                                                                               N'12B2F03B-E315-50A5-B631-E6B1EB961A17'),
(N'E3C972D6-0EE7-570A-87EB-0A9228809BFC', N'IntControl',        N'control', N'Integer input with optional formatting.',                                                                  N'E3EDE0CE-2A03-501E-A796-3487BEA03B7B'),
(N'D5C2C1A8-7E78-5579-BB0D-C0C9A004CE4A', N'ReadOnlyDisplay',   N'control', N'Generic read-only value display for any type.',                                                            NULL),
(N'65CC86B2-E961-56AD-9C07-FDF78A57F301', N'ButtonLinkControl', N'control', N'Clickable button-style link to a route or URL.',                                                           NULL);
GO


-- ============================================================================
-- 2. Workbench Component Tree — 13 nodes
--    Deterministic from uuid5(NS, 'tree:{full.dot.path}')
--
--    Workbench
--    ├── NavigationSidebar
--    │   ├── SidebarHeader
--    │   │   └── HamburgerToggle
--    │   ├── SidebarContent
--    │   │   ├── NavigationTreeView    (standard mode)
--    │   │   └── ObjectTreeView        (dev mode)
--    │   └── SidebarFooter
--    │       ├── LoginControl
--    │       ├── UserProfileControl
--    │       └── DevModeToggle         (ROLE_SERVICE_ADMIN only)
--    └── ContentPanel
--        └── ObjectEditor              (dev mode)
-- ============================================================================

INSERT INTO [dbo].[system_objects_component_tree]
  ([key_guid], [ref_parent_guid], [ref_component_guid], [pub_sequence])
VALUES
-- Root
(N'EE3B1A30-83A2-5990-96FE-99F8154138E3', NULL,                                          N'1850A30E-D4F3-5437-87B2-4C39B33B56E5', 1),  -- Workbench

-- NavigationSidebar and its children
(N'E297DCC6-2879-5051-A78D-6AC23688C483', N'EE3B1A30-83A2-5990-96FE-99F8154138E3',       N'9315F484-9EC0-56EA-9720-20676B3742C1', 1),  -- Workbench.NavigationSidebar
(N'F23E7889-BD54-5504-83FA-6E3E4D6D58B7', N'E297DCC6-2879-5051-A78D-6AC23688C483',       N'794E91C4-AF73-58F5-823E-924465A5F62B', 1),  -- .SidebarHeader
(N'AB329EA0-4B49-53EF-8B49-921EB6751FE7', N'F23E7889-BD54-5504-83FA-6E3E4D6D58B7',       N'B9A629DB-ECD0-536F-80B3-D580CC13F549', 1),  -- .SidebarHeader.HamburgerToggle
(N'1EC83FDF-1509-57DF-82BF-4C2F399F779F', N'E297DCC6-2879-5051-A78D-6AC23688C483',       N'8145D3C6-8417-5731-A243-DDBAC5B05771', 2),  -- .SidebarContent
(N'F43EBECC-3755-542E-A15B-9C3891F24D18', N'1EC83FDF-1509-57DF-82BF-4C2F399F779F',       N'F0554091-5683-553E-B55F-162610002798', 1),  -- .SidebarContent.NavigationTreeView
(N'5CACE551-8AC7-530F-A8D1-910248778F7C', N'1EC83FDF-1509-57DF-82BF-4C2F399F779F',       N'44AC851E-CE61-56A8-88B8-AD76A7D66606', 2),  -- .SidebarContent.ObjectTreeView
(N'4AA281E5-175E-58DA-A659-6BD0D4690A81', N'E297DCC6-2879-5051-A78D-6AC23688C483',       N'DB3E7A4F-E769-5058-95C4-6A47FEB8E377', 3),  -- .SidebarFooter
(N'F08E9791-30DE-54BE-A85C-8C550FEFA093', N'4AA281E5-175E-58DA-A659-6BD0D4690A81',       N'2406E984-BED7-5E4A-B844-EE4977F2F9F1', 1),  -- .SidebarFooter.LoginControl
(N'63B0486E-368C-5494-AC89-FDC68C8AD429', N'4AA281E5-175E-58DA-A659-6BD0D4690A81',       N'CAB5888A-9F06-5608-9A0E-C9D197605EA2', 2),  -- .SidebarFooter.UserProfileControl
(N'96616EDE-0CA6-5188-B2BD-1397927CDD1A', N'4AA281E5-175E-58DA-A659-6BD0D4690A81',       N'1E78CE96-0BBA-57EA-AD67-D71775EF7A67', 3),  -- .SidebarFooter.DevModeToggle

-- ContentPanel and its children
(N'4D268AF7-18BB-5CD1-886C-7EFE643560D5', N'EE3B1A30-83A2-5990-96FE-99F8154138E3',       N'091A6979-C04A-5816-A896-7B0C61AE6361', 2),  -- Workbench.ContentPanel
(N'3B1C8990-F6F3-5171-A7D3-6EDFF6326C9E', N'4D268AF7-18BB-5CD1-886C-7EFE643560D5',       N'B99BD3E1-8267-5775-91C5-88F75EB038F2', 1);  -- Workbench.ContentPanel.ObjectEditor
GO


-- ============================================================================
-- 3. Type-to-Control Default Mappings — 12 mappings
--    One default control per type. 3 specific, 9 to ReadOnlyDisplay.
--    Deterministic from uuid5(NS, 'typecontrol:{type_name}.{component_name}')
-- ============================================================================

INSERT INTO [dbo].[system_objects_type_controls]
  ([key_guid], [ref_type_guid], [ref_component_guid], [pub_is_default])
VALUES
-- Specific default controls
(N'485B3561-11CD-5CBA-8F71-04F91FFB42D6', N'E3EDE0CE-2A03-501E-A796-3487BEA03B7B', N'E3C972D6-0EE7-570A-87EB-0A9228809BFC', 1),  -- INT32 → IntControl
(N'0C4E7543-18B1-5485-BD93-99516D1A7752', N'12B2F03B-E315-50A5-B631-E6B1EB961A17', N'3013D91D-9A96-536C-A76D-A8F18DC7EDAC', 1),  -- BOOL → BoolToggle
(N'AA697AFD-C849-5E76-844B-A878E4605B60', N'0093B404-1EEE-563D-9135-4B9E7EECA7A2', N'64D2E77E-74A0-5D88-9138-46CF848F5017', 1),  -- STRING → StringControl

-- ReadOnlyDisplay defaults (until dedicated controls are registered)
(N'76B27CA7-72F1-54E9-9E45-3D0628F8EEBD', N'362EB7D6-8ECF-58FA-9416-D4822410DF9F', N'D5C2C1A8-7E78-5579-BB0D-C0C9A004CE4A', 1),  -- INT64 → ReadOnlyDisplay
(N'0B4A9420-BE08-5E24-B9CB-3193E9A441BE', N'E0556F4C-ECA5-5475-B6C1-F60706632F06', N'D5C2C1A8-7E78-5579-BB0D-C0C9A004CE4A', 1),  -- INT64_IDENTITY → ReadOnlyDisplay
(N'D71F0345-7C5E-5E45-A304-F2EA824E7BCA', N'4D2EB10B-363E-5AF4-826A-9294146244E4', N'D5C2C1A8-7E78-5579-BB0D-C0C9A004CE4A', 1),  -- UUID → ReadOnlyDisplay
(N'96E60EBD-14AA-5471-827C-322CC57AC0FA', N'70F890D3-5AB5-5250-860E-4F7F9624190C', N'D5C2C1A8-7E78-5579-BB0D-C0C9A004CE4A', 1),  -- DATETIME_TZ → ReadOnlyDisplay
(N'E41DF125-036E-5419-AD41-12EAEF4A4D21', N'DCA18974-D648-5DFF-AEFB-122C081145AA', N'D5C2C1A8-7E78-5579-BB0D-C0C9A004CE4A', 1),  -- TEXT → ReadOnlyDisplay
(N'BA2CDC14-B3CD-582B-ACC1-CA5A9DBD1BC3', N'6F99D39D-EE59-56D4-A966-B0707DF806D9', N'D5C2C1A8-7E78-5579-BB0D-C0C9A004CE4A', 1),  -- INT8 → ReadOnlyDisplay
(N'7422282F-FCFD-522E-A8EA-539F6D361431', N'EA9D3720-732F-5D6B-8EB1-DD8ECC6F67F6', N'D5C2C1A8-7E78-5579-BB0D-C0C9A004CE4A', 1),  -- DATE → ReadOnlyDisplay
(N'45C3BE8E-E59F-5B97-B68D-34C6CB185BA4', N'A79190A1-FB3B-580C-8A24-445D590715BD', N'D5C2C1A8-7E78-5579-BB0D-C0C9A004CE4A', 1),  -- DECIMAL_19_5 → ReadOnlyDisplay
(N'BB24F58C-9E39-5853-8695-931C8D504A8F', N'02FDC04C-3C49-5A88-8BCE-E2B30DEE0805', N'D5C2C1A8-7E78-5579-BB0D-C0C9A004CE4A', 1);  -- DECIMAL_28_12 → ReadOnlyDisplay
GO


-- ============================================================================
-- 4. Route Registrations — 17 routes
--    Deterministic from uuid5(NS, 'route:{pub_path}')
--
--    ref_root_node_guid points to the Workbench root tree node for now.
--    As individual page component trees are defined, each route's
--    ref_root_node_guid will be updated to point to its own page tree root.
-- ============================================================================

INSERT INTO [dbo].[system_objects_routes]
  ([key_guid], [pub_path], [pub_title], [ref_root_node_guid], [pub_sequence], [pub_icon], [ref_parent_route_guid], [ref_required_role_guid], [pub_is_active])
VALUES
-- Public routes
(N'5815B7E9-B262-5890-8F00-167967C05587', N'/',                            N'Home',           N'EE3B1A30-83A2-5990-96FE-99F8154138E3', 10,  N'Home',          NULL, NULL,                                          1),
GO


-- ============================================================================
-- 5. Verification
-- ============================================================================

SELECT 'system_objects_components' AS [table], COUNT(*) AS [rows] FROM [dbo].[system_objects_components];
SELECT 'system_objects_component_tree' AS [table], COUNT(*) AS [rows] FROM [dbo].[system_objects_component_tree];
SELECT 'system_objects_type_controls' AS [table], COUNT(*) AS [rows] FROM [dbo].[system_objects_type_controls];
SELECT 'system_objects_routes' AS [table], COUNT(*) AS [rows] FROM [dbo].[system_objects_routes];

-- Components by category
SELECT [pub_category], COUNT(*) AS [count]
FROM [dbo].[system_objects_components]
GROUP BY [pub_category]
ORDER BY [pub_category];

-- Workbench tree structure
SELECT
  REPLICATE('  ', tree_depth.depth) + c.[pub_name] AS [tree],
  t.[pub_sequence] AS [seq]
FROM [dbo].[system_objects_component_tree] t
JOIN [dbo].[system_objects_components] c ON c.[key_guid] = t.[ref_component_guid]
CROSS APPLY (
  SELECT COUNT(*) AS depth
  FROM [dbo].[system_objects_component_tree] ancestor
  WHERE ancestor.[key_guid] != t.[key_guid]
    AND EXISTS (
      -- Walk up the tree to count depth
      SELECT 1
      FROM [dbo].[system_objects_component_tree] walk
      WHERE walk.[key_guid] = t.[key_guid]
        AND walk.[ref_parent_guid] IS NOT NULL
    )
) tree_depth
ORDER BY t.[pub_sequence];

-- Type-control mappings
SELECT
  typ.[pub_name] AS [type],
  comp.[pub_name] AS [default_control],
  tc.[pub_is_default]
FROM [dbo].[system_objects_type_controls] tc
JOIN [dbo].[system_objects_types] typ ON typ.[key_guid] = tc.[ref_type_guid]
JOIN [dbo].[system_objects_components] comp ON comp.[key_guid] = tc.[ref_component_guid]
ORDER BY typ.[pub_name];

-- Routes with role requirements
SELECT
  r.[pub_path],
  r.[pub_title],
  r.[pub_icon],
  r.[pub_sequence],
  role.[pub_name] AS [required_role]
FROM [dbo].[system_objects_routes] r
LEFT JOIN [dbo].[system_auth_roles] role ON role.[key_guid] = r.[ref_required_role_guid]
ORDER BY r.[pub_sequence];