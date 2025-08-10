import { createContext } from 'react';
import type { AuthTokens } from './RpcModels';

export interface UserContext {
        userData: AuthTokens | null;
        setUserData: (data: AuthTokens) => void;
        clearUserData: () => void;
}

const defaultContext: UserContext = {
        userData: null,
        setUserData: () => {},
        clearUserData: () => {},
};

const UserContextObject = createContext<UserContext>(defaultContext);

export default UserContextObject;
