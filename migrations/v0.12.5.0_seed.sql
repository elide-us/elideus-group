-- =============================================================
-- Migration v0.12.5.0: Full Object Tree Expansion
-- =============================================================
-- UUID5 Namespace: DECAFBAD-CAFE-FADE-BABE-C0FFEE420B67
-- 9 new tables, 2 altered tables, ~115 seed rows
-- =============================================================

-- =============================================================
-- PHASE 1: Standalone tables (no inter-dependencies)
-- =============================================================

-- Table 1: system_objects_modules
CREATE TABLE system_objects_modules (
    key_guid                    UNIQUEIDENTIFIER    NOT NULL    PRIMARY KEY,
    pub_name                    NVARCHAR(128)       NOT NULL    UNIQUE,
    pub_state_attr              NVARCHAR(128)       NOT NULL    UNIQUE,
    pub_module_path             NVARCHAR(256)       NOT NULL,
    pub_description             NVARCHAR(512)       NULL,
    pub_is_active               BIT                 NOT NULL    DEFAULT 1,
    priv_created_on             DATETIMEOFFSET(7)   NOT NULL    DEFAULT SYSUTCDATETIME(),
    priv_modified_on            DATETIMEOFFSET(7)   NOT NULL    DEFAULT SYSUTCDATETIME()
);

-- Table 2: system_objects_rpc_models
CREATE TABLE system_objects_rpc_models (
    key_guid                    UNIQUEIDENTIFIER    NOT NULL    PRIMARY KEY,
    pub_name                    NVARCHAR(128)       NOT NULL    UNIQUE,
    pub_description             NVARCHAR(512)       NULL,
    pub_version                 INT                 NOT NULL    DEFAULT 1,
    ref_parent_model_guid       UNIQUEIDENTIFIER    NULL,
    priv_created_on             DATETIMEOFFSET(7)   NOT NULL    DEFAULT SYSUTCDATETIME(),
    priv_modified_on            DATETIMEOFFSET(7)   NOT NULL    DEFAULT SYSUTCDATETIME(),
    CONSTRAINT FK_sorm_parent FOREIGN KEY (ref_parent_model_guid)
        REFERENCES system_objects_rpc_models(key_guid)
);

-- Table 3: system_objects_rpc_domains
CREATE TABLE system_objects_rpc_domains (
    key_guid                    UNIQUEIDENTIFIER    NOT NULL    PRIMARY KEY,
    pub_name                    NVARCHAR(64)        NOT NULL    UNIQUE,
    pub_description             NVARCHAR(512)       NULL,
    ref_required_role_guid      UNIQUEIDENTIFIER    NULL,
    pub_is_active               BIT                 NOT NULL    DEFAULT 1,
    priv_created_on             DATETIMEOFFSET(7)   NOT NULL    DEFAULT SYSUTCDATETIME(),
    priv_modified_on            DATETIMEOFFSET(7)   NOT NULL    DEFAULT SYSUTCDATETIME(),
    CONSTRAINT FK_sord_role FOREIGN KEY (ref_required_role_guid)
        REFERENCES system_auth_roles(key_guid)
);

-- =============================================================
-- PHASE 2: Tables with deps on Phase 1
-- =============================================================

-- Table 4: system_objects_rpc_model_fields
CREATE TABLE system_objects_rpc_model_fields (
    key_guid                    UNIQUEIDENTIFIER    NOT NULL    PRIMARY KEY,
    ref_model_guid              UNIQUEIDENTIFIER    NOT NULL,
    pub_name                    NVARCHAR(128)       NOT NULL,
    pub_ordinal                 INT                 NOT NULL    DEFAULT 0,
    ref_type_guid               UNIQUEIDENTIFIER    NULL,
    ref_nested_model_guid       UNIQUEIDENTIFIER    NULL,
    pub_is_nullable             BIT                 NOT NULL    DEFAULT 0,
    pub_is_list                 BIT                 NOT NULL    DEFAULT 0,
    pub_default_value           NVARCHAR(256)       NULL,
    pub_max_length              INT                 NULL,
    pub_description             NVARCHAR(512)       NULL,
    priv_created_on             DATETIMEOFFSET(7)   NOT NULL    DEFAULT SYSUTCDATETIME(),
    priv_modified_on            DATETIMEOFFSET(7)   NOT NULL    DEFAULT SYSUTCDATETIME(),
    CONSTRAINT FK_sormf_model FOREIGN KEY (ref_model_guid) REFERENCES system_objects_rpc_models(key_guid),
    CONSTRAINT FK_sormf_type FOREIGN KEY (ref_type_guid) REFERENCES system_objects_types(key_guid),
    CONSTRAINT FK_sormf_nested_model FOREIGN KEY (ref_nested_model_guid) REFERENCES system_objects_rpc_models(key_guid),
    CONSTRAINT UQ_sormf_model_name UNIQUE (ref_model_guid, pub_name)
);
CREATE INDEX IX_sormf_model ON system_objects_rpc_model_fields (ref_model_guid);

-- Table 5: system_objects_module_methods
CREATE TABLE system_objects_module_methods (
    key_guid                    UNIQUEIDENTIFIER    NOT NULL    PRIMARY KEY,
    ref_module_guid             UNIQUEIDENTIFIER    NOT NULL,
    pub_name                    NVARCHAR(128)       NOT NULL,
    pub_description             NVARCHAR(512)       NULL,
    ref_request_model_guid      UNIQUEIDENTIFIER    NULL,
    ref_response_model_guid     UNIQUEIDENTIFIER    NULL,
    pub_is_active               BIT                 NOT NULL    DEFAULT 1,
    priv_created_on             DATETIMEOFFSET(7)   NOT NULL    DEFAULT SYSUTCDATETIME(),
    priv_modified_on            DATETIMEOFFSET(7)   NOT NULL    DEFAULT SYSUTCDATETIME(),
    CONSTRAINT FK_somm_module FOREIGN KEY (ref_module_guid) REFERENCES system_objects_modules(key_guid),
    CONSTRAINT FK_somm_request_model FOREIGN KEY (ref_request_model_guid) REFERENCES system_objects_rpc_models(key_guid),
    CONSTRAINT FK_somm_response_model FOREIGN KEY (ref_response_model_guid) REFERENCES system_objects_rpc_models(key_guid),
    CONSTRAINT UQ_somm_module_method UNIQUE (ref_module_guid, pub_name)
);
CREATE INDEX IX_somm_module ON system_objects_module_methods (ref_module_guid);

-- Table 6: system_objects_rpc_subdomains
CREATE TABLE system_objects_rpc_subdomains (
    key_guid                    UNIQUEIDENTIFIER    NOT NULL    PRIMARY KEY,
    pub_name                    NVARCHAR(64)        NOT NULL,
    pub_description             NVARCHAR(512)       NULL,
    ref_domain_guid             UNIQUEIDENTIFIER    NOT NULL,
    ref_required_entitlement_guid UNIQUEIDENTIFIER  NULL,
    pub_is_active               BIT                 NOT NULL    DEFAULT 1,
    priv_created_on             DATETIMEOFFSET(7)   NOT NULL    DEFAULT SYSUTCDATETIME(),
    priv_modified_on            DATETIMEOFFSET(7)   NOT NULL    DEFAULT SYSUTCDATETIME(),
    CONSTRAINT FK_sorsd_domain FOREIGN KEY (ref_domain_guid) REFERENCES system_objects_rpc_domains(key_guid),
    CONSTRAINT FK_sorsd_entitlement FOREIGN KEY (ref_required_entitlement_guid) REFERENCES system_auth_entitlements(key_guid),
    CONSTRAINT UQ_sorsd_domain_name UNIQUE (ref_domain_guid, pub_name)
);
CREATE INDEX IX_sorsd_domain ON system_objects_rpc_subdomains (ref_domain_guid);

-- =============================================================
-- PHASE 3: Tables with deps on Phase 2
-- =============================================================

