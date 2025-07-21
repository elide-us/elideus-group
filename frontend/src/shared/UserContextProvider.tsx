import { useState, ReactNode, useEffect } from 'react';
import UserContext from './UserContext';
import type { FrontendUserProfileData1, BrowserSessionData1 } from './RpcModels';

interface UserContextProviderProps {
  	children: ReactNode;
}

const UserContextProvider = ({ children }: UserContextProviderProps): JSX.Element => {
        const [userData, setUserData] = useState<FrontendUserProfileData1 | null>(null);

        useEffect(() => {
                const raw = localStorage.getItem('authTokens');
                if (raw) {
                        try {
                                const stored: BrowserSessionData1 = JSON.parse(raw);
                                if (stored.bearerToken) {
                                        const base: FrontendUserProfileData1 = {
                                                bearerToken: stored.bearerToken,
                                                defaultProvider: 'microsoft',
                                                username: '',
                                                email: '',
                                                backupEmail: null,
                                                profilePicture: null,
                                                credits: 0,
                                                storageUsed: 0,
                                                displayEmail: false,
                                                rotationToken: stored.rotationToken ?? null,
                                                rotationExpires: stored.rotationExpires ?? null,
                                        };
                                        setUserData(prev => prev ? { ...prev, ...base } : base);
                                }
                        } catch {
                                console.error('Failed to parse stored auth tokens');
                        }
                }
        }, []);

        const clearUserData = () => {
        setUserData(null);
        };

  	return (
    	<UserContext.Provider value={{ userData, setUserData, clearUserData }}>
      		{children}
    	</UserContext.Provider>
  	);
};

export default UserContextProvider;
