import { createContext } from 'react';

export interface UserData {
	bearerToken: string;
}

export interface UserContextType {
	userData: UserData | null;
	setUserData: (data: UserData | null) => void;
	clearUserData: () => void;
}

const defaultContext: UserContextType = {
	userData: null,
	setUserData: () => {},
	clearUserData: () => {},
};

const UserContext = createContext<UserContextType>(defaultContext);

export default UserContext;