-- Table 7: system_objects_rpc_functions
CREATE TABLE system_objects_rpc_functions (
    key_guid                    UNIQUEIDENTIFIER    NOT NULL    PRIMARY KEY,
    pub_name                    NVARCHAR(128)       NOT NULL,
    pub_version                 INT                 NOT NULL    DEFAULT 1,
    pub_description             NVARCHAR(512)       NULL,
    ref_subdomain_guid          UNIQUEIDENTIFIER    NOT NULL,
    ref_method_guid             UNIQUEIDENTIFIER    NOT NULL,
    ref_required_role_guid      UNIQUEIDENTIFIER    NULL,
    ref_required_entitlement_guid UNIQUEIDENTIFIER  NULL,
    pub_is_active               BIT                 NOT NULL    DEFAULT 1,
    priv_created_on             DATETIMEOFFSET(7)   NOT NULL    DEFAULT SYSUTCDATETIME(),
    priv_modified_on            DATETIMEOFFSET(7)   NOT NULL    DEFAULT SYSUTCDATETIME(),
    CONSTRAINT FK_sorf_subdomain FOREIGN KEY (ref_subdomain_guid) REFERENCES system_objects_rpc_subdomains(key_guid),
    CONSTRAINT FK_sorf_method FOREIGN KEY (ref_method_guid) REFERENCES system_objects_module_methods(key_guid),
    CONSTRAINT FK_sorf_role FOREIGN KEY (ref_required_role_guid) REFERENCES system_auth_roles(key_guid),
    CONSTRAINT FK_sorf_entitlement FOREIGN KEY (ref_required_entitlement_guid) REFERENCES system_auth_entitlements(key_guid),
    CONSTRAINT UQ_sorf_subdomain_name_version UNIQUE (ref_subdomain_guid, pub_name, pub_version)
);
CREATE INDEX IX_sorf_subdomain ON system_objects_rpc_functions (ref_subdomain_guid);
CREATE INDEX IX_sorf_method ON system_objects_rpc_functions (ref_method_guid);

-- =============================================================
-- PHASE 4: Page system
-- =============================================================

-- Table 8: system_objects_pages
CREATE TABLE system_objects_pages (
    key_guid                    UNIQUEIDENTIFIER    NOT NULL    PRIMARY KEY,
    pub_slug                    NVARCHAR(256)       NOT NULL    UNIQUE,
    pub_title                   NVARCHAR(256)       NULL,
    pub_description             NVARCHAR(512)       NULL,
    pub_icon                    NVARCHAR(64)        NULL,
    ref_root_component_guid     UNIQUEIDENTIFIER    NULL,
    ref_required_role_guid      UNIQUEIDENTIFIER    NULL,
    ref_required_entitlement_guid UNIQUEIDENTIFIER  NULL,
    priv_created_on             DATETIMEOFFSET(7)   NOT NULL    DEFAULT SYSUTCDATETIME(),
    priv_modified_on            DATETIMEOFFSET(7)   NOT NULL    DEFAULT SYSUTCDATETIME(),
    CONSTRAINT FK_sop_root_component FOREIGN KEY (ref_root_component_guid) REFERENCES system_objects_component_tree(key_guid),
    CONSTRAINT FK_sop_role FOREIGN KEY (ref_required_role_guid) REFERENCES system_auth_roles(key_guid),
    CONSTRAINT FK_sop_entitlement FOREIGN KEY (ref_required_entitlement_guid) REFERENCES system_auth_entitlements(key_guid)
);

-- Table 9: system_objects_page_data_bindings
CREATE TABLE system_objects_page_data_bindings (
    key_guid                    UNIQUEIDENTIFIER    NOT NULL    PRIMARY KEY,
    ref_page_guid               UNIQUEIDENTIFIER    NOT NULL,
    ref_component_node_guid     UNIQUEIDENTIFIER    NOT NULL,
    ref_column_guid             UNIQUEIDENTIFIER    NULL,
    pub_source_type             NVARCHAR(32)        NOT NULL    DEFAULT 'column',
    pub_literal_value           NVARCHAR(1024)      NULL,
    pub_config_key              NVARCHAR(256)       NULL,
    pub_alias                   NVARCHAR(128)       NULL,
    priv_created_on             DATETIMEOFFSET(7)   NOT NULL    DEFAULT SYSUTCDATETIME(),
    priv_modified_on            DATETIMEOFFSET(7)   NOT NULL    DEFAULT SYSUTCDATETIME(),
    CONSTRAINT FK_sopdb_page FOREIGN KEY (ref_page_guid) REFERENCES system_objects_pages(key_guid),
    CONSTRAINT FK_sopdb_component_node FOREIGN KEY (ref_component_node_guid) REFERENCES system_objects_component_tree(key_guid),
    CONSTRAINT FK_sopdb_column FOREIGN KEY (ref_column_guid) REFERENCES system_objects_database_columns(key_guid),
    CONSTRAINT UQ_sopdb_page_node UNIQUE (ref_page_guid, ref_component_node_guid)
);
CREATE INDEX IX_sopdb_page ON system_objects_page_data_bindings (ref_page_guid);
CREATE INDEX IX_sopdb_column ON system_objects_page_data_bindings (ref_column_guid);

-- =============================================================
-- PHASE 5: Alter existing tables
-- =============================================================

-- Add page ownership + security to component_tree
ALTER TABLE system_objects_component_tree
    ADD ref_page_guid                 UNIQUEIDENTIFIER NULL,
        ref_required_role_guid        UNIQUEIDENTIFIER NULL,
        ref_required_entitlement_guid UNIQUEIDENTIFIER NULL;

ALTER TABLE system_objects_component_tree
    ADD CONSTRAINT FK_soct_page FOREIGN KEY (ref_page_guid)
            REFERENCES system_objects_pages(key_guid),
        CONSTRAINT FK_soct_role FOREIGN KEY (ref_required_role_guid)
            REFERENCES system_auth_roles(key_guid),
        CONSTRAINT FK_soct_entitlement FOREIGN KEY (ref_required_entitlement_guid)
            REFERENCES system_auth_entitlements(key_guid);

-- Add page reference to routes
ALTER TABLE system_objects_routes
    ADD ref_page_guid UNIQUEIDENTIFIER NULL;

ALTER TABLE system_objects_routes
    ADD CONSTRAINT FK_sor_page FOREIGN KEY (ref_page_guid)
            REFERENCES system_objects_pages(key_guid);

-- =============================================================
-- PHASE 6: Seed data
-- =============================================================

-- 6a: Server modules (15 rows)
INSERT INTO system_objects_modules (key_guid, pub_name, pub_state_attr, pub_module_path)
VALUES ('CF85FB11-5981-56B7-8E43-9D453E611D43', 'CmsWorkbenchModule', 'cms_workbench', 'server.modules.cms_workbench_module');
INSERT INTO system_objects_modules (key_guid, pub_name, pub_state_attr, pub_module_path)
VALUES ('95C9AEA9-6EA8-5CCE-A1AF-A210B7B9A72D', 'AuthModule', 'auth', 'server.modules.auth_module');
INSERT INTO system_objects_modules (key_guid, pub_name, pub_state_attr, pub_module_path)
VALUES ('EF624C02-1277-50E7-8CC5-7D41E92707CE', 'SystemConfigModule', 'system_config', 'server.modules.system_config_module');
INSERT INTO system_objects_modules (key_guid, pub_name, pub_state_attr, pub_module_path)
VALUES ('02982339-7CAA-5581-AC3C-1E0454FFB6FF', 'RoleModule', 'role', 'server.modules.role_module');
INSERT INTO system_objects_modules (key_guid, pub_name, pub_state_attr, pub_module_path)
VALUES ('6D818DCB-5B60-5B80-91F1-A1D19DC03110', 'SessionModule', 'session', 'server.modules.session_module');
INSERT INTO system_objects_modules (key_guid, pub_name, pub_state_attr, pub_module_path)
VALUES ('ACE1F6E5-9E84-51CB-B595-FA02C7D46CE9', 'OauthModule', 'oauth', 'server.modules.oauth_module');
INSERT INTO system_objects_modules (key_guid, pub_name, pub_state_attr, pub_module_path)
VALUES ('F13CB430-FA45-5BF2-BA53-B589FD00FD8A', 'RpcdispatchModule', 'rpcdispatch', 'server.modules.rpcdispatch_module');
INSERT INTO system_objects_modules (key_guid, pub_name, pub_state_attr, pub_module_path)
VALUES ('73754733-5650-5469-A391-9A89B5581CA2', 'ServiceRoutesModule', 'service_routes', 'server.modules.service_routes_module');
INSERT INTO system_objects_modules (key_guid, pub_name, pub_state_attr, pub_module_path)
VALUES ('48B0A9CD-EDC3-5823-81AA-75C25152C667', 'PublicLinksModule', 'public_links', 'server.modules.public_links_module');
INSERT INTO system_objects_modules (key_guid, pub_name, pub_state_attr, pub_module_path)
VALUES ('19CA2779-FAF9-501B-94D9-09D718D141EF', 'PublicVarsModule', 'public_vars', 'server.modules.public_vars_module');
INSERT INTO system_objects_modules (key_guid, pub_name, pub_state_attr, pub_module_path)
VALUES ('029B2026-89CE-5376-8E5A-92D9967B2A32', 'DiscordBotModule', 'discord_bot', 'server.modules.discord_bot_module');
INSERT INTO system_objects_modules (key_guid, pub_name, pub_state_attr, pub_module_path)
VALUES ('217B5C5E-BA81-5EEA-92A4-563E56F7B40B', 'McpGatewayModule', 'mcp_gateway', 'server.modules.mcp_gateway_module');
INSERT INTO system_objects_modules (key_guid, pub_name, pub_state_attr, pub_module_path)
VALUES ('088468A2-A5C4-580F-910B-2B2F640316D3', 'DbModule', 'db', 'server.modules.db_module');
INSERT INTO system_objects_modules (key_guid, pub_name, pub_state_attr, pub_module_path)
VALUES ('059F2419-E249-5CD9-BCA2-0FCC7CD7CF7E', 'EnvModule', 'env', 'server.modules.env_module');
INSERT INTO system_objects_modules (key_guid, pub_name, pub_state_attr, pub_module_path)
VALUES ('1622E106-6FB7-5FA8-9460-A4D0AF1C7ACD', 'DatabaseCliModule', 'database_cli', 'server.modules.database_cli_module');

