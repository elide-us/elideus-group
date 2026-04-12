import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';
import type { ReactNode } from 'react';

import { getToken, getUserContext, invalidateToken, logoutDevice } from '../api/rpc';
import type { GetTokenPayload, UserContext } from '../api/rpc';
import { getFingerprint } from './fingerprint';

export interface UserContextValue {
	user: UserContext | null;
	sessionToken: string | null;
	isLoading: boolean;
	login: (provider: string, tokens: Record<string, unknown>) => Promise<void>;
	logout: () => Promise<void>;
}

const UserContextState = createContext<UserContextValue | undefined>(undefined);

function readStoredSessionToken(): string | null {
	try {
		const raw = localStorage.getItem('authTokens');
		if (!raw) {
			return null;
		}
		const parsed = JSON.parse(raw) as { sessionToken?: unknown };
		return typeof parsed.sessionToken === 'string' ? parsed.sessionToken : null;
	} catch {
		return null;
	}
}

function clearStoredSession(): void {
	localStorage.removeItem('authTokens');
}

function writeStoredSessionToken(sessionToken: string): void {
	localStorage.setItem('authTokens', JSON.stringify({ sessionToken }));
}

export function UserContextProvider({ children }: { children: ReactNode }): JSX.Element {
	const [user, setUser] = useState<UserContext | null>(null);
	const [sessionToken, setSessionToken] = useState<string | null>(() => readStoredSessionToken());
	const [isLoading, setIsLoading] = useState<boolean>(true);

	const clearState = useCallback(() => {
		clearStoredSession();
		setSessionToken(null);
		setUser(null);
	}, []);

	useEffect(() => {
		let mounted = true;
		const hydrateUser = async (): Promise<void> => {
			const existingToken = readStoredSessionToken();
			if (!existingToken) {
				if (mounted) {
					setIsLoading(false);
				}
				return;
			}

			try {
				const currentUser = await getUserContext();
				if (mounted) {
					setSessionToken(existingToken);
					setUser(currentUser);
				}
			} catch {
				if (mounted) {
					clearState();
				}
			} finally {
				if (mounted) {
					setIsLoading(false);
				}
			}
		};

		void hydrateUser();

		return () => {
			mounted = false;
		};
	}, [clearState]);

	const login = useCallback(async (provider: string, tokens: Record<string, unknown>): Promise<void> => {
		const payload: GetTokenPayload = {
			provider,
			fingerprint: getFingerprint(),
			...(tokens as Partial<GetTokenPayload>),
		};

		const loginResult = await getToken(payload);
		writeStoredSessionToken(loginResult.sessionToken);
		setSessionToken(loginResult.sessionToken);
		const currentUser = await getUserContext();
		setUser(currentUser);
	}, []);

	const logout = useCallback(async (): Promise<void> => {
		try {
			await logoutDevice();
		} finally {
			try {
				await invalidateToken();
			} finally {
				clearState();
			}
		}
	}, [clearState]);

	useEffect(() => {
		const onSessionExpired = (): void => {
			clearState();
		};
		window.addEventListener('sessionExpired', onSessionExpired);
		return () => {
			window.removeEventListener('sessionExpired', onSessionExpired);
		};
	}, [clearState]);

	const contextValue = useMemo<UserContextValue>(
		() => ({
			user,
			sessionToken,
			isLoading,
			login,
			logout,
		}),
		[user, sessionToken, isLoading, login, logout],
	);

	return <UserContextState.Provider value={contextValue}>{children}</UserContextState.Provider>;
}

export function useUserContext(): UserContextValue {
	const context = useContext(UserContextState);
	if (!context) {
		throw new Error('useUserContext must be used within a UserContextProvider.');
	}
	return context;
}
