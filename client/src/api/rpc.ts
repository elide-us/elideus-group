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
