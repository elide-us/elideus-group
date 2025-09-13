import { createContext } from 'react';
import type {
        AuthMicrosoftOauthLogin1,
        AuthGoogleOauthLogin1,
        AuthDiscordOauthLogin1,
} from './RpcModels';

export type AuthTokens = (
        | AuthMicrosoftOauthLogin1
        | AuthGoogleOauthLogin1
        | AuthDiscordOauthLogin1
) & {
        provider: string;
};

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