-- 6b: RPC models (6 rows)
INSERT INTO system_objects_rpc_models (key_guid, pub_name, pub_version)
VALUES ('BD4DCBED-A062-5987-BD60-167908B68EAE', 'LoadShellResult1', 1);
INSERT INTO system_objects_rpc_models (key_guid, pub_name, pub_version)
VALUES ('0403ADBF-AEE4-5391-B87A-5E26EFA501D5', 'LoadPageParams1', 1);
INSERT INTO system_objects_rpc_models (key_guid, pub_name, pub_version)
VALUES ('BA9D602B-7A6F-5374-848A-4CCF5611E54B', 'LoadPageResult1', 1);
INSERT INTO system_objects_rpc_models (key_guid, pub_name, pub_version)
VALUES ('8B2F86FB-9236-50A1-89B0-BF75CDE2CDE4', 'PathNode1', 1);
INSERT INTO system_objects_rpc_models (key_guid, pub_name, pub_version)
VALUES ('8CC28238-0F62-5C32-8FF9-23F0A5525946', 'ReadNavigationResult1', 1);
INSERT INTO system_objects_rpc_models (key_guid, pub_name, pub_version)
VALUES ('6C1B8A0C-F1F0-5C89-AEE4-6E178706EBD8', 'NavigationRouteElement1', 1);

-- 6c: RPC model fields (17 rows)
-- LoadShellResult1.shellData
INSERT INTO system_objects_rpc_model_fields (key_guid, ref_model_guid, pub_name, pub_ordinal, ref_type_guid, ref_nested_model_guid, pub_is_nullable, pub_is_list)
VALUES ('FD87CBC4-B773-5193-8FF9-ACEA1DE423D8', 'BD4DCBED-A062-5987-BD60-167908B68EAE', 'shellData', 0, NULL, '8B2F86FB-9236-50A1-89B0-BF75CDE2CDE4', 0, 0);
-- LoadPageParams1.path
INSERT INTO system_objects_rpc_model_fields (key_guid, ref_model_guid, pub_name, pub_ordinal, ref_type_guid, ref_nested_model_guid, pub_is_nullable, pub_is_list)
VALUES ('9C230CE9-6DDB-54BD-A05E-F7DC868BC458', '0403ADBF-AEE4-5391-B87A-5E26EFA501D5', 'path', 1, '0093B404-1EEE-563D-9135-4B9E7EECA7A2', NULL, 0, 0);
-- LoadPageResult1.pathData
INSERT INTO system_objects_rpc_model_fields (key_guid, ref_model_guid, pub_name, pub_ordinal, ref_type_guid, ref_nested_model_guid, pub_is_nullable, pub_is_list)
VALUES ('C4434DBA-5DA8-5CB8-BF29-186A7ADDBE64', 'BA9D602B-7A6F-5374-848A-4CCF5611E54B', 'pathData', 2, NULL, '8B2F86FB-9236-50A1-89B0-BF75CDE2CDE4', 0, 0);
-- LoadPageResult1.componentData
INSERT INTO system_objects_rpc_model_fields (key_guid, ref_model_guid, pub_name, pub_ordinal, ref_type_guid, ref_nested_model_guid, pub_is_nullable, pub_is_list)
VALUES ('9E21DBBD-E945-50A2-84BC-B09192E69BD3', 'BA9D602B-7A6F-5374-848A-4CCF5611E54B', 'componentData', 3, NULL, NULL, 1, 0);
-- PathNode1.guid
INSERT INTO system_objects_rpc_model_fields (key_guid, ref_model_guid, pub_name, pub_ordinal, ref_type_guid, ref_nested_model_guid, pub_is_nullable, pub_is_list)
VALUES ('22CBC9D0-9D1D-5A2E-8FAC-457ED6FE862F', '8B2F86FB-9236-50A1-89B0-BF75CDE2CDE4', 'guid', 4, '4D2EB10B-363E-5AF4-826A-9294146244E4', NULL, 0, 0);
-- PathNode1.component
INSERT INTO system_objects_rpc_model_fields (key_guid, ref_model_guid, pub_name, pub_ordinal, ref_type_guid, ref_nested_model_guid, pub_is_nullable, pub_is_list)
VALUES ('AE036A96-C415-5910-80AA-A3FF3D74C479', '8B2F86FB-9236-50A1-89B0-BF75CDE2CDE4', 'component', 5, '0093B404-1EEE-563D-9135-4B9E7EECA7A2', NULL, 0, 0);
-- PathNode1.category
INSERT INTO system_objects_rpc_model_fields (key_guid, ref_model_guid, pub_name, pub_ordinal, ref_type_guid, ref_nested_model_guid, pub_is_nullable, pub_is_list)
VALUES ('58FA0177-ED6A-5AC1-B218-3D25C35BCFAB', '8B2F86FB-9236-50A1-89B0-BF75CDE2CDE4', 'category', 6, '0093B404-1EEE-563D-9135-4B9E7EECA7A2', NULL, 0, 0);
-- PathNode1.label
INSERT INTO system_objects_rpc_model_fields (key_guid, ref_model_guid, pub_name, pub_ordinal, ref_type_guid, ref_nested_model_guid, pub_is_nullable, pub_is_list)
VALUES ('65D2E5BE-214D-5283-BF79-869A3714A64B', '8B2F86FB-9236-50A1-89B0-BF75CDE2CDE4', 'label', 7, '0093B404-1EEE-563D-9135-4B9E7EECA7A2', NULL, 1, 0);
-- PathNode1.fieldBinding
INSERT INTO system_objects_rpc_model_fields (key_guid, ref_model_guid, pub_name, pub_ordinal, ref_type_guid, ref_nested_model_guid, pub_is_nullable, pub_is_list)
VALUES ('7C0BFFE4-5642-524C-98AF-1DC10FE9A1D6', '8B2F86FB-9236-50A1-89B0-BF75CDE2CDE4', 'fieldBinding', 8, '0093B404-1EEE-563D-9135-4B9E7EECA7A2', NULL, 1, 0);
-- PathNode1.sequence
INSERT INTO system_objects_rpc_model_fields (key_guid, ref_model_guid, pub_name, pub_ordinal, ref_type_guid, ref_nested_model_guid, pub_is_nullable, pub_is_list)
VALUES ('536C1F70-BA70-5755-88F7-6D1524F80627', '8B2F86FB-9236-50A1-89B0-BF75CDE2CDE4', 'sequence', 9, 'E3EDE0CE-2A03-501E-A796-3487BEA03B7B', NULL, 0, 0);
-- PathNode1.children
INSERT INTO system_objects_rpc_model_fields (key_guid, ref_model_guid, pub_name, pub_ordinal, ref_type_guid, ref_nested_model_guid, pub_is_nullable, pub_is_list)
VALUES ('713C2BE8-4A63-5CA6-B2D1-E7DDF0FFFC82', '8B2F86FB-9236-50A1-89B0-BF75CDE2CDE4', 'children', 10, NULL, '8B2F86FB-9236-50A1-89B0-BF75CDE2CDE4', 0, 1);
-- ReadNavigationResult1.elements
INSERT INTO system_objects_rpc_model_fields (key_guid, ref_model_guid, pub_name, pub_ordinal, ref_type_guid, ref_nested_model_guid, pub_is_nullable, pub_is_list)
VALUES ('3D1984FC-5E18-5C91-A14C-F20832E1CC23', '8CC28238-0F62-5C32-8FF9-23F0A5525946', 'elements', 11, NULL, '6C1B8A0C-F1F0-5C89-AEE4-6E178706EBD8', 0, 1);
-- NavigationRouteElement1.path
INSERT INTO system_objects_rpc_model_fields (key_guid, ref_model_guid, pub_name, pub_ordinal, ref_type_guid, ref_nested_model_guid, pub_is_nullable, pub_is_list)
VALUES ('A3756A90-4A53-53C9-860B-F1838C683AA9', '6C1B8A0C-F1F0-5C89-AEE4-6E178706EBD8', 'path', 12, '0093B404-1EEE-563D-9135-4B9E7EECA7A2', NULL, 0, 0);
-- NavigationRouteElement1.title
INSERT INTO system_objects_rpc_model_fields (key_guid, ref_model_guid, pub_name, pub_ordinal, ref_type_guid, ref_nested_model_guid, pub_is_nullable, pub_is_list)
VALUES ('49DCC39A-CA6F-55C4-A087-EAEB261DE77A', '6C1B8A0C-F1F0-5C89-AEE4-6E178706EBD8', 'title', 13, '0093B404-1EEE-563D-9135-4B9E7EECA7A2', NULL, 0, 0);
-- NavigationRouteElement1.icon
INSERT INTO system_objects_rpc_model_fields (key_guid, ref_model_guid, pub_name, pub_ordinal, ref_type_guid, ref_nested_model_guid, pub_is_nullable, pub_is_list)
VALUES ('9B2D4264-BE1B-5BE1-B8C7-7F2E114CC279', '6C1B8A0C-F1F0-5C89-AEE4-6E178706EBD8', 'icon', 14, '0093B404-1EEE-563D-9135-4B9E7EECA7A2', NULL, 1, 0);
-- NavigationRouteElement1.sequence
INSERT INTO system_objects_rpc_model_fields (key_guid, ref_model_guid, pub_name, pub_ordinal, ref_type_guid, ref_nested_model_guid, pub_is_nullable, pub_is_list)
VALUES ('B835966E-92F1-5ECE-9248-B3627C552A3D', '6C1B8A0C-F1F0-5C89-AEE4-6E178706EBD8', 'sequence', 15, 'E3EDE0CE-2A03-501E-A796-3487BEA03B7B', NULL, 0, 0);
-- NavigationRouteElement1.children
INSERT INTO system_objects_rpc_model_fields (key_guid, ref_model_guid, pub_name, pub_ordinal, ref_type_guid, ref_nested_model_guid, pub_is_nullable, pub_is_list)
VALUES ('E99C1B38-B06D-5D09-8695-31D5656CEE26', '6C1B8A0C-F1F0-5C89-AEE4-6E178706EBD8', 'children', 16, NULL, '6C1B8A0C-F1F0-5C89-AEE4-6E178706EBD8', 0, 1);

