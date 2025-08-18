import { useState, ReactNode, useEffect } from 'react';
import { PublicClientApplication } from '@azure/msal-browser';
import UserContext from './UserContext';
import { msalConfig, loginRequest } from '../config/msal';
import { fetchOauthLogin } from '../rpc/auth/microsoft';
import type { AuthMicrosoftOauthLogin1 } from './RpcModels';

interface UserContextProviderProps {
	children: ReactNode;
}

const UserContextProvider = ({ children }: UserContextProviderProps): JSX.Element => {
		const [userData, setUserDataState] = useState<AuthMicrosoftOauthLogin1 | null>(() => {
				if (typeof localStorage !== 'undefined') {
						try {
								const raw = localStorage.getItem('authTokens');
								if (raw) {
										return JSON.parse(raw) as AuthMicrosoftOauthLogin1;
								}
						} catch {
								/* ignore */
						}
				}
				return null;
		});

		const setUserData = (data: AuthMicrosoftOauthLogin1) => {
				setUserDataState(data);
				if (typeof localStorage !== 'undefined') {
						localStorage.setItem('authTokens', JSON.stringify(data));
				}
		};

		const clearUserData = () => {
				setUserDataState(null);
				if (typeof localStorage !== 'undefined') {
						localStorage.removeItem('authTokens');
				}
		};

		useEffect(() => {
				const msal = new PublicClientApplication(msalConfig);
				const init = async () => {
						try {
								await msal.initialize();
								const account = msal.getActiveAccount() || msal.getAllAccounts()[0];
								if (!account) return;
								const result = await msal.acquireTokenSilent({
										...loginRequest,
										account
								});
								const data = await fetchOauthLogin({
										idToken: result.idToken,
										accessToken: result.accessToken,
										provider: 'microsoft'
								}) as AuthMicrosoftOauthLogin1;
								setUserData(data);
						} catch {
								/* silent token acquisition failed */
						}
				};
				void init();
		}, []);

		return (
		<UserContext.Provider value={{ userData, setUserData, clearUserData }}>
				{children}
		</UserContext.Provider>
		);
};

export default UserContextProvider;
