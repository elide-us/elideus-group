import { useState, ReactNode, useEffect } from 'react';
import UserContext from './UserContext';
import type { FrontendUserProfileData1 } from './RpcModels';
import { fetchProfileData } from '../rpc/frontend/user';

interface UserContextProviderProps {
  	children: ReactNode;
}

const UserContextProvider = ({ children }: UserContextProviderProps): JSX.Element => {
        const [userData, setUserData] = useState<FrontendUserProfileData1 | null>(null);

        useEffect(() => {
                const raw = localStorage.getItem('authTokens');
                if (!raw) return;
                try {
                        interface StoredSession { bearerToken: string; }
                        const stored: StoredSession = JSON.parse(raw);
                        if (!stored.bearerToken) return;

                        const base: FrontendUserProfileData1 = {
                                bearerToken: stored.bearerToken,
                                defaultProvider: 'microsoft',
                                username: '',
                                email: '',
                                backupEmail: null,
                               profilePicture: null,
                               credits: 0,
                               storageUsed: 0,
                                storageEnabled: false,
                               displayEmail: false,
                                roles: [],
                        };
                        setUserData(prev => prev ? { ...prev, ...base } : base);

                        void (async () => {
                                try {
                                        const profile = await fetchProfileData({ bearerToken: stored.bearerToken });
                                const profilePictureBase64 = profile.profilePicture ? `data:image/png;base64,${profile.profilePicture}` : null;
                                setUserData({ ...profile, profilePicture: profilePictureBase64 });
                                } catch (err) {
                                        console.error('Failed to refresh user profile', err);
                                }
                        })();
                } catch {
                        console.error('Failed to parse stored auth tokens');
                }
        }, []);

        const clearUserData = () => {
                localStorage.removeItem('authTokens');
                setUserData(null);
        };

  	return (
    	<UserContext.Provider value={{ userData, setUserData, clearUserData }}>
      		{children}
    	</UserContext.Provider>
  	);
};

export default UserContextProvider;