-- 6d: Module methods (8 rows)
INSERT INTO system_objects_module_methods (key_guid, ref_module_guid, pub_name, ref_request_model_guid, ref_response_model_guid)
VALUES ('4427A371-81DF-57C4-A16C-E03008BA1AB9', 'CF85FB11-5981-56B7-8E43-9D453E611D43', 'load_shell', NULL, 'BD4DCBED-A062-5987-BD60-167908B68EAE');
INSERT INTO system_objects_module_methods (key_guid, ref_module_guid, pub_name, ref_request_model_guid, ref_response_model_guid)
VALUES ('D207AE62-AF24-514D-A7C5-FBEC5200DC24', 'CF85FB11-5981-56B7-8E43-9D453E611D43', 'load_page', '0403ADBF-AEE4-5391-B87A-5E26EFA501D5', 'BA9D602B-7A6F-5374-848A-4CCF5611E54B');
INSERT INTO system_objects_module_methods (key_guid, ref_module_guid, pub_name, ref_request_model_guid, ref_response_model_guid)
VALUES ('88EB34E5-DBF0-5254-AEE4-D61D18ACCF8F', 'CF85FB11-5981-56B7-8E43-9D453E611D43', 'read_navigation', NULL, '8CC28238-0F62-5C32-8FF9-23F0A5525946');
INSERT INTO system_objects_module_methods (key_guid, ref_module_guid, pub_name, ref_request_model_guid, ref_response_model_guid)
VALUES ('2D3B31B8-62EB-5CBB-A15C-C3FB19A975F6', '95C9AEA9-6EA8-5CCE-A1AF-A210B7B9A72D', 'get_auth_state', NULL, NULL);
INSERT INTO system_objects_module_methods (key_guid, ref_module_guid, pub_name, ref_request_model_guid, ref_response_model_guid)
VALUES ('5C9020C1-BA56-5898-A271-E0B62E00BC99', '95C9AEA9-6EA8-5CCE-A1AF-A210B7B9A72D', 'read_current_user', NULL, NULL);
INSERT INTO system_objects_module_methods (key_guid, ref_module_guid, pub_name, ref_request_model_guid, ref_response_model_guid)
VALUES ('79EF9D0C-D111-555C-A77E-1C39A01E076C', 'EF624C02-1277-50E7-8CC5-7D41E92707CE', 'get_configs', NULL, NULL);
INSERT INTO system_objects_module_methods (key_guid, ref_module_guid, pub_name, ref_request_model_guid, ref_response_model_guid)
VALUES ('573886C1-F179-5EB4-8C16-7B410041E73B', 'EF624C02-1277-50E7-8CC5-7D41E92707CE', 'upsert_config', NULL, NULL);
INSERT INTO system_objects_module_methods (key_guid, ref_module_guid, pub_name, ref_request_model_guid, ref_response_model_guid)
VALUES ('EAE41724-3FCB-5EA6-8E5B-8F23A55B96D6', 'EF624C02-1277-50E7-8CC5-7D41E92707CE', 'delete_config', NULL, NULL);

-- 6e: RPC domains (3 rows)
INSERT INTO system_objects_rpc_domains (key_guid, pub_name, ref_required_role_guid)
VALUES ('E5487180-28BD-5381-84EF-58A153F7999A', 'public', NULL);
INSERT INTO system_objects_rpc_domains (key_guid, pub_name, ref_required_role_guid)
VALUES ('B90B0747-38A7-54B4-8BE5-963D962BA93A', 'system', '20F0C823-4742-51BE-938B-7AA5B9D36B81');
INSERT INTO system_objects_rpc_domains (key_guid, pub_name, ref_required_role_guid)
VALUES ('DBC16219-905A-58C8-8F69-3EFFF6E0424A', 'service', 'E8E1A4CC-0898-59F4-8B03-B2C9804516C0');

-- 6f: RPC subdomains (10 rows)
INSERT INTO system_objects_rpc_subdomains (key_guid, pub_name, ref_domain_guid, ref_required_entitlement_guid)
VALUES ('3D0C1FC1-FB23-524E-8750-24C4CDAC1845', 'route', 'E5487180-28BD-5381-84EF-58A153F7999A', NULL);
INSERT INTO system_objects_rpc_subdomains (key_guid, pub_name, ref_domain_guid, ref_required_entitlement_guid)
VALUES ('A894CC9F-0D19-59C4-9624-F3942785AB95', 'auth', 'E5487180-28BD-5381-84EF-58A153F7999A', NULL);
INSERT INTO system_objects_rpc_subdomains (key_guid, pub_name, ref_domain_guid, ref_required_entitlement_guid)
VALUES ('0E7C6D9E-935D-58FA-B7BC-654968051C12', 'links', 'E5487180-28BD-5381-84EF-58A153F7999A', NULL);
INSERT INTO system_objects_rpc_subdomains (key_guid, pub_name, ref_domain_guid, ref_required_entitlement_guid)
VALUES ('50021D5A-0B7A-5529-B3C7-9D35D23FFAD1', 'config', 'B90B0747-38A7-54B4-8BE5-963D962BA93A', NULL);
INSERT INTO system_objects_rpc_subdomains (key_guid, pub_name, ref_domain_guid, ref_required_entitlement_guid)
VALUES ('8E26A0A1-B15A-5236-B08E-5E2F9A9BA9A0', 'users', 'B90B0747-38A7-54B4-8BE5-963D962BA93A', NULL);
INSERT INTO system_objects_rpc_subdomains (key_guid, pub_name, ref_domain_guid, ref_required_entitlement_guid)
VALUES ('1212949E-27FC-524E-80BB-FB936F711017', 'discord', 'B90B0747-38A7-54B4-8BE5-963D962BA93A', 'C1B7B7E2-851D-5EFA-A837-D9E4DD2B179A');
INSERT INTO system_objects_rpc_subdomains (key_guid, pub_name, ref_domain_guid, ref_required_entitlement_guid)
VALUES ('3DB4CC67-C121-50C3-ACA6-5F17F479DDEA', 'models', 'B90B0747-38A7-54B4-8BE5-963D962BA93A', NULL);
INSERT INTO system_objects_rpc_subdomains (key_guid, pub_name, ref_domain_guid, ref_required_entitlement_guid)
VALUES ('E00E13AA-5F82-5ED7-B03A-933D2D05F616', 'conversations', 'B90B0747-38A7-54B4-8BE5-963D962BA93A', NULL);
INSERT INTO system_objects_rpc_subdomains (key_guid, pub_name, ref_domain_guid, ref_required_entitlement_guid)
VALUES ('A33A3361-D7D6-556B-8098-2FE0482229D2', 'management', 'DBC16219-905A-58C8-8F69-3EFFF6E0424A', NULL);
INSERT INTO system_objects_rpc_subdomains (key_guid, pub_name, ref_domain_guid, ref_required_entitlement_guid)
VALUES ('7E778B2B-0DD6-5B35-B504-B6F8DB4D6362', 'schema', 'DBC16219-905A-58C8-8F69-3EFFF6E0424A', NULL);

