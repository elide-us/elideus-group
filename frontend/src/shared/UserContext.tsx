import { createContext } from 'react';
import type { AuthSessionAuthTokens } from './RpcModels';

export interface UserContext {
        userData: AuthSessionAuthTokens | null;
        setUserData: (data: AuthSessionAuthTokens) => void;
        clearUserData: () => void;
}

const defaultContext: UserContext = {
        userData: null,
        setUserData: () => {},
        clearUserData: () => {},
};

const UserContextObject = createContext<UserContext>(defaultContext);

export default UserContextObject;
