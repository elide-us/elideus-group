export interface RPCRequest {
  op: string;
  payload: any;
  version: number;
  timestamp: any;
  metadata: any;
}

export interface RPCResponse {
  op: string;
  payload: any;
  version: number;
  timestamp: any;
  metadata: any;
}

export interface UserData {
  bearerToken: string;
}

export interface AdminVarsHostname1 {
  hostname: string;
}

export interface AdminVarsRepo1 {
  repo: string;
  build: string;
}

export interface AdminVarsVersion1 {
  version: string;
}
