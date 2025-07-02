import { useState, ReactNode } from 'react';
import UserContext, { UserData } from './UserContext';

interface UserContextProviderProps {
  children: ReactNode;
}

const UserContextProvider = ({ children }: UserContextProviderProps): JSX.Element => {
  const [userData, setUserData] = useState<UserData | null>(null);

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
