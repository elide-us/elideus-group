import { createContext } from 'react';
import type { AuthMicrosoftLoginData1 } from './RpcModels';

export interface UserContext {
	userData: AuthMicrosoftLoginData1 | null;
	setUserData: (data: AuthMicrosoftLoginData1 | null) => void;
	clearUserData: () => void;
}
const defaultContext: UserContext = {
	userData: null,
	setUserData: () => {},
	clearUserData: () => {},
};

const UserContextObject = createContext<UserContext>(defaultContext);

export default UserContextObject;
