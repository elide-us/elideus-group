import { useState, ReactNode } from 'react';
import UserContext from './UserContext';
import type { FrontendUserProfileData1 } from './RpcModels';

interface UserContextProviderProps {
  	children: ReactNode;
}

const UserContextProvider = ({ children }: UserContextProviderProps): JSX.Element => {
        const [userData, setUserData] = useState<FrontendUserProfileData1 | null>(null);

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
