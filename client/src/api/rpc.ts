import axios, { AxiosError } from 'axios';

import type { PathNode } from '../engine/types';
import { getFingerprint } from '../shared/fingerprint';

interface RpcEnvelope<TPayload> {
	op: string;
	payload: TPayload;
	version: number;
	timestamp?: string;
}

interface AuthTokens {
	sessionToken: string;
}

interface RefreshTokenResult {
	sessionToken: string;
}

interface LoadPathResult {
	pathData: PathNode;
	componentData: Record<string, unknown>;
}

export interface NavigationRouteElement {
	path: string;
	title: string;
	icon: string | null;
	sequence: number;
	parentRouteGuid: string | null;
}

export interface ReadNavigationResult {
	elements: NavigationRouteElement[];
}

export interface ObjectTreeCategory {
	guid: string;
	name: string;
	display: string;
	icon: string | null;
	sequence: number;
	treeDepth: number;
	builderComponent: string | null;
}

export interface ObjectTreeTable {
	guid: string;
	name: string;
	schema: string;
	isRoot: boolean;
	sequence: number;
}

export interface ObjectTreeColumn {
	guid: string;
	name: string;
	ordinal: number;
	isPrimaryKey: boolean;
	isNullable: boolean;
	typeName: string | null;
	maxLength: number | null;
}

export interface ObjectTreeDetail {
	tableName: string;
	schema: string;
	rowCount: number;
	rows: Record<string, unknown>[];
}

export interface GetTokenPayload {
	provider: string;
	idToken?: string | null;
	id_token?: string | null;
	accessToken?: string | null;
	access_token?: string | null;
	code?: string;
	fingerprint: string;
	confirm?: boolean | null;
	reAuthToken?: string | null;
}

export interface GetTokenResult {
	sessionToken: string;
	display_name: string;
	credits: number;
	profile_image: string | null;
}

export interface UserContext {
	display: string;
	email: string;
	roles: string[];
	entitlements: string[];
	providers: string[];
	sessionType: string;
	isAuthenticated: boolean;
}

function getStoredSessionToken(): string | null {
	try {
		const raw = localStorage.getItem('authTokens');
		if (!raw) {
			return null;
		}
		const parsed = JSON.parse(raw) as Partial<AuthTokens>;
		return typeof parsed.sessionToken === 'string' ? parsed.sessionToken : null;
	} catch {
		return null;
	}
}

function setStoredSessionToken(sessionToken: string): void {
	localStorage.setItem('authTokens', JSON.stringify({ sessionToken }));
}

function clearStoredSessionToken(): void {
	localStorage.removeItem('authTokens');
}

async function tryRefreshToken(): Promise<string | null> {
	try {
		const refreshResponse = await axios.post<RpcEnvelope<RefreshTokenResult>>(
			'/rpc',
			{
				op: 'urn:auth:session:refresh_token:1',
				payload: { fingerprint: getFingerprint() },
				version: 1,
				timestamp: new Date().toISOString(),
			},
			{ headers: {} },
		);
		const refreshedToken = refreshResponse.data.payload.sessionToken;
		if (!refreshedToken) {
			throw new Error('No refreshed session token returned by server.');
		}
		setStoredSessionToken(refreshedToken);
		return refreshedToken;
	} catch {
		clearStoredSessionToken();
		window.dispatchEvent(new Event('sessionExpired'));
		return null;
	}
}

export async function rpcCall<T>(op: string, payload: unknown = {}): Promise<T> {
	const sessionToken = getStoredSessionToken();
	const headers: Record<string, string> = {};
	if (sessionToken) {
		headers.Authorization = `Bearer ${sessionToken}`;
	}

	try {
		const response = await axios.post<RpcEnvelope<T>>(
			'/rpc',
			{
				op,
				payload,
				version: 1,
				timestamp: new Date().toISOString(),
			},
			{ headers },
		);
		return response.data.payload;
	} catch (error) {
		const isUnauthorized =
			error instanceof AxiosError && error.response?.status === 401 && op !== 'urn:auth:session:refresh_token:1';
		if (!isUnauthorized) {
			throw error;
		}

		const refreshedToken = await tryRefreshToken();
		if (!refreshedToken) {
			throw error;
		}

		const retryResponse = await axios.post<RpcEnvelope<T>>(
			'/rpc',
			{
				op,
				payload,
				version: 1,
				timestamp: new Date().toISOString(),
			},
			{ headers: { Authorization: `Bearer ${refreshedToken}` } },
		);
		return retryResponse.data.payload;
	}
}

