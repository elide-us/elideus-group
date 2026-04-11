-- =============================================================
-- Update HomePage links to match frontend_links data
-- =============================================================

-- Step 1: Update existing tree node labels and field bindings
-- Products → Discord
UPDATE system_objects_component_tree
SET pub_label = 'Discord', pub_field_binding = 'link_discord', pub_sequence = 2
WHERE key_guid = '181FCFC1-E9CC-5AE7-98B0-AD46DB0BBB2B';

-- Gallery → GitHub
UPDATE system_objects_component_tree
SET pub_label = 'GitHub', pub_field_binding = 'link_github', pub_sequence = 3
WHERE key_guid = '62DEF194-3BF5-5368-877C-C5FC11C1B5DE';

-- GitHub → TikTok
UPDATE system_objects_component_tree
SET pub_label = 'TikTok', pub_field_binding = 'link_tiktok', pub_sequence = 4
WHERE key_guid = '24F9CDE8-3C22-56D3-BFBF-1BB43D30BA2A';

-- LinkedIn → BlueSky
UPDATE system_objects_component_tree
SET pub_label = 'BlueSky', pub_field_binding = 'link_bluesky', pub_sequence = 5
WHERE key_guid = 'EB6297D3-3D54-5004-881D-6A8DDE569AAE';

-- Step 2: Update existing data bindings
-- Discord
UPDATE system_objects_page_data_bindings
SET pub_alias = 'link_discord', pub_literal_value = 'https://discord.gg/xXUZFTuzSw'
WHERE ref_page_guid = 'C75ECC15-B5ED-59A8-AC10-C17242F9F038' AND ref_component_node_guid = '181FCFC1-E9CC-5AE7-98B0-AD46DB0BBB2B';

-- GitHub
UPDATE system_objects_page_data_bindings
SET pub_alias = 'link_github', pub_literal_value = 'https://github.com/elide-us'
WHERE ref_page_guid = 'C75ECC15-B5ED-59A8-AC10-C17242F9F038' AND ref_component_node_guid = '62DEF194-3BF5-5368-877C-C5FC11C1B5DE';

-- TikTok
UPDATE system_objects_page_data_bindings
SET pub_alias = 'link_tiktok', pub_literal_value = 'https://www.tiktok.com/@elide.us'
WHERE ref_page_guid = 'C75ECC15-B5ED-59A8-AC10-C17242F9F038' AND ref_component_node_guid = '24F9CDE8-3C22-56D3-BFBF-1BB43D30BA2A';

-- BlueSky
UPDATE system_objects_page_data_bindings
SET pub_alias = 'link_bluesky', pub_literal_value = 'https://bsky.app/profile/elideusgroup.com'
WHERE ref_page_guid = 'C75ECC15-B5ED-59A8-AC10-C17242F9F038' AND ref_component_node_guid = 'EB6297D3-3D54-5004-881D-6A8DDE569AAE';

-- Step 3: Add new LinkButton tree nodes
-- Suno
INSERT INTO system_objects_component_tree
  (key_guid, ref_parent_guid, ref_component_guid, ref_type_guid,
   pub_label, pub_field_binding, pub_sequence,
   pub_rpc_operation, pub_rpc_contract, pub_mutation_operation,
   pub_is_default_editable, ref_page_guid)
VALUES
  ('BDE3289A-D57D-5EB1-81C1-F0BE8FDA6748', '54CDA54E-ED20-5249-87CE-43B19D96B39A', '62B142DE-9DD8-567A-844E-6E1CF63FC958', NULL,
   'Suno', 'link_suno', 6, NULL, NULL, NULL, 0, 'C75ECC15-B5ED-59A8-AC10-C17242F9F038');

-- Patreon
INSERT INTO system_objects_component_tree
  (key_guid, ref_parent_guid, ref_component_guid, ref_type_guid,
   pub_label, pub_field_binding, pub_sequence,
   pub_rpc_operation, pub_rpc_contract, pub_mutation_operation,
   pub_is_default_editable, ref_page_guid)
VALUES
  ('A384D3D9-24DF-5208-A31F-D02C4BF0DA2B', '54CDA54E-ED20-5249-87CE-43B19D96B39A', '62B142DE-9DD8-567A-844E-6E1CF63FC958', NULL,
   'Patreon', 'link_patreon', 7, NULL, NULL, NULL, 0, 'C75ECC15-B5ED-59A8-AC10-C17242F9F038');

-- Step 4: Add new data bindings
-- Suno
INSERT INTO system_objects_page_data_bindings
  (key_guid, ref_page_guid, ref_component_node_guid, pub_source_type, pub_literal_value, pub_alias)
VALUES
  ('36F752DF-0295-5BB5-BDB4-CEC6BB017002', 'C75ECC15-B5ED-59A8-AC10-C17242F9F038', 'BDE3289A-D57D-5EB1-81C1-F0BE8FDA6748', 'literal', 'https://suno.com/@elideus', 'link_suno');

-- Patreon
INSERT INTO system_objects_page_data_bindings
  (key_guid, ref_page_guid, ref_component_node_guid, pub_source_type, pub_literal_value, pub_alias)
VALUES
  ('BC0EC471-25D9-5059-8938-818E55F9D0DE', 'C75ECC15-B5ED-59A8-AC10-C17242F9F038', 'A384D3D9-24DF-5208-A31F-D02C4BF0DA2B', 'literal', 'https://patreon.com/Elideus', 'link_patreon');

-- Step 5: Push copyright label after all links
UPDATE system_objects_component_tree SET pub_sequence = 10 WHERE key_guid = '7C2CEC0E-9221-57C3-8217-FA5AB36AC814';

-- Verify
SELECT t.pub_sequence, c.pub_name AS component, t.pub_label, t.pub_field_binding
FROM system_objects_component_tree t
JOIN system_objects_components c ON c.key_guid = t.ref_component_guid
WHERE t.ref_parent_guid = '54CDA54E-ED20-5249-87CE-43B19D96B39A'
ORDER BY t.pub_sequence;

