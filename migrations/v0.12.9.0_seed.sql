-- ==========================================================================
-- v0.12.9.0_rpc_gateway_bindings
-- Phase 3: RPC gateway formalization seeds
--   1) Register SessionModule methods in system_objects_module_methods
--   2) Seed RPC gateway method bindings in system_objects_gateway_method_bindings
--   3) Seed missing SessionModule data-driven query:
--      security.sessions.list_user_sessions
--
-- UUID5 namespace: DECAFBAD-CAFE-FADE-BABE-C0FFEE420B67
-- ==========================================================================

DECLARE @RPC_GATEWAY_GUID UNIQUEIDENTIFIER = N'606C04E3-44F1-593D-9C8B-8006E0A377D3';
DECLARE @SESSION_MODULE_GUID UNIQUEIDENTIFIER = N'6D818DCB-5B60-5B80-91F1-A1D19DC03110';
DECLARE @ROLE_SYSTEM_ADMIN UNIQUEIDENTIFIER = N'20F0C823-4742-51BE-938B-7AA5B9D36B81';
GO

-- ==========================================================================
-- 1) SessionModule method registrations (missing from object tree)
-- ==========================================================================

INSERT INTO [dbo].[system_objects_module_methods]
  ([key_guid], [ref_module_guid], [pub_name], [pub_description], [pub_is_active])
SELECT
  src.[key_guid],
  src.[ref_module_guid],
  src.[pub_name],
  src.[pub_description],
  1
FROM (VALUES
  (N'578E9F0B-2C40-58A8-9921-4FB125A95100', N'6D818DCB-5B60-5B80-91F1-A1D19DC03110', N'issue_token',      N'Issue session and rotation tokens for authenticated provider login.'),
  (N'6221F741-E7F3-5C80-B714-7BF741CCD73B', N'6D818DCB-5B60-5B80-91F1-A1D19DC03110', N'refresh_token',    N'Refresh session token from rotation token.'),
  (N'20424F76-90C6-5A44-AF5C-0D2D22046ECD', N'6D818DCB-5B60-5B80-91F1-A1D19DC03110', N'invalidate_token', N'Revoke all active sessions for a user.'),
  (N'6C086B5F-5308-5A1D-8E8F-2ED96A92BD5F', N'6D818DCB-5B60-5B80-91F1-A1D19DC03110', N'logout_device',    N'Revoke the current device token.'),
  (N'1A025F00-F1B7-52A9-B2CE-4F617CF00858', N'6D818DCB-5B60-5B80-91F1-A1D19DC03110', N'get_session',      N'Read and validate the current session payload.')
) src([key_guid], [ref_module_guid], [pub_name], [pub_description])
WHERE NOT EXISTS (
  SELECT 1
  FROM [dbo].[system_objects_module_methods] mm
  WHERE mm.[key_guid] = src.[key_guid]
);
GO