-- 6g: RPC functions (8 rows)
-- urn:public:route:load_shell:1
INSERT INTO system_objects_rpc_functions (key_guid, pub_name, pub_version, ref_subdomain_guid, ref_method_guid)
VALUES ('4D5FA3D6-B6F9-532D-9F7A-C54E1F8DBE09', 'load_shell', 1, '3D0C1FC1-FB23-524E-8750-24C4CDAC1845', '4427A371-81DF-57C4-A16C-E03008BA1AB9');
-- urn:public:route:load_page:1
INSERT INTO system_objects_rpc_functions (key_guid, pub_name, pub_version, ref_subdomain_guid, ref_method_guid)
VALUES ('4979EB91-4F87-5740-B027-309F80A3358E', 'load_page', 1, '3D0C1FC1-FB23-524E-8750-24C4CDAC1845', 'D207AE62-AF24-514D-A7C5-FBEC5200DC24');
-- urn:public:route:read_navigation:1
INSERT INTO system_objects_rpc_functions (key_guid, pub_name, pub_version, ref_subdomain_guid, ref_method_guid)
VALUES ('24B4A4C7-CF6F-51BB-A373-FD9B22AD9AE6', 'read_navigation', 1, '3D0C1FC1-FB23-524E-8750-24C4CDAC1845', '88EB34E5-DBF0-5254-AEE4-D61D18ACCF8F');
-- urn:public:auth:get_auth_state:1
INSERT INTO system_objects_rpc_functions (key_guid, pub_name, pub_version, ref_subdomain_guid, ref_method_guid)
VALUES ('EA2DF078-1AB4-56F4-AE7D-07CD7642D831', 'get_auth_state', 1, 'A894CC9F-0D19-59C4-9624-F3942785AB95', '2D3B31B8-62EB-5CBB-A15C-C3FB19A975F6');
-- urn:public:auth:read_current_user:1
INSERT INTO system_objects_rpc_functions (key_guid, pub_name, pub_version, ref_subdomain_guid, ref_method_guid)
VALUES ('F7A31343-79FB-53E1-8C85-A7BBFF509782', 'read_current_user', 1, 'A894CC9F-0D19-59C4-9624-F3942785AB95', '5C9020C1-BA56-5898-A271-E0B62E00BC99');
-- urn:system:config:read_config:1
INSERT INTO system_objects_rpc_functions (key_guid, pub_name, pub_version, ref_subdomain_guid, ref_method_guid)
VALUES ('22E4AAD9-B6EE-5385-BB43-8586BF76F8C6', 'read_config', 1, '50021D5A-0B7A-5529-B3C7-9D35D23FFAD1', '79EF9D0C-D111-555C-A77E-1C39A01E076C');
-- urn:system:config:upsert_config:1
INSERT INTO system_objects_rpc_functions (key_guid, pub_name, pub_version, ref_subdomain_guid, ref_method_guid)
VALUES ('89FA69C0-4F09-51A5-88AE-D146065432E3', 'upsert_config', 1, '50021D5A-0B7A-5529-B3C7-9D35D23FFAD1', '573886C1-F179-5EB4-8C16-7B410041E73B');
-- urn:system:config:delete_config:1
INSERT INTO system_objects_rpc_functions (key_guid, pub_name, pub_version, ref_subdomain_guid, ref_method_guid)
VALUES ('A8A422CF-B509-5B0B-BE54-C84C4CC16997', 'delete_config', 1, '50021D5A-0B7A-5529-B3C7-9D35D23FFAD1', 'EAE41724-3FCB-5EA6-8E5B-8F23A55B96D6');

-- 6h: New components (4 rows)
INSERT INTO system_objects_components (key_guid, pub_name, pub_category, pub_description, ref_default_type_guid)
VALUES ('B501C466-0ADD-5BCF-9BBB-8B7607DDBBEC', 'SimplePage', 'page', 'Simple static page with centered content.', NULL);
INSERT INTO system_objects_components (key_guid, pub_name, pub_category, pub_description, ref_default_type_guid)
VALUES ('5359AE9B-C76E-532E-8F0D-03EAC0C6072B', 'ImageElement', 'control', 'Renders a static image. fieldBinding = image source.', '0093B404-1EEE-563D-9135-4B9E7EECA7A2');
INSERT INTO system_objects_components (key_guid, pub_name, pub_category, pub_description, ref_default_type_guid)
VALUES ('62B142DE-9DD8-567A-844E-6E1CF63FC958', 'LinkButton', 'control', 'Clickable button link. pub_label = text, fieldBinding = URL.', '0093B404-1EEE-563D-9135-4B9E7EECA7A2');
INSERT INTO system_objects_components (key_guid, pub_name, pub_category, pub_description, ref_default_type_guid)
VALUES ('E2D54B31-291F-586B-98E6-BAC7DCE58C2A', 'LabelElement', 'control', 'Simple text label. Falls back to pub_label if no fieldBinding.', '0093B404-1EEE-563D-9135-4B9E7EECA7A2');


---- GO TO ALTERNATE SCRIPT AT BOTTOM, continue back on 6k


