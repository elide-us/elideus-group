import { createContext } from 'react';

export interface UserData {
  bearerToken: string;
}
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