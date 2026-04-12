-- =============================================================================
-- v0.12.13.0_seed_object_tree_rpc (CORRECTED)
-- Date: 2026-04-12
-- Purpose:
--   1) Register CmsWorkbenchModule object tree methods
--   2) Seed RPC gateway method bindings for object tree operations
--
-- FIX: RPC gateway GUID corrected from 3D0C1FC1 (route subdomain)
--      to 606C04E3 (actual io_gateways row for 'rpc').
--      All GUIDs inlined (no DECLARE across GO boundaries).
--
-- GUIDs:
--   RPC Gateway:          606C04E3-44F1-593D-9C8B-8006E0A377D3
--   CmsWorkbenchModule:   CF85FB11-5981-56B7-8E43-9D453E611D43
--   ROLE_SERVICE_ADMIN:   E8E1A4CC-0898-59F4-8B03-B2C9804516C0
--
-- UUID5 namespace: DECAFBAD-CAFE-FADE-BABE-C0FFEE420B67
-- =============================================================================

-- =============================================================================
-- 1) CmsWorkbenchModule method registrations
-- =============================================================================
INSERT INTO [dbo].[system_objects_module_methods]
  ([key_guid], [ref_module_guid], [pub_name], [pub_description], [pub_is_active])
SELECT
  src.[key_guid],
  src.[ref_module_guid],
  src.[pub_name],
  src.[pub_description],
  1
FROM (VALUES
  (N'C7C9F53E-2F31-52A0-923F-5E17CC34C1D0', N'CF85FB11-5981-56B7-8E43-9D453E611D43', N'read_object_tree_categories', N'Read top-level object tree category metadata for the workbench tree.'),
  (N'4A3681CD-8323-574F-975D-34D48AD01893', N'CF85FB11-5981-56B7-8E43-9D453E611D43', N'read_object_tree_children',   N'Read object tree children for category tables or table columns.'),
  (N'811868C6-593D-5B7A-B38C-E8AEDFD744DF', N'CF85FB11-5981-56B7-8E43-9D453E611D43', N'read_object_tree_detail',     N'Read bounded row details for a validated object tree table.')
) src([key_guid], [ref_module_guid], [pub_name], [pub_description])
WHERE NOT EXISTS (
  SELECT 1
  FROM [dbo].[system_objects_module_methods] mm
  WHERE mm.[key_guid] = src.[key_guid]
);
GO

-- =============================================================================
-- 2) RPC gateway method binding seeds
--    ref_gateway_guid = 606C04E3-44F1-593D-9C8B-8006E0A377D3 (RPC gateway)
-- =============================================================================
INSERT INTO [dbo].[system_objects_gateway_method_bindings]
  ([key_guid], [ref_gateway_guid], [pub_operation_name], [ref_method_guid],
   [pub_required_scope], [ref_required_role_guid], [ref_required_entitlement_guid],
   [pub_is_read_only], [pub_is_active])
SELECT
  src.[key_guid],
  src.[ref_gateway_guid],
  src.[pub_operation_name],
  src.[ref_method_guid],
  src.[pub_required_scope],
  src.[ref_required_role_guid],
  src.[ref_required_entitlement_guid],
  src.[pub_is_read_only],
  1
FROM (VALUES
  (N'7B9AD1AF-B07C-5F63-851F-31F4F1931C8D', N'606C04E3-44F1-593D-9C8B-8006E0A377D3', N'urn:public:route:read_object_tree_categories:1',  N'C7C9F53E-2F31-52A0-923F-5E17CC34C1D0', CAST(NULL AS NVARCHAR(128)), CAST(NULL AS UNIQUEIDENTIFIER),                          CAST(NULL AS UNIQUEIDENTIFIER), CAST(1 AS BIT)),
  (N'6C940BAC-991D-5D1D-93C9-AA561C95C3A1', N'606C04E3-44F1-593D-9C8B-8006E0A377D3', N'urn:service:objects:read_object_tree_children:1',  N'4A3681CD-8323-574F-975D-34D48AD01893', CAST(NULL AS NVARCHAR(128)), N'E8E1A4CC-0898-59F4-8B03-B2C9804516C0',                  CAST(NULL AS UNIQUEIDENTIFIER), CAST(1 AS BIT)),
  (N'936F21B6-6A18-558A-8062-0B46DFD9A034', N'606C04E3-44F1-593D-9C8B-8006E0A377D3', N'urn:service:objects:read_object_tree_detail:1',    N'811868C6-593D-5B7A-B38C-E8AEDFD744DF', CAST(NULL AS NVARCHAR(128)), N'E8E1A4CC-0898-59F4-8B03-B2C9804516C0',                  CAST(NULL AS UNIQUEIDENTIFIER), CAST(1 AS BIT))
) src([key_guid], [ref_gateway_guid], [pub_operation_name], [ref_method_guid], [pub_required_scope], [ref_required_role_guid], [ref_required_entitlement_guid], [pub_is_read_only])
WHERE NOT EXISTS (
  SELECT 1
  FROM [dbo].[system_objects_gateway_method_bindings] b
  WHERE b.[key_guid] = src.[key_guid]
);
GO

-- =============================================================================
-- 3) Verification
-- =============================================================================
SELECT mm.pub_name AS method, mod.pub_state_attr AS module
FROM system_objects_module_methods mm
JOIN system_objects_modules mod ON mod.key_guid = mm.ref_module_guid
WHERE mm.ref_module_guid = N'CF85FB11-5981-56B7-8E43-9D453E611D43'
ORDER BY mm.pub_name;
GO

SELECT b.pub_operation_name, mm.pub_name AS method, b.pub_is_read_only,
       CASE WHEN b.ref_required_role_guid IS NOT NULL THEN 'SERVICE_ADMIN' ELSE 'public' END AS access
FROM system_objects_gateway_method_bindings b
JOIN system_objects_module_methods mm ON mm.key_guid = b.ref_method_guid
WHERE b.key_guid IN (
  N'7B9AD1AF-B07C-5F63-851F-31F4F1931C8D',
  N'6C940BAC-991D-5D1D-93C9-AA561C95C3A1',
  N'936F21B6-6A18-558A-8062-0B46DFD9A034'
)
ORDER BY b.pub_operation_name;
GO