-- 6i: HomePage component tree (7 rows, standalone root)
-- tree:HomePage
INSERT INTO system_objects_component_tree (key_guid, ref_parent_guid, ref_component_guid, ref_type_guid, pub_label, pub_field_binding, pub_sequence, pub_rpc_operation, pub_rpc_contract, pub_mutation_operation, pub_is_default_editable, ref_page_guid)
VALUES ('54CDA54E-ED20-5249-87CE-43B19D96B39A', NULL, 'B501C466-0ADD-5BCF-9BBB-8B7607DDBBEC', NULL, NULL, NULL, 0, NULL, NULL, NULL, 0, 'C75ECC15-B5ED-59A8-AC10-C17242F9F038');
-- tree:HomePage.ImageElement:banner
INSERT INTO system_objects_component_tree (key_guid, ref_parent_guid, ref_component_guid, ref_type_guid, pub_label, pub_field_binding, pub_sequence, pub_rpc_operation, pub_rpc_contract, pub_mutation_operation, pub_is_default_editable, ref_page_guid)
VALUES ('31219EA9-A5D7-5D9D-A449-B1A743165A84', '54CDA54E-ED20-5249-87CE-43B19D96B39A', '5359AE9B-C76E-532E-8F0D-03EAC0C6072B', NULL, 'The Elideus Group', 'banner_image', 1, NULL, NULL, NULL, 0, 'C75ECC15-B5ED-59A8-AC10-C17242F9F038');
-- tree:HomePage.LinkButton:products
INSERT INTO system_objects_component_tree (key_guid, ref_parent_guid, ref_component_guid, ref_type_guid, pub_label, pub_field_binding, pub_sequence, pub_rpc_operation, pub_rpc_contract, pub_mutation_operation, pub_is_default_editable, ref_page_guid)
VALUES ('181FCFC1-E9CC-5AE7-98B0-AD46DB0BBB2B', '54CDA54E-ED20-5249-87CE-43B19D96B39A', '62B142DE-9DD8-567A-844E-6E1CF63FC958', NULL, 'Products', 'link_products', 2, NULL, NULL, NULL, 0, 'C75ECC15-B5ED-59A8-AC10-C17242F9F038');
-- tree:HomePage.LinkButton:gallery
INSERT INTO system_objects_component_tree (key_guid, ref_parent_guid, ref_component_guid, ref_type_guid, pub_label, pub_field_binding, pub_sequence, pub_rpc_operation, pub_rpc_contract, pub_mutation_operation, pub_is_default_editable, ref_page_guid)
VALUES ('62DEF194-3BF5-5368-877C-C5FC11C1B5DE', '54CDA54E-ED20-5249-87CE-43B19D96B39A', '62B142DE-9DD8-567A-844E-6E1CF63FC958', NULL, 'Gallery', 'link_gallery', 3, NULL, NULL, NULL, 0, 'C75ECC15-B5ED-59A8-AC10-C17242F9F038');
-- tree:HomePage.LinkButton:github
INSERT INTO system_objects_component_tree (key_guid, ref_parent_guid, ref_component_guid, ref_type_guid, pub_label, pub_field_binding, pub_sequence, pub_rpc_operation, pub_rpc_contract, pub_mutation_operation, pub_is_default_editable, ref_page_guid)
VALUES ('24F9CDE8-3C22-56D3-BFBF-1BB43D30BA2A', '54CDA54E-ED20-5249-87CE-43B19D96B39A', '62B142DE-9DD8-567A-844E-6E1CF63FC958', NULL, 'GitHub', 'link_github', 4, NULL, NULL, NULL, 0, 'C75ECC15-B5ED-59A8-AC10-C17242F9F038');
-- tree:HomePage.LinkButton:linkedin
INSERT INTO system_objects_component_tree (key_guid, ref_parent_guid, ref_component_guid, ref_type_guid, pub_label, pub_field_binding, pub_sequence, pub_rpc_operation, pub_rpc_contract, pub_mutation_operation, pub_is_default_editable, ref_page_guid)
VALUES ('EB6297D3-3D54-5004-881D-6A8DDE569AAE', '54CDA54E-ED20-5249-87CE-43B19D96B39A', '62B142DE-9DD8-567A-844E-6E1CF63FC958', NULL, 'LinkedIn', 'link_linkedin', 5, NULL, NULL, NULL, 0, 'C75ECC15-B5ED-59A8-AC10-C17242F9F038');
-- tree:HomePage.LabelElement:copyright
INSERT INTO system_objects_component_tree (key_guid, ref_parent_guid, ref_component_guid, ref_type_guid, pub_label, pub_field_binding, pub_sequence, pub_rpc_operation, pub_rpc_contract, pub_mutation_operation, pub_is_default_editable, ref_page_guid)
VALUES ('7C2CEC0E-9221-57C3-8217-FA5AB36AC814', '54CDA54E-ED20-5249-87CE-43B19D96B39A', 'E2D54B31-291F-586B-98E6-BAC7DCE58C2A', NULL, N'\u00a9 2026 The Elideus Group', NULL, 6, NULL, NULL, NULL, 0, 'C75ECC15-B5ED-59A8-AC10-C17242F9F038');

-- 6j: Pages (2 rows)
INSERT INTO system_objects_pages (key_guid, pub_slug, pub_title, pub_icon, ref_root_component_guid)
VALUES ('C75ECC15-B5ED-59A8-AC10-C17242F9F038', 'home', 'Home', 'Home', '54CDA54E-ED20-5249-87CE-43B19D96B39A');

INSERT INTO system_objects_pages (key_guid, pub_slug, pub_title, pub_icon)
VALUES ('EAB31881-7A0B-5247-950C-52A3C15E31D9', 'navigation_panel', 'Navigation', NULL);



---- Come back to here after seed correction below



-- 6k: HomePage data bindings (6 rows, all literal)
INSERT INTO system_objects_page_data_bindings (key_guid, ref_page_guid, ref_component_node_guid, pub_source_type, pub_literal_value, pub_alias)
VALUES ('90E24926-A61C-5738-A8C5-5B69AB5C1984', 'C75ECC15-B5ED-59A8-AC10-C17242F9F038', '31219EA9-A5D7-5D9D-A449-B1A743165A84', 'literal', N'/assets/elideus_group_green.png', 'banner_image');
INSERT INTO system_objects_page_data_bindings (key_guid, ref_page_guid, ref_component_node_guid, pub_source_type, pub_literal_value, pub_alias)
VALUES ('5F6CB558-58EB-5D2F-814B-1041E1F685D2', 'C75ECC15-B5ED-59A8-AC10-C17242F9F038', '181FCFC1-E9CC-5AE7-98B0-AD46DB0BBB2B', 'literal', N'/products', 'link_products');
INSERT INTO system_objects_page_data_bindings (key_guid, ref_page_guid, ref_component_node_guid, pub_source_type, pub_literal_value, pub_alias)
VALUES ('C4C3D5A4-964D-549F-9DCD-33D0913E9480', 'C75ECC15-B5ED-59A8-AC10-C17242F9F038', '62DEF194-3BF5-5368-877C-C5FC11C1B5DE', 'literal', N'/gallery', 'link_gallery');
INSERT INTO system_objects_page_data_bindings (key_guid, ref_page_guid, ref_component_node_guid, pub_source_type, pub_literal_value, pub_alias)
VALUES ('110AFBCF-13E7-5238-ACF2-C8152225A84A', 'C75ECC15-B5ED-59A8-AC10-C17242F9F038', '24F9CDE8-3C22-56D3-BFBF-1BB43D30BA2A', 'literal', N'https://github.com/Elideus', 'link_github');
INSERT INTO system_objects_page_data_bindings (key_guid, ref_page_guid, ref_component_node_guid, pub_source_type, pub_literal_value, pub_alias)
VALUES ('F1825FB7-7DAA-5B9C-AAC8-342DFABF308B', 'C75ECC15-B5ED-59A8-AC10-C17242F9F038', 'EB6297D3-3D54-5004-881D-6A8DDE569AAE', 'literal', N'https://www.linkedin.com/company/elideus-group', 'link_linkedin');
INSERT INTO system_objects_page_data_bindings (key_guid, ref_page_guid, ref_component_node_guid, pub_source_type, pub_literal_value, pub_alias)
VALUES ('4DDCE210-0CEB-5534-85F5-B4C500E962A9', 'C75ECC15-B5ED-59A8-AC10-C17242F9F038', '7C2CEC0E-9221-57C3-8217-FA5AB36AC814', 'literal', N'© 2026 The Elideus Group', 'copyright');

-- 6l: Security backfill on existing tree nodes
-- DevModeToggle → ROLE_SERVICE_ADMIN
UPDATE system_objects_component_tree SET ref_required_role_guid = 'E8E1A4CC-0898-59F4-8B03-B2C9804516C0' WHERE key_guid = '96616EDE-0CA6-5188-B2BD-1397927CDD1A';
-- ObjectEditor → ROLE_SERVICE_ADMIN
UPDATE system_objects_component_tree SET ref_required_role_guid = 'E8E1A4CC-0898-59F4-8B03-B2C9804516C0' WHERE key_guid = '3B1C8990-F6F3-5171-A7D3-6EDFF6326C9E';
-- ObjectTreeView → ROLE_SERVICE_ADMIN
UPDATE system_objects_component_tree SET ref_required_role_guid = 'E8E1A4CC-0898-59F4-8B03-B2C9804516C0' WHERE key_guid = '5CACE551-8AC7-530F-A8D1-910248778F7C';

-- 6m: Route '/' → page 'home'
UPDATE system_objects_routes SET ref_page_guid = 'C75ECC15-B5ED-59A8-AC10-C17242F9F038' WHERE pub_path = '/';

UPDATE system_objects_routes SET ref_root_node_guid = '54CDA54E-ED20-5249-87CE-43B19D96B39A' WHERE pub_path = '/';

-- =============================================================
-- PHASE 7: Self-registration in database_tables
-- =============================================================

INSERT INTO system_objects_database_tables (key_guid, pub_name, pub_schema)
VALUES ('D039D8FB-3F95-5A66-B7FB-AB4BA1301FEA', 'system_objects_modules', 'dbo');
INSERT INTO system_objects_database_tables (key_guid, pub_name, pub_schema)
VALUES ('65E5E8F3-7EFF-57F7-B4F9-087C191B7B5E', 'system_objects_module_methods', 'dbo');
INSERT INTO system_objects_database_tables (key_guid, pub_name, pub_schema)
VALUES ('D963B65C-E10E-5E04-9E30-D2220D368998', 'system_objects_rpc_domains', 'dbo');
INSERT INTO system_objects_database_tables (key_guid, pub_name, pub_schema)
VALUES ('DAFD98E7-9E2C-55AC-B2DC-64525EDDEF1A', 'system_objects_rpc_subdomains', 'dbo');
INSERT INTO system_objects_database_tables (key_guid, pub_name, pub_schema)
VALUES ('2FC9F843-AD1A-5042-8BEF-4B176B46CD9E', 'system_objects_rpc_functions', 'dbo');
INSERT INTO system_objects_database_tables (key_guid, pub_name, pub_schema)
VALUES ('1F64750F-DCE9-5AC1-93FE-362AF3A96B94', 'system_objects_rpc_models', 'dbo');
INSERT INTO system_objects_database_tables (key_guid, pub_name, pub_schema)
VALUES ('435807CF-4798-560C-BA94-64DB94B8F259', 'system_objects_rpc_model_fields', 'dbo');
INSERT INTO system_objects_database_tables (key_guid, pub_name, pub_schema)
VALUES ('43C62BE6-0611-52E7-87A2-362240EB61C0', 'system_objects_pages', 'dbo');
INSERT INTO system_objects_database_tables (key_guid, pub_name, pub_schema)
VALUES ('5AB53AB1-B603-558C-9A6B-AC06651C8BDC', 'system_objects_page_data_bindings', 'dbo');

-- =============================================================
-- VERIFICATION
-- =============================================================

-- Module count
SELECT COUNT(*) AS module_count FROM system_objects_modules;

-- RPC namespace hierarchy
SELECT d.pub_name AS domain, s.pub_name AS subdomain, f.pub_name AS function, f.pub_version,
       m.pub_name AS method, mod.pub_state_attr AS module_attr
FROM system_objects_rpc_functions f
JOIN system_objects_rpc_subdomains s ON s.key_guid = f.ref_subdomain_guid
JOIN system_objects_rpc_domains d ON d.key_guid = s.ref_domain_guid
JOIN system_objects_module_methods m ON m.key_guid = f.ref_method_guid
JOIN system_objects_modules mod ON mod.key_guid = m.ref_module_guid
ORDER BY d.pub_name, s.pub_name, f.pub_name;

-- Page definitions
SELECT p.pub_slug, p.pub_title, c.pub_name AS root_component
FROM system_objects_pages p
LEFT JOIN system_objects_component_tree t ON t.key_guid = p.ref_root_component_guid
LEFT JOIN system_objects_components c ON c.key_guid = t.ref_component_guid;

-- HomePage data bindings
SELECT b.pub_alias, b.pub_source_type, b.pub_literal_value
FROM system_objects_page_data_bindings b
JOIN system_objects_pages p ON p.key_guid = b.ref_page_guid
WHERE p.pub_slug = 'home'
ORDER BY b.pub_alias;

-- Security backfill verification
SELECT c.pub_name AS component, r.pub_name AS required_role
FROM system_objects_component_tree t
JOIN system_objects_components c ON c.key_guid = t.ref_component_guid
JOIN system_auth_roles r ON r.key_guid = t.ref_required_role_guid
WHERE t.ref_required_role_guid IS NOT NULL;

-- Component count (should be 25)
SELECT COUNT(*) AS component_count FROM system_objects_components;

-- New table self-registrations
SELECT pub_name FROM system_objects_database_tables WHERE pub_name LIKE 'system_objects_%' ORDER BY pub_name;







-- =============================================================
-- v0.12.5.0 PATCH: Fix circular FK between pages and component_tree
-- =============================================================
-- Problem: component_tree INSERTs referenced ref_page_guid before 
--          the page row existed. Pages reference tree roots, tree
--          nodes reference pages — circular dependency.
--
-- Fix: Insert tree nodes WITHOUT ref_page_guid first, then insert
--      the page, then UPDATE tree nodes with ref_page_guid.
--
-- Run this INSTEAD OF sections 6i + 6j from the original seed.
-- If you've already partially run the original and hit the conflict,
-- first clean up any partial inserts:
-- =============================================================

-- Cleanup: remove any partial tree inserts that may have failed
DELETE FROM system_objects_component_tree WHERE key_guid = '54CDA54E-ED20-5249-87CE-43B19D96B39A';
DELETE FROM system_objects_component_tree WHERE key_guid = '31219EA9-A5D7-5D9D-A449-B1A743165A84';
DELETE FROM system_objects_component_tree WHERE key_guid = '181FCFC1-E9CC-5AE7-98B0-AD46DB0BBB2B';
DELETE FROM system_objects_component_tree WHERE key_guid = '62DEF194-3BF5-5368-877C-C5FC11C1B5DE';
DELETE FROM system_objects_component_tree WHERE key_guid = '24F9CDE8-3C22-56D3-BFBF-1BB43D30BA2A';
DELETE FROM system_objects_component_tree WHERE key_guid = 'EB6297D3-3D54-5004-881D-6A8DDE569AAE';
DELETE FROM system_objects_component_tree WHERE key_guid = '7C2CEC0E-9221-57C3-8217-FA5AB36AC814';

-- Cleanup: remove any partial page inserts
DELETE FROM system_objects_pages WHERE key_guid = 'C75ECC15-B5ED-59A8-AC10-C17242F9F038';
DELETE FROM system_objects_pages WHERE key_guid = 'EAB31881-7A0B-5247-950C-52A3C15E31D9';


-- =============================================================
-- Step 1: Insert tree nodes WITHOUT ref_page_guid
-- =============================================================

-- tree:HomePage (SimplePage root, standalone — no parent)
INSERT INTO system_objects_component_tree
  (key_guid, ref_parent_guid, ref_component_guid, ref_type_guid,
   pub_label, pub_field_binding, pub_sequence,
   pub_rpc_operation, pub_rpc_contract, pub_mutation_operation,
   pub_is_default_editable)
VALUES
  ('54CDA54E-ED20-5249-87CE-43B19D96B39A', NULL,
   'B501C466-0ADD-5BCF-9BBB-8B7607DDBBEC', NULL,
   NULL, NULL, 0, NULL, NULL, NULL, 0);

-- tree:HomePage.ImageElement:banner
INSERT INTO system_objects_component_tree
  (key_guid, ref_parent_guid, ref_component_guid, ref_type_guid,
   pub_label, pub_field_binding, pub_sequence,
   pub_rpc_operation, pub_rpc_contract, pub_mutation_operation,
   pub_is_default_editable)
VALUES
  ('31219EA9-A5D7-5D9D-A449-B1A743165A84',
   '54CDA54E-ED20-5249-87CE-43B19D96B39A',
   '5359AE9B-C76E-532E-8F0D-03EAC0C6072B', NULL,
   'The Elideus Group', 'banner_image', 1, NULL, NULL, NULL, 0);

-- tree:HomePage.LinkButton:products
INSERT INTO system_objects_component_tree
  (key_guid, ref_parent_guid, ref_component_guid, ref_type_guid,
   pub_label, pub_field_binding, pub_sequence,
   pub_rpc_operation, pub_rpc_contract, pub_mutation_operation,
   pub_is_default_editable)
VALUES
  ('181FCFC1-E9CC-5AE7-98B0-AD46DB0BBB2B',
   '54CDA54E-ED20-5249-87CE-43B19D96B39A',
   '62B142DE-9DD8-567A-844E-6E1CF63FC958', NULL,
   'Products', 'link_products', 2, NULL, NULL, NULL, 0);

-- tree:HomePage.LinkButton:gallery
INSERT INTO system_objects_component_tree
  (key_guid, ref_parent_guid, ref_component_guid, ref_type_guid,
   pub_label, pub_field_binding, pub_sequence,
   pub_rpc_operation, pub_rpc_contract, pub_mutation_operation,
   pub_is_default_editable)
VALUES
  ('62DEF194-3BF5-5368-877C-C5FC11C1B5DE',
   '54CDA54E-ED20-5249-87CE-43B19D96B39A',
   '62B142DE-9DD8-567A-844E-6E1CF63FC958', NULL,
   'Gallery', 'link_gallery', 3, NULL, NULL, NULL, 0);

-- tree:HomePage.LinkButton:github
INSERT INTO system_objects_component_tree
  (key_guid, ref_parent_guid, ref_component_guid, ref_type_guid,
   pub_label, pub_field_binding, pub_sequence,
   pub_rpc_operation, pub_rpc_contract, pub_mutation_operation,
   pub_is_default_editable)
VALUES
  ('24F9CDE8-3C22-56D3-BFBF-1BB43D30BA2A',
   '54CDA54E-ED20-5249-87CE-43B19D96B39A',
   '62B142DE-9DD8-567A-844E-6E1CF63FC958', NULL,
   'GitHub', 'link_github', 4, NULL, NULL, NULL, 0);

-- tree:HomePage.LinkButton:linkedin
INSERT INTO system_objects_component_tree
  (key_guid, ref_parent_guid, ref_component_guid, ref_type_guid,
   pub_label, pub_field_binding, pub_sequence,
   pub_rpc_operation, pub_rpc_contract, pub_mutation_operation,
   pub_is_default_editable)
