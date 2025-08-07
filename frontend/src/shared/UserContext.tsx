import { createContext } from 'react';

export interface UserContext {
        userData: null;
        setUserData: (data: null) => void;
	clearUserData: () => void;
}

const defaultContext: UserContext = {
        userData: null,
        setUserData: () => {},
        clearUserData: () => {},
};

const UserContextObject = createContext<UserContext>(defaultContext);

export default UserContextObject;
