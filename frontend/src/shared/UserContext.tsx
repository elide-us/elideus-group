import { createContext } from 'react';
import type { UserData } from './RpcModels';

export interface UserContext {
  userData: UserData | null;
  setUserData: (data: UserData | null) => void;
  clearUserData: () => void;
}
const defaultContext: UserContext = {
  userData: null,
  setUserData: () => {},
  clearUserData: () => {},
};

const UserContextObject = createContext<UserContext>(defaultContext);

export default UserContextObject;