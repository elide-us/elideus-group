import { createContext } from 'react';
import type { AuthMicrosoftOauthLogin1 } from './RpcModels';

export interface UserContext {
        userData: AuthMicrosoftOauthLogin1 | null;
        setUserData: (data: AuthMicrosoftOauthLogin1) => void;
        clearUserData: () => void;
}

const defaultContext: UserContext = {
        userData: null,
        setUserData: () => {},
        clearUserData: () => {},
};

const UserContextObject = createContext<UserContext>(defaultContext);

export default UserContextObject;
