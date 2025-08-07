import { useState, ReactNode, useEffect } from 'react';
import UserContext from './UserContext';

interface UserContextProviderProps {
  	children: ReactNode;
}

const UserContextProvider = ({ children }: UserContextProviderProps): JSX.Element => {
        const [userData, setUserData] = useState<null>(null);

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
