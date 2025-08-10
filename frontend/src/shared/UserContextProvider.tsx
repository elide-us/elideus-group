import { useState, ReactNode } from 'react';
import UserContext from './UserContext';
import type { AuthTokens } from './RpcModels';

interface UserContextProviderProps {
  	children: ReactNode;
}

const UserContextProvider = ({ children }: UserContextProviderProps): JSX.Element => {
        const [userData, setUserDataState] = useState<AuthTokens | null>(() => {
                if (typeof localStorage !== 'undefined') {
                        try {
                                const raw = localStorage.getItem('authTokens');
                                if (raw) {
                                        return JSON.parse(raw) as AuthTokens;
                                }
                        } catch {
                                /* ignore */
                        }
                }
                return null;
        });

        const setUserData = (data: AuthTokens) => {
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

        return (
        <UserContext.Provider value={{ userData, setUserData, clearUserData }}>
                {children}
        </UserContext.Provider>
        );
};

export default UserContextProvider;