VALUES
  ('EB6297D3-3D54-5004-881D-6A8DDE569AAE',
   '54CDA54E-ED20-5249-87CE-43B19D96B39A',
   '62B142DE-9DD8-567A-844E-6E1CF63FC958', NULL,
   'LinkedIn', 'link_linkedin', 5, NULL, NULL, NULL, 0);

-- tree:HomePage.LabelElement:copyright
INSERT INTO system_objects_component_tree
  (key_guid, ref_parent_guid, ref_component_guid, ref_type_guid,
   pub_label, pub_field_binding, pub_sequence,
   pub_rpc_operation, pub_rpc_contract, pub_mutation_operation,
   pub_is_default_editable)
VALUES
  ('7C2CEC0E-9221-57C3-8217-FA5AB36AC814',
   '54CDA54E-ED20-5249-87CE-43B19D96B39A',
   'E2D54B31-291F-586B-98E6-BAC7DCE58C2A', NULL,
   N'© 2026 The Elideus Group', NULL, 6, NULL, NULL, NULL, 0);


-- =============================================================
-- Step 2: Insert pages (tree nodes now exist for ref_root_component_guid)
-- =============================================================

INSERT INTO system_objects_pages
  (key_guid, pub_slug, pub_title, pub_icon, ref_root_component_guid)
VALUES
  ('C75ECC15-B5ED-59A8-AC10-C17242F9F038', 'home', 'Home', 'Home',
   '54CDA54E-ED20-5249-87CE-43B19D96B39A');

INSERT INTO system_objects_pages
  (key_guid, pub_slug, pub_title, pub_icon)
VALUES
  ('EAB31881-7A0B-5247-950C-52A3C15E31D9', 'navigation_panel', 'Navigation', NULL);


-- =============================================================
-- Step 3: Backfill ref_page_guid on HomePage tree nodes
-- =============================================================

UPDATE system_objects_component_tree
SET ref_page_guid = 'C75ECC15-B5ED-59A8-AC10-C17242F9F038'
WHERE key_guid IN (
    '54CDA54E-ED20-5249-87CE-43B19D96B39A',  -- HomePage root
    '31219EA9-A5D7-5D9D-A449-B1A743165A84',  -- ImageElement:banner
    '181FCFC1-E9CC-5AE7-98B0-AD46DB0BBB2B',  -- LinkButton:products
    '62DEF194-3BF5-5368-877C-C5FC11C1B5DE',  -- LinkButton:gallery
    '24F9CDE8-3C22-56D3-BFBF-1BB43D30BA2A',  -- LinkButton:github
    'EB6297D3-3D54-5004-881D-6A8DDE569AAE',  -- LinkButton:linkedin
    '7C2CEC0E-9221-57C3-8217-FA5AB36AC814'   -- LabelElement:copyright
);


-- =============================================================
-- Now continue with 6k (data bindings), 6l (security backfill),
-- 6m (route update), and Phase 7 (self-registration) from the
-- original seed script — those have no ordering issues.
-- =============================================================

-- Verify
SELECT
    t.pub_sequence AS seq,
    c.pub_name AS component,
    t.pub_label AS label,
    t.pub_field_binding AS binding,
    CASE WHEN t.ref_page_guid IS NOT NULL THEN 'yes' ELSE 'no' END AS has_page_ref
FROM system_objects_component_tree t
JOIN system_objects_components c ON c.key_guid = t.ref_component_guid
WHERE t.ref_page_guid = 'C75ECC15-B5ED-59A8-AC10-C17242F9F038'
ORDER BY t.pub_sequence;

SELECT p.pub_slug, p.pub_title, c.pub_name AS root_component
FROM system_objects_pages p
LEFT JOIN system_objects_component_tree t ON t.key_guid = p.ref_root_component_guid
LEFT JOIN system_objects_components c ON c.key_guid = t.ref_component_guid;









-- ============================================================================
-- Backfill: Column registrations for system_objects_modules and
-- system_objects_module_methods (tables registered in v0.12.5.0,
-- columns were never seeded)
-- ============================================================================

DECLARE @T_UUID  UNIQUEIDENTIFIER = N'4D2EB10B-363E-5AF4-826A-9294146244E4';
DECLARE @T_STR   UNIQUEIDENTIFIER = N'0093B404-1EEE-563D-9135-4B9E7EECA7A2';
DECLARE @T_BOOL  UNIQUEIDENTIFIER = N'12B2F03B-E315-50A5-B631-E6B1EB961A17';
DECLARE @T_DTZ   UNIQUEIDENTIFIER = N'70F890D3-5AB5-5250-860E-4F7F9624190C';

DECLARE @TBL_MOD UNIQUEIDENTIFIER = N'D039D8FB-3F95-5A66-B7FB-AB4BA1301FEA'; -- system_objects_modules
DECLARE @TBL_MM  UNIQUEIDENTIFIER = N'65E5E8F3-7EFF-57F7-B4F9-087C191B7B5E'; -- system_objects_module_methods

-- system_objects_modules columns
INSERT INTO [dbo].[system_objects_database_columns]
  ([key_guid],[ref_table_guid],[ref_type_guid],[pub_name],[pub_ordinal],
   [pub_is_nullable],[pub_is_primary_key],[pub_is_identity],[pub_default],[pub_max_length])
VALUES
(N'A1B2C3D4-0001-5000-8000-000000000001',@TBL_MOD,@T_UUID,N'key_guid',         1,0,1,0,NULL,               NULL),
(N'A1B2C3D4-0002-5000-8000-000000000001',@TBL_MOD,@T_STR, N'pub_name',         2,0,0,0,NULL,               128),
(N'A1B2C3D4-0003-5000-8000-000000000001',@TBL_MOD,@T_STR, N'pub_state_attr',   3,0,0,0,NULL,               128),
(N'A1B2C3D4-0004-5000-8000-000000000001',@TBL_MOD,@T_STR, N'pub_module_path',  4,0,0,0,NULL,               256),
(N'A1B2C3D4-0005-5000-8000-000000000001',@TBL_MOD,@T_STR, N'pub_description',  5,1,0,0,NULL,               512),
(N'A1B2C3D4-0006-5000-8000-000000000001',@TBL_MOD,@T_BOOL,N'pub_is_active',    6,0,0,0,N'1',              NULL),
(N'A1B2C3D4-0007-5000-8000-000000000001',@TBL_MOD,@T_DTZ, N'priv_created_on',  7,0,0,0,N'SYSUTCDATETIME()',NULL),
(N'A1B2C3D4-0008-5000-8000-000000000001',@TBL_MOD,@T_DTZ, N'priv_modified_on', 8,0,0,0,N'SYSUTCDATETIME()',NULL);

-- system_objects_module_methods columns
INSERT INTO [dbo].[system_objects_database_columns]
  ([key_guid],[ref_table_guid],[ref_type_guid],[pub_name],[pub_ordinal],
   [pub_is_nullable],[pub_is_primary_key],[pub_is_identity],[pub_default],[pub_max_length])
VALUES
(N'A1B2C3D4-0001-5000-8000-000000000002',@TBL_MM,@T_UUID,N'key_guid',                1,0,1,0,NULL,               NULL),
(N'A1B2C3D4-0002-5000-8000-000000000002',@TBL_MM,@T_UUID,N'ref_module_guid',         2,0,0,0,NULL,               NULL),
(N'A1B2C3D4-0003-5000-8000-000000000002',@TBL_MM,@T_STR, N'pub_name',                3,0,0,0,NULL,               128),
(N'A1B2C3D4-0004-5000-8000-000000000002',@TBL_MM,@T_STR, N'pub_description',         4,1,0,0,NULL,               512),
(N'A1B2C3D4-0005-5000-8000-000000000002',@TBL_MM,@T_UUID,N'ref_request_model_guid',  5,1,0,0,NULL,               NULL),
(N'A1B2C3D4-0006-5000-8000-000000000002',@TBL_MM,@T_UUID,N'ref_response_model_guid', 6,1,0,0,NULL,               NULL),
(N'A1B2C3D4-0007-5000-8000-000000000002',@TBL_MM,@T_BOOL,N'pub_is_active',           7,0,0,0,N'1',              NULL),
(N'A1B2C3D4-0008-5000-8000-000000000002',@TBL_MM,@T_DTZ, N'priv_created_on',         8,0,0,0,N'SYSUTCDATETIME()',NULL),
(N'A1B2C3D4-0009-5000-8000-000000000002',@TBL_MM,@T_DTZ, N'priv_modified_on',        9,0,0,0,N'SYSUTCDATETIME()',NULL);
GO