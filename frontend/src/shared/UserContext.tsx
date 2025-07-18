import { createContext } from 'react';
import type { FrontendUserProfileData1 } from './RpcModels';

export interface UserContext {
        userData: FrontendUserProfileData1 | null;
        setUserData: (data: FrontendUserProfileData1 | null) => void;
	clearUserData: () => void;
}
const defaultContext: UserContext = {
        userData: null,
        setUserData: () => {},
        clearUserData: () => {},
};

const UserContextObject = createContext<UserContext>(defaultContext);

export default UserContextObject;