export async function loadPath(path: string): Promise<LoadPathResult> {
	return rpcCall<LoadPathResult>('urn:public:route:load_path:1', { path });
}

export async function readNavigation(): Promise<ReadNavigationResult> {
	return rpcCall<ReadNavigationResult>('urn:public:route:read_navigation:1');
}

export async function readObjectTreeCategories(): Promise<ObjectTreeCategory[]> {
	return rpcCall<ObjectTreeCategory[]>('urn:public:route:read_object_tree_categories:1');
}

export async function readObjectTreeChildren(
	categoryGuid: string,
	tableGuid?: string,
): Promise<ObjectTreeTable[] | ObjectTreeColumn[]> {
	return rpcCall<ObjectTreeTable[] | ObjectTreeColumn[]>(
		'urn:service:objects:read_object_tree_children:1',
		{ categoryGuid, tableGuid },
	);
}

export async function readObjectTreeDetail(
	tableGuid: string,
	maxRows?: number,
): Promise<ObjectTreeDetail> {
	return rpcCall<ObjectTreeDetail>('urn:service:objects:read_object_tree_detail:1', { tableGuid, maxRows });
}

export async function upsertDatabaseTable(payload: {
	keyGuid?: string;
	name: string;
	schema: string;
}): Promise<{ ok: boolean }> {
	return rpcCall<{ ok: boolean }>('urn:service:objects:upsert_database_table:1', payload);
}

export async function deleteDatabaseTable(keyGuid: string): Promise<{ ok: boolean }> {
	return rpcCall<{ ok: boolean }>('urn:service:objects:delete_database_table:1', { keyGuid });
}

export async function upsertDatabaseColumn(payload: {
	keyGuid?: string;
	tableGuid: string;
	typeGuid: string;
	name: string;
	ordinal: number;
	isNullable: boolean;
	isPrimaryKey: boolean;
	isIdentity: boolean;
	defaultValue?: string | null;
	maxLength?: number | null;
}): Promise<{ ok: boolean }> {
	return rpcCall<{ ok: boolean }>('urn:service:objects:upsert_database_column:1', payload);
}

export async function deleteDatabaseColumn(keyGuid: string): Promise<{ ok: boolean }> {
	return rpcCall<{ ok: boolean }>('urn:service:objects:delete_database_column:1', { keyGuid });
}

export async function upsertType(payload: {
	keyGuid?: string | null;
	name: string;
	mssqlType: string;
	postgresqlType?: string | null;
	mysqlType?: string | null;
	pythonType: string;
	typescriptType: string;
	jsonType: string;
	odbcTypeCode?: number | null;
	maxLength?: number | null;
	notes?: string | null;
}): Promise<{ ok: boolean }> {
	return rpcCall<{ ok: boolean }>('urn:service:objects:upsert_type:1', payload);
}

export async function deleteType(keyGuid: string): Promise<{ ok: boolean }> {
	return rpcCall<{ ok: boolean }>('urn:service:objects:delete_type:1', { keyGuid });
}

export async function getTypeControls(
	typeGuid: string,
): Promise<{ guid: string; componentName: string; isDefault: boolean }[]> {
	return rpcCall<{ guid: string; componentName: string; isDefault: boolean }[]>(
		'urn:service:objects:get_type_controls:1',
		{ typeGuid },
	);
}

export interface ModuleMethod {
	guid: string;
	name: string;
	description: string | null;
	isActive: boolean;
	requestModelGuid: string | null;
	responseModelGuid: string | null;
	requestModelName: string | null;
	responseModelName: string | null;
}

export interface MethodContract {
	contractGuid: string;
	contractName: string;
	version: number;
	isAsync: boolean;
	isInternalOnly: boolean;
	isActive: boolean;
	requestModelGuid: string | null;
	responseModelGuid: string | null;
	requestModelName: string | null;
	responseModelName: string | null;
}

export async function getModuleMethods(moduleGuid: string): Promise<ModuleMethod[]> {
	return rpcCall<ModuleMethod[]>('urn:service:objects:get_module_methods:1', { moduleGuid });
}

export async function upsertModule(payload: {
	keyGuid: string;
	description: string | null;
	isActive: boolean;
}): Promise<{ ok: boolean }> {
	return rpcCall<{ ok: boolean }>('urn:service:objects:upsert_module:1', payload);
}

export async function upsertModuleMethod(payload: {
	keyGuid?: string | null;
	moduleGuid: string;
	name: string;
	description: string | null;
	isActive: boolean;
}): Promise<{ ok: boolean }> {
	return rpcCall<{ ok: boolean }>('urn:service:objects:upsert_module_method:1', payload);
}

export async function deleteModuleMethod(keyGuid: string): Promise<{ ok: boolean }> {
	return rpcCall<{ ok: boolean }>('urn:service:objects:delete_module_method:1', { keyGuid });
}

export async function getMethodContract(methodGuid: string): Promise<MethodContract[]> {
	return rpcCall<MethodContract[]>('urn:service:objects:get_method_contract:1', { methodGuid });
}

export async function getToken(payload: GetTokenPayload): Promise<GetTokenResult> {
	return rpcCall<GetTokenResult>('urn:auth:session:get_token:1', payload);
}

export async function getUserContext(): Promise<UserContext> {
	return rpcCall<UserContext>('urn:public:auth:context:get_user_context:1');
}

export async function invalidateToken(): Promise<{ ok: boolean }> {
	return rpcCall<{ ok: boolean }>('urn:auth:session:invalidate_token:1');
}

export async function logoutDevice(): Promise<{ ok: boolean }> {
	return rpcCall<{ ok: boolean }>('urn:auth:session:logout_device:1');
}


export interface PageTreeNode {
	guid: string;
	parent_guid: string | null;
	component_name: string;
	component_category: string;
	component_guid: string;
	label: string | null;
	field_binding: string | null;
	sequence: number;
	rpc_operation: string | null;
	rpc_contract: string | null;
	mutation_operation: string | null;
	is_editable: boolean;
	depth: number;
}

export interface ComponentEntry {
	guid: string;
	name: string;
	category: string;
	description: string | null;
}

export interface ComponentDetail {
	guid: string;
	name: string;
	category: string;
	description: string | null;
	defaultTypeGuid: string | null;
	defaultTypeName: string | null;
	createdOn: string;
	modifiedOn: string;
}

export async function getPageTree(pageGuid: string): Promise<PageTreeNode[]> {
	return rpcCall<PageTreeNode[]>('urn:service:objects:get_page_tree:1', { pageGuid });
}

export async function listComponents(): Promise<ComponentEntry[]> {
	return rpcCall<ComponentEntry[]>('urn:service:objects:list_components:1');
}

export async function getComponentDetail(componentGuid: string): Promise<ComponentDetail> {
	return rpcCall<ComponentDetail>('urn:service:objects:get_component_detail:1', { componentGuid });
}

export async function upsertComponent(payload: {
	keyGuid: string;
	description?: string | null;
	defaultTypeGuid?: string | null;
}): Promise<{ ok: boolean }> {
	return rpcCall<{ ok: boolean }>('urn:service:objects:upsert_component:1', payload);
}

export async function createTreeNode(payload: {
	pageGuid: string;
	parentGuid: string | null;
	componentGuid: string;
	label?: string | null;
	fieldBinding?: string | null;
	sequence?: number;
}): Promise<{ ok: boolean; keyGuid: string }> {
	return rpcCall<{ ok: boolean; keyGuid: string }>('urn:service:objects:create_tree_node:1', payload);
}

export async function updateTreeNode(payload: {
	keyGuid: string;
	label?: string | null;
	fieldBinding?: string | null;
	sequence?: number | null;
	rpcOperation?: string | null;
	rpcContract?: string | null;
	componentGuid?: string | null;
}): Promise<{ ok: boolean }> {
	return rpcCall<{ ok: boolean }>('urn:service:objects:update_tree_node:1', payload);
}

export async function deleteTreeNode(keyGuid: string): Promise<{ ok: boolean }> {
	return rpcCall<{ ok: boolean }>('urn:service:objects:delete_tree_node:1', { keyGuid });
}

export async function moveTreeNode(payload: {
	keyGuid: string;
	newParentGuid: string | null;
	newSequence: number;
}): Promise<{ ok: boolean }> {
	return rpcCall<{ ok: boolean }>('urn:service:objects:move_tree_node:1', payload);
}