-- ==========================================================================
-- 2) RPC gateway method binding seeds
-- ==========================================================================

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
  (N'455F2B23-1368-59E3-89E2-9FF4148D9DC9', N'606C04E3-44F1-593D-9C8B-8006E0A377D3', N'urn:public:route:load_shell:1',              N'4427A371-81DF-57C4-A16C-E03008BA1AB9', NULL, NULL, NULL, 1),
  (N'52D6E030-0C70-5E8C-83FB-F85A87AA414D', N'606C04E3-44F1-593D-9C8B-8006E0A377D3', N'urn:public:route:load_page:1',               N'D207AE62-AF24-514D-A7C5-FBEC5200DC24', NULL, NULL, NULL, 1),
  (N'DDADA624-F75E-55EF-80BE-14F7C529024C', N'606C04E3-44F1-593D-9C8B-8006E0A377D3', N'urn:public:route:read_navigation:1',         N'88EB34E5-DBF0-5254-AEE4-D61D18ACCF8F', NULL, NULL, NULL, 1),
  (N'7D5B7DA5-92BC-5325-96A5-002E70DDFBBC', N'606C04E3-44F1-593D-9C8B-8006E0A377D3', N'urn:public:auth:get_auth_state:1',           N'2D3B31B8-62EB-5CBB-A15C-C3FB19A975F6', NULL, NULL, NULL, 1),
  (N'18A3A986-8499-5BC8-B9DC-F2CA4E30CF15', N'606C04E3-44F1-593D-9C8B-8006E0A377D3', N'urn:public:auth:read_current_user:1',        N'5C9020C1-BA56-5898-A271-E0B62E00BC99', NULL, NULL, NULL, 1),
  (N'2363D705-96F7-5119-8B57-37572A7636ED', N'606C04E3-44F1-593D-9C8B-8006E0A377D3', N'urn:public:auth:context:get_user_context:1', N'C57DE8A4-674B-5D1D-AE99-A2D8CC529E11', NULL, NULL, NULL, 1),
  (N'4609D116-BE89-5752-9D8B-C2E2FC6284B7', N'606C04E3-44F1-593D-9C8B-8006E0A377D3', N'urn:system:config:read_config:1',            N'79EF9D0C-D111-555C-A77E-1C39A01E076C', NULL, N'20F0C823-4742-51BE-938B-7AA5B9D36B81', NULL, 1),
  (N'F0CB2B43-8E38-5614-80C3-A99C4EF9A36D', N'606C04E3-44F1-593D-9C8B-8006E0A377D3', N'urn:system:config:upsert_config:1',          N'573886C1-F179-5EB4-8C16-7B410041E73B', NULL, N'20F0C823-4742-51BE-938B-7AA5B9D36B81', NULL, 0),
  (N'538EA266-1B8B-5750-9B35-F4BF64A6A43C', N'606C04E3-44F1-593D-9C8B-8006E0A377D3', N'urn:system:config:delete_config:1',          N'EAE41724-3FCB-5EA6-8E5B-8F23A55B96D6', NULL, N'20F0C823-4742-51BE-938B-7AA5B9D36B81', NULL, 0),

  (N'71806D25-6FE0-5ADD-BC9C-9AC83D999020', N'606C04E3-44F1-593D-9C8B-8006E0A377D3', N'urn:auth:session:get_token:1',               N'578E9F0B-2C40-58A8-9921-4FB125A95100', NULL, NULL, NULL, 0),
  (N'5658D6E2-2393-50A8-9949-A064E00569D8', N'606C04E3-44F1-593D-9C8B-8006E0A377D3', N'urn:auth:session:refresh_token:1',           N'6221F741-E7F3-5C80-B714-7BF741CCD73B', NULL, NULL, NULL, 0),
  (N'07C67CFC-0628-5808-967B-5396BB1444E9', N'606C04E3-44F1-593D-9C8B-8006E0A377D3', N'urn:auth:session:invalidate_token:1',        N'20424F76-90C6-5A44-AF5C-0D2D22046ECD', NULL, NULL, NULL, 0),
  (N'3D4122D9-B020-5A10-95BF-821842BA1339', N'606C04E3-44F1-593D-9C8B-8006E0A377D3', N'urn:auth:session:logout_device:1',           N'6C086B5F-5308-5A1D-8E8F-2ED96A92BD5F', NULL, NULL, NULL, 0),
  (N'2CAAC3F5-7EE8-5CDE-AA54-2F4FD9190ED1', N'606C04E3-44F1-593D-9C8B-8006E0A377D3', N'urn:auth:session:get_session:1',             N'1A025F00-F1B7-52A9-B2CE-4F617CF00858', NULL, NULL, NULL, 1)
) src([key_guid], [ref_gateway_guid], [pub_operation_name], [ref_method_guid], [pub_required_scope], [ref_required_role_guid], [ref_required_entitlement_guid], [pub_is_read_only])
WHERE NOT EXISTS (
  SELECT 1
  FROM [dbo].[system_objects_gateway_method_bindings] b
  WHERE b.[key_guid] = src.[key_guid]
);
GO

-- ==========================================================================
-- 3) Missing SessionModule query seed
-- ==========================================================================

INSERT INTO [dbo].[system_objects_queries]
  ([key_guid], [pub_name], [pub_description], [ref_module_guid],
   [pub_is_parameterized], [pub_parameter_names], [pub_query_text], [pub_is_active])
SELECT
  N'75EAF5A1-37A2-5828-B8A0-6FBF495ABB4D',
  N'security.sessions.list_user_sessions',
  N'List all active sessions for a user.',
  N'6D818DCB-5B60-5B80-91F1-A1D19DC03110',
  1,
  N'user_guid',
  N'SELECT s.[key_guid] AS session_guid, s.[pub_is_active] AS is_active,
         s.[pub_expires_at] AS expires_at, st.[pub_name] AS session_type
  FROM [dbo].[system_sessions] s
  JOIN [dbo].[service_enum_values] st ON st.[key_guid] = s.[ref_session_type_guid]
  WHERE s.[ref_user_guid] = TRY_CAST(? AS UNIQUEIDENTIFIER)
    AND s.[pub_is_active] = 1
  FOR JSON PATH, INCLUDE_NULL_VALUES;',
  1
WHERE NOT EXISTS (
  SELECT 1
  FROM [dbo].[system_objects_queries] q
  WHERE q.[pub_name] = N'security.sessions.list_user_sessions'
);
GO
